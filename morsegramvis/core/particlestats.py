from dataclasses import dataclass, asdict
import pandas as pd
import time
import vtk
import math
from core import cleandata, multiproc, surface_reconstruction_bk, utils
import os
import logging
import multiprocessing as mp


@dataclass
class Stats():
    '''
    abstract class for statistics
    '''
    cp_id: int
    centroid: list
    eig_vecs: list
    eig_vals: list
    neighbours: set


@dataclass
class Particle(Stats):
    """
    Class to hold particle data.
    """
    num_voxels: int
    eq_rad: float
    label: int = 0
    cn : int = 0     # Coordination number / number of neighbours
    # metrics from MassProperties filter
    volume: float = 0.0
    surface_area: float = 0.0
    min_cell_surface_area: float = 0.0
    max_cell_surface_area: float = 0.0
    normalized_shape_index: float = 0.0
    EI: float = 0.0    # elongation index
    FI: float = 0.0    # flatness index
    S: float = 0.0     # sphericity
    C: float = 0.0     # compactness


def compute_centroid(point_cloud):
    """
    Compute the centroid of a point cloud.
    @param point_cloud: VTK point cloud.
    """
    centroid = [0.0, 0.0, 0.0]
    numPoints = point_cloud.GetNumberOfPoints()
    if numPoints > 0:
        for i in range(numPoints):
            point = point_cloud.GetPoint(i)
            centroid[0] += point[0]
            centroid[1] += point[1]
            centroid[2] += point[2]
        centroid[0] /= numPoints
        centroid[1] /= numPoints
        centroid[2] /= numPoints
    else:
        logging.getLogger().error("compute_centroid: point_cloud.GetNumberOfPoints() == 0")
        return None
    return centroid


def get_eigen_vectors_values(point_cloud):
    '''
    returns eigen values, vector
    @param points: VTK point cloud.
    @return: eigen values, vector
    '''
    # vtk double array
    xArr = vtk.vtkDoubleArray()
    xArr.SetName("x")
    xArr.SetNumberOfComponents(1)

    yArr = vtk.vtkDoubleArray()
    yArr.SetName("y")
    yArr.SetNumberOfComponents(1)

    zArr = vtk.vtkDoubleArray()
    zArr.SetName("z")
    zArr.SetNumberOfComponents(1)

    for i in range(point_cloud.GetNumberOfPoints()):
        xArr.InsertNextValue(point_cloud.GetPoint(i)[0])
        yArr.InsertNextValue(point_cloud.GetPoint(i)[1])
        zArr.InsertNextValue(point_cloud.GetPoint(i)[2])

    # vtk table
    table = vtk.vtkTable()
    table.AddColumn(xArr)
    table.AddColumn(yArr)
    table.AddColumn(zArr)

    # vtk pca
    pca = vtk.vtkPCAStatistics()
    pca.SetInputData(table)
    pca.SetColumnStatus("x", 1)
    pca.SetColumnStatus("y", 1)
    pca.SetColumnStatus("z", 1)
    pca.RequestSelectedColumns()
    pca.SetDeriveOption(True)
    pca.Update()

    # eigenvalues
    eigenvalues = vtk.vtkDoubleArray()
    pca.GetEigenvalues(eigenvalues)
    ev = []
    # print("Eigenvalues: ")
    for i in range(eigenvalues.GetNumberOfTuples()):
        # print(eigenvalues.GetValue(i))
        ev.append(eigenvalues.GetValue(i))

    # eigenvectors
    eigenvectors = vtk.vtkDoubleArray()
    pca.GetEigenvectors(eigenvectors)

    eig_vec = [vtk.vtkDoubleArray() for i in range(eigenvectors.GetNumberOfTuples())]
    for i in range(eigenvectors.GetNumberOfTuples()):
        pca.GetEigenvector(i, eig_vec[i])

    eig_vec_2 = []
    for i in range(len(eig_vec)):
        eig_vec_2.append([eig_vec[i].GetValue(0), eig_vec[i].GetValue(1), eig_vec[i].GetValue(2)])

    return eig_vec_2, ev


def compute_eq_rad(vol):
    """
    Compute the equivalent radius of a particle.
    @param vol: volume of the particle.
    """
    return math.pow((3.0 * vol) / (4.0 * math.pi), 1.0 / 3.0)


def get_convex_hull(point_cloud):
    """
    Compute the convex hull of a point cloud using scipy.
    @param point_cloud: VTK point cloud.
    @return: VTK polydata.
    """
    
    poly_data = utils.delaunay3d_vtk(point_cloud, surface_reconstruction_bk.my_callback, False, None, 0)
    
    # extract surface
    surface = vtk.vtkDataSetSurfaceFilter()
    surface.SetInputData(poly_data)
    surface.Update()

    return surface.GetOutput()


def convex_hull_volume(point_cloud):
    """
    Compute the volume of the convex hull of a point cloud.
    @param point_cloud: VTK point cloud.
    """
    mp = vtk.vtkMassProperties()
    mp.SetInputData(utils.compute_normals(get_convex_hull(point_cloud)))
    mp.Update()

    return mp.GetVolume()


def compute_particle_stats_task(particle_id, pc_filename, point_cloud, contact_points, noisy, error_grains, particle_mesh_dir):
    """
    Compute particle stats task.
    @param particle_id: particle id.
    @param pc_filename: point cloud filename.
    @param point_cloud: point cloud.
    @param contact_points: contact points.
    @param noisy: noisy flag.
    @param error_grains: error grains.
    @param particle_mesh_dir: particle mesh directory.
    """

    if not noisy:
        if particle_id in error_grains.cp_ids:
            return None

    # print(grain_id)
    neighbours = set()
    try:
        for contact_pt in contact_points:
            if not noisy and contact_pt in error_grains.cp_ids:
                return None
            neighbours.add(contact_pt.sibling_cp_id)
    except KeyError:
        return None
    
    if point_cloud is None:
        # reading point cloud of particle from file
        point_cloud = utils.get_particle_pc_polydata(pc_filename)
    else:
        # converting point cloud to vtk polydata
        pd = vtk.vtkPolyData()
        pd.SetPoints(vtk.vtkPoints())
        for point in point_cloud:
            pd.GetPoints().InsertNextPoint(point)
        point_cloud = pd

    centroid = compute_centroid(point_cloud)
    eig_vecs, eig_vals = get_eigen_vectors_values(point_cloud)
    vol = point_cloud.GetNumberOfPoints()
    eq_rad = compute_eq_rad(vol)

    particle = Particle(    cp_id=particle_id, 
                            num_voxels=vol, 
                            centroid=centroid, 
                            eq_rad=eq_rad, 
                            eig_vecs=eig_vecs, 
                            eig_vals=eig_vals, 
                            neighbours=neighbours,
                            cn=len(neighbours))

    # MassProperties
    if particle.num_voxels > 0:
        pd = utils.read_file(particle_mesh_dir + str(int(particle_id)) + ".vtp")

        if pd.GetNumberOfPoints() > 0:
            mass_properties = vtk.vtkMassProperties()
            mass_properties.SetInputData(utils.compute_normals(pd))
            mass_properties.Update()

            particle.surface_area = mass_properties.GetSurfaceArea()
            particle.volume = mass_properties.GetVolume()
            particle.max_cell_surface_area = mass_properties.GetMaxCellArea()
            particle.min_cell_surface_area = mass_properties.GetMinCellArea()
            particle.normalized_shape_index = mass_properties.GetNormalizedShapeIndex()

            # computing sphericiy
            if particle.surface_area != 0:
                particle.S = math.pow((36 * math.pi * (particle.volume**2)), 1/3) / particle.surface_area

            # computing compactness
            conv_hull_vol = convex_hull_volume(point_cloud)
            if conv_hull_vol != 0:
                particle.C = particle.volume / conv_hull_vol

            # computing elongation index and flatness index
            if particle.eig_vals[0] != 0:
                particle.EI = particle.eig_vals[1] / particle.eig_vals[0]
            if particle.eig_vals[1] != 0:
                particle.FI = particle.eig_vals[2] / particle.eig_vals[1]

    logging.getLogger().info("(Particle Stats) Finished processing particle: " + str(particle_id))

    return particle


def compute_particle_stats(contact_points, pipe, seg_file, point_cloud_dir, stats_file, data_dir, particle_mesh_dir, noisy = False):
    """
    Compute particle stats.
    @param point_clouds: point clouds.
    @param contact_points: contact points.
    @param pipe: pipe to send data to the main process
    @param seg_file: segmentation file.
    @param point_cloud_dir: point cloud directory.
    @param stats_file: stats file.
    @param data_dir: data directory.
    @param noisy: noisy flag.
    """
    particle_stats_df = pd.DataFrame(columns=[x for x in Particle.__dataclass_fields__.keys()])

    grain_ids = []
    data_from_segmentation = False
    try:
        for file in os.listdir(point_cloud_dir):
            # file - grain_123.vtp
            grain_ids.append(int(file.split("_")[1].split(".")[0]))
    except FileNotFoundError:
        logging.getLogger().error("Point clouds folder not found.")
        # pipe.send(("Error computing particle statistics").encode("utf-8"))
        pcs = utils.get_grains_point_cloud(utils.read_file(seg_file))
        grain_ids = list(pcs.keys())
        data_from_segmentation = True

    error_grains = None
    if not noisy:
        error_grains = cleandata.CleanData()
        error_grains.load()

    num_cores = mp.cpu_count()

    worker_pool = multiproc.MultiProc(num_procs=num_cores-1)

    results = []

    for i in range(len(grain_ids)):
        particle_pc = None if not data_from_segmentation else pcs[grain_ids[i]]

        cont_pts = []
        try:
            cont_pts = contact_points[grain_ids[i]]
        except KeyError:
            # if there is no contact point for the particle, then
            logging.getLogger().warning("No contact points for particle: " + str(grain_ids[i]))

        results.append(worker_pool.add_task(compute_particle_stats_task, \
                grain_ids[i], point_cloud_dir + "grain_"+str(grain_ids[i])+".vtp", \
                particle_pc, cont_pts, noisy, error_grains, particle_mesh_dir))
        
        if data_from_segmentation:
            del pcs[grain_ids[i]]

    # finish the processes
    for i, result in enumerate(results):

        prog = (i / len(grain_ids)) * 100
        msg = 'ps{}'.format(int(prog))
        pipe.send(msg.encode('utf-8'))

        particle_stats_df.loc[i] = asdict(result.get())

    pipe.send('ps100'.encode('utf-8'))

    worker_pool.close()

    if noisy:
        particle_stats_df.to_csv(stats_file, index=True)
    else:
        particle_stats_df.to_csv(data_dir + "particle_stats_" + time.strftime("%Y%m%d-%H%M%S") + ".csv", index=True)


def particle_record(particlde_id, stats_file):
    """
    Record particle stats.
    @param cp_id: contact point id.
    """
    # check csv file exists
    if not os.path.isfile(stats_file):
        raise FileNotFoundError("Particle stats file not found.")
    
    # read csv file
    particle_stats_df = pd.read_csv(stats_file)
    return particle_stats_df.loc[particle_stats_df['cp_id'] == particlde_id]


