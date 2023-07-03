import vtk
import logging
import trimesh
from  core import fileutil, utils
from scipy.spatial import Delaunay
import multiprocessing as mp
import trimesh
from numba import jit
import pymeshlab
from enum import Enum
from core import multiproc


class SurfaceReconstructionMethod(Enum):
    '''
    Enum for surface reconstruction method
    '''
    VOXEL       = 0         # voxel model
    VTK         = 1         # vtk
    # MESH_LAB    = 2         # meshlab
    # SCIPY       = 3         # scipy

    # get the enum from string
    @staticmethod
    def from_string(s):
        '''
        Get the enum from string
        @param s: string
        @return: enum
        '''
        try:
            return SurfaceReconstructionMethod[s]
        except KeyError:
            raise ValueError()


class Voxel:
    '''
    Voxel with 8 vertices and 6 faces
    defined by the center of the voxel
    '''

    def __init__(self, center):
        '''
        Initialize the voxel
        @param center: center of the voxel
        '''
        self.center = center

    def get_vertices(self):
        vertices = []
        for xd in [-0.5, 0.5]:
            for yd in [-0.5, 0.5]:
                for zd in [-0.5, 0.5]:
                    vertices.append([self.center[0] + xd, self.center[1] + yd, self.center[2] + zd])
        return vertices

    def get_faces(self):
        faces = []
        faces.append([0, 1, 3, 2])
        faces.append([4, 5, 7, 6])
        faces.append([0, 1, 5, 4])
        faces.append([2, 3, 7, 6])
        faces.append([0, 2, 6, 4])
        faces.append([1, 3, 7, 5])

        return faces


def subdivide_polydata(polydata):
    '''
    each quad in the polydata is subdivided into 4 triangles
    @param polydata: input polydata
    @return: subdivided polydata
    '''
    # Create a new polydata to store the subdivided triangles
    subdivided_polydata = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    triangles = vtk.vtkCellArray()

    points_dict = {}
    num_points = 0

    # Iterate over each quad in the input polydata
    for i in range(polydata.GetNumberOfCells()):
        cell = polydata.GetCell(i)
        if cell.GetCellType() != vtk.VTK_QUAD:
            continue

        # Get the four corner points of the quad
        point1 = polydata.GetPoint(cell.GetPointId(0))
        point2 = polydata.GetPoint(cell.GetPointId(1))
        point3 = polydata.GetPoint(cell.GetPointId(2))
        point4 = polydata.GetPoint(cell.GetPointId(3))

        # Compute the center point of the quad
        center = [0.0, 0.0, 0.0]
        for point in [point1, point2, point3, point4]:
            for i in range(3):
                center[i] += point[i]
        
        for i in range(3):
            center[i] /= 4.0

        center = tuple(center)

        for point in [point1, point2, point3, point4, center]:
            point = tuple(point)
            # add each corner point of the quad to the new polydata
            if point not in points_dict:
                points_dict[point] = num_points
                num_points += 1
                points.InsertNextPoint(point)

        # Create three triangles connecting the center point with the quad's corner points
        triangle1 = vtk.vtkTriangle()
        triangle1.GetPointIds().SetId(0, points_dict[point1])
        triangle1.GetPointIds().SetId(1, points_dict[point2])
        triangle1.GetPointIds().SetId(2, points_dict[center])

        triangle2 = vtk.vtkTriangle()
        triangle2.GetPointIds().SetId(0, points_dict[point2])
        triangle2.GetPointIds().SetId(1, points_dict[point3])
        triangle2.GetPointIds().SetId(2, points_dict[center])

        triangle3 = vtk.vtkTriangle()
        triangle3.GetPointIds().SetId(0, points_dict[point3])
        triangle3.GetPointIds().SetId(1, points_dict[point4])
        triangle3.GetPointIds().SetId(2, points_dict[center])

        triangle4 = vtk.vtkTriangle()
        triangle4.GetPointIds().SetId(0, points_dict[point4])
        triangle4.GetPointIds().SetId(1, points_dict[point1])
        triangle4.GetPointIds().SetId(2, points_dict[center])

        # Add the triangles with the center point to the new polydata
        triangles.InsertNextCell(triangle1)
        triangles.InsertNextCell(triangle2)
        triangles.InsertNextCell(triangle3)
        triangles.InsertNextCell(triangle4)



    # Set the points and triangles in the new polydata
    subdivided_polydata.SetPoints(points)
    subdivided_polydata.SetPolys(triangles)

    return subdivided_polydata



def my_callback(obj, string):
    """
    Callback function for the progress bar.
    @param obj: the object
    @param string: the string
    """
    pass


def surface_reconstruction(task, cb):
    """
    Surface reconstruction of the input_data.
    @param task: object of the ChildTask class
    @param cb: the callback function for the progress bar or Connection Pipe
    """

    # filename = "grain_0.vtp"
    curr_cp = task.filename.split('/')[-1].replace("grain_", "").split('.')[0]

    if task.point_cloud is None:
        input_data = utils.get_particle_pc_polydata(task.filename)
    else:
        input_data = vtk.vtkPolyData()
        input_data.SetPoints(vtk.vtkPoints())
        input_data.GetPoints().SetNumberOfPoints(len(task.point_cloud))
        for j in range(len(task.point_cloud)):
            input_data.GetPoints().SetPoint(j, task.point_cloud[j])
    
    # if SurfaceReconstructionMethod.SCIPY.name == method:
    #     polydata = surface_reconstruct_scipy(input_data, cb)
    
    if SurfaceReconstructionMethod.VTK.name == task.sr_method:
        # surface reconstruction using vtk
        polydata = utils.delaunay3d_vtk(input_data, my_callback, task.display_progress, cb, task.opts['alpha'])

        # smooth the unsructured grid
        surface = vtk.vtkDataSetSurfaceFilter()
        surface.SetInputData(polydata)
        surface.Update()

        smooth = vtk.vtkSmoothPolyDataFilter()
        smooth.SetInputData(surface.GetOutput())
        smooth.SetNumberOfIterations(task.opts['iters'])
        smooth.Update()

        polydata = smooth.GetOutput()

    elif SurfaceReconstructionMethod.VOXEL.name == task.sr_method:
        polydata = surface_reconstruct_voxel(input_data, cb, curr_cp, task.surf_pc_dir, task.dem_dir, task.opts)

    fileutil.save_to_vtp(polydata, task.dest_dir + str(curr_cp).split(".")[0] + ".vtp", task.color)


@jit(nopython=True, fastmath=True)
def distance(p1, p2):
    '''
    Calculate the distance between two points
    @param p1: point 1
    @param p2: point 2
    @return: distance between p1 and p2
    '''
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)**0.5


def surface_reconstruct_scipy(input_data, C_pipe):
    '''
    surface reconstruction using scipy
    @param input_data: the input data point cloud.
    @param C_pipe: the pipe to send the progress to
    '''
    poly_data = vtk.vtkPolyData()
    points = [input_data.GetPoint(i) for i in range(input_data.GetNumberOfPoints())]

    try:
        tri = Delaunay(points)

        triangle_counts = {}
        for i, simplex in enumerate(tri.simplices):
            length_of_simplices = []
            length_of_simplices.append(distance(points[simplex[0]], points[simplex[1]]))
            length_of_simplices.append(distance(points[simplex[0]], points[simplex[2]]))
            length_of_simplices.append(distance(points[simplex[0]], points[simplex[3]]))
            length_of_simplices.append(distance(points[simplex[1]], points[simplex[2]]))
            length_of_simplices.append(distance(points[simplex[1]], points[simplex[3]]))
            length_of_simplices.append(distance(points[simplex[2]], points[simplex[3]]))

            # if length of longest edge is greater than 0.5, then it is a pesudo simplex
            check = False
            for j in range(6):
                if length_of_simplices[-1-j] > 5:
                    check = True
                    break
            if not check:
                for j in range(4):
                    triangle = tuple(sorted((simplex[j], simplex[(j+1)%4], simplex[(j+2)%4])))
                    triangle_counts[triangle] = triangle_counts.get(triangle, 0) + 1


        msg = '{},{}'.format(mp.current_process().pid, 25)
        C_pipe.send(msg.encode('utf-8'))

        # boundary faces : triangular face belong to boundary 
        # if it has only one tetrahedron associated with it
        boundary = set()
        for triangle in triangle_counts:
            if triangle_counts[triangle] == 1:
                boundary.add(triangle)

        filtered_points = set()
        for triangle in boundary:
            for point in triangle:
                filtered_points.add(point)

        msg = '{},{}'.format(mp.current_process().pid, 50)
        C_pipe.send(msg.encode('utf-8'))

        old_points_new_points_map = {}
        m_vertices = []
        for i, point in enumerate(filtered_points):
            old_points_new_points_map[point] = i
            m_vertices.append(points[point])

        msg = '{},{}'.format(mp.current_process().pid, 75)
        C_pipe.send(msg.encode('utf-8'))

        m_faces = []
        for triangle in boundary:
            triangle = [old_points_new_points_map[point] for point in triangle]
            m_faces.append(triangle)

        tri_mesh = trimesh.Trimesh(vertices=m_vertices, faces=m_faces)
        trimesh.smoothing.filter_humphrey(tri_mesh, beta=0.1)
        # trimesh.repair.fill_holes(tri_mesh)
        # check for holes
        if not tri_mesh.is_watertight:
            tri_mesh.fill_holes()
        if not tri_mesh.is_winding_consistent:
            tri_mesh.fix_normals()

        poly_data = utils.trimesh_to_polydata(tri_mesh)

    except Exception as e:
        logging.getLogger().error("Error in delaunay_scipy: {}".format(e))

    msg = '{},{}'.format(mp.current_process().pid, 100)
    C_pipe.send(msg.encode('utf-8'))

    return poly_data


def smooth_meshlab(filename, dem_dir, opts):
    '''
    Smooth the mesh using pymeshlab
    @param filename: the filename of the mesh
    @param dem_dir: the directory to save the mesh
    '''
    # create a meshset
    ms = pymeshlab.MeshSet()

    # load a mesh
    ms.load_new_mesh(filename)

    # taubin_smooth
    ms.apply_coord_taubin_smoothing(stepsmoothnum=opts['iters'],
                                    lambda_=opts['lambda'],
                                    mu=opts['mu'])

    # decimate
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=0, targetperc=0.1)

    # save the mesh
    ms.save_current_mesh(dem_dir + filename.split('/')[-1].split('.')[0] + ".stl")


def surface_reconstruct_meshlab(filename, dem_dir):
    '''
    surface reconstruction using meshlab
    @param filename: the filename of the mesh
    @param dem_dir: the directory to save the mesh
    '''
    # create a meshset
    ms = pymeshlab.MeshSet()

    curr_cp = filename.split('/')[-1]

    # load a mesh
    ms.load_new_mesh(filename)

    # print(len(ms))  # now ms contains 1 mesh
    # instead of len(ms) you can also use:
    # print(ms.number_meshes())

    # print(ms.current_mesh().vertex_number())

    ms.compute_normal_for_point_clouds()

    # generate_surface_reconstruction_screened_poisson
    ms.generate_surface_reconstruction_screened_poisson(depth=5)

    # taubin_smooth
    ms.apply_coord_taubin_smoothing(stepsmoothnum=100, lambda_=0.5, mu=-0.43)

    # decimate
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=0, targetperc=0.1)

    # save the mesh
    ms.save_current_mesh(dem_dir + str(curr_cp).split(".")[0] + ".stl")


def surface_reconstruct_voxel(input_data, C_pipe, curr_cp, surf_pc_dir, dem_dir, opts):
    '''
    surface reconstruction using voxel grid

    input_data: vtkPolyData
    C_pipe: multiprocessing.Pipe
    curr_cp: id of the particle
    surf_pc_dir: directory to save the surface point cloud
    dem_dir: directory to save the surface mesh
    opts: options like alpha, mu, iterations
    '''
    points = [input_data.GetPoint(i) for i in range(input_data.GetNumberOfPoints())]

    # for each point create a voxel
    vg_points = {}
    num_vg_points = 0
    vg_faces = {}
    for i, point in enumerate(points):

        voxel = Voxel(point)

        for pt in voxel.get_vertices():
            pt_tup = tuple(pt)
            if pt_tup not in vg_points:
                vg_points[pt_tup] = num_vg_points
                num_vg_points += 1

        for face in voxel.get_faces():
            vox_verts = voxel.get_vertices()
            pt1 = tuple(vox_verts[face[0]])
            pt2 = tuple(vox_verts[face[1]])
            pt3 = tuple(vox_verts[face[2]])
            pt4 = tuple(vox_verts[face[3]])

            face_tup = tuple(sorted([vg_points[pt1], vg_points[pt2], vg_points[pt3], vg_points[pt4]]))

            if face_tup not in vg_faces:
                vg_faces[face_tup] = [1, (vg_points[pt1], vg_points[pt2], vg_points[pt3], vg_points[pt4])]
            else:
                vg_faces[face_tup][0] = vg_faces[face_tup][0] + 1

        # update the progress bar
        curr_progress = int((i+1)/len(points)*100)
        msg = '{},{}'.format(mp.current_process().pid, curr_progress)
        C_pipe.send(msg.encode('utf-8'))


    new_points = []
    for pt in vg_points:
        new_points.append(pt)

    new_faces = []
    for k, v in vg_faces.items():
        if v[0] == 1:
            new_faces.append(v[1])

    voxel_grid_polydata = vtk.vtkPolyData()

    points = vtk.vtkPoints()
    for pt in new_points:
        points.InsertNextPoint(pt)

    faces = vtk.vtkCellArray()
    for face in new_faces:
        faces.InsertNextCell(4)
        faces.InsertCellPoint(face[0])
        faces.InsertCellPoint(face[1])
        faces.InsertCellPoint(face[2])
        faces.InsertCellPoint(face[3])

    voxel_grid_polydata.SetPoints(points)
    voxel_grid_polydata.SetPolys(faces)
    voxel_grid_polydata.Modified()

    # clean the voxel grid polydata
    clean = vtk.vtkCleanPolyData()
    clean.SetInputData(voxel_grid_polydata)
    clean.Update()

    # extract the surface of the voxel grid polydata
    extract_surface = vtk.vtkDataSetSurfaceFilter()
    extract_surface.SetInputData(subdivide_polydata(clean.GetOutput()))
    extract_surface.Update()

    mesh = utils.get_trimesh_from_polydata(extract_surface.GetOutput())
    mesh.export(surf_pc_dir + str(curr_cp).split(".")[0] + ".ply")

    # if SurfaceReconstructionMethod.MESH_LAB.name == impl:

    #     surface_points = trimesh.Trimesh(vertices=mesh.vertices)
    #     surface_points.export(surf_pc_dir + str(curr_cp).split(".")[0] + ".ply")

    #     curr_progress = 70
    #     msg = '{},{}'.format(mp.current_process().pid, curr_progress)
    #     C_pipe.send(msg.encode('utf-8'))

    #     # generate surface reconstruction using pymeshlab
    #     surface_reconstruct_meshlab(curr_cp)

    #     curr_progress = 100
    #     msg = '{},{}'.format(mp.current_process().pid, curr_progress)
    #     C_pipe.send(msg.encode('utf-8'))

    #     # reading file from dem folder
    #     poly_data = utils.read_file(dem_dir + str(curr_cp).split(".")[0] + ".stl")
    
    # if SurfaceReconstructionMethod.VOXEL.name == impl:
    smooth_meshlab(surf_pc_dir + str(curr_cp).split(".")[0] + ".ply", dem_dir, opts)
    poly_data = utils.read_file(dem_dir + str(curr_cp).split(".")[0] + ".stl")

    return poly_data


