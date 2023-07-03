from dataclasses import dataclass
import vtk
import sys
import os
import shutil
import trimesh
import point_cloud_utils as pcu


@dataclass
class ContactPoint:
    '''
    ContactPoint class
    '''
    cp_id: int
    position: tuple
    sibling_cp_id: int
    distance_val: float
    saddle_2_cp_id: int

colors = vtk.vtkNamedColors()

# enum for single , neighbor
class ViewType:
    SINGLE = 0
    NEIGHBOR = 1


def read_file(filename, progress_handler=None):
    """
    Read a vtp file and return a vtkPolyData object.
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError("File not found: " + filename)

    print("\033[1;32mReading file: " + filename + "\033[1;m")
    # extension
    extension = filename.split(".")[-1]
    if extension == "vtp":
        reader = vtk.vtkXMLPolyDataReader()
    elif extension == "vtu":
        reader = vtk.vtkXMLUnstructuredGridReader()
    elif extension == "mhd":
        reader = vtk.vtkMetaImageReader()
    elif extension == "stl":
        reader = vtk.vtkSTLReader()
    else:
        print("Unknown file extension: ", extension)
        sys.exit(1)
    
    reader.SetFileName(filename)
    if progress_handler is not None:
        reader.AddObserver("ProgressEvent", progress_handler)
    reader.Update()
    
    return reader.GetOutput()


def print_all_arrays_point_data(input_data):
    """
    Find all arrays in the point data of the input_data.
    print out the array names, types, and number of components.
    @param input_data: the input data (polydata)
    """
    print("==========================================================")
    pointData = input_data.GetPointData()
    print("Number of arrays in the point data: ", pointData.GetNumberOfArrays())
    # print the points size
    print("Number of points: ", input_data.GetNumberOfPoints())
    # set for storing distance values
    for i in range(pointData.GetNumberOfArrays()):
        print("----------------------------------------------------------")
        cell_array = pointData.GetArray(i)
        print("Array: ", i, "(Name): ", cell_array.GetName())
        print("Array: ", i, "(Data type): ", cell_array.GetDataType())
        print("Array: ", i, "(Number of components): ",
              cell_array.GetNumberOfComponents())
        print("Array: ", i, "(Number of cells): ",
              cell_array.GetNumberOfTuples())
        print("Array: ", i, "(Range): ", cell_array.GetRange())
        print("----------------------------------------------------------")
    print("==========================================================")


def print_all_arrays_cell_data(input_data):
    """
    Find all arrays in the cell data of the input_data.
    print out the array names, types, and number of components.
    """
    print("==========================================================")
    print("Number of arrays in the cell data: ",
          input_data.GetCellData().GetNumberOfArrays())
    cellData = input_data.GetCellData()
    for i in range(cellData.GetNumberOfArrays()):
        cell_array = cellData.GetArray(i)
        print("Array: ", i, "(Name): ", cell_array.GetName())
        print("Array: ", i, "(Data type): ", cell_array.GetDataType())
        print("Array: ", i, "(Number of components): ",
              cell_array.GetNumberOfComponents())
        print("Array: ", i, "(Data type): ", cell_array.GetDataType())
    print("==========================================================")


def get_grains_point_cloud(input_polydata):
    '''
    extract the point cloud of each grain from the input_polydata(PointData)
    @param input_polydata: the input data (polydata)
    @return: a dict of point cloud of each grain key is CP ID and value is the point cloud
    e.g: dict[CP ID] = [(x1, y1, z1), (x2, y2, z2), (x3, y3, z3),...]
    '''
    point_cloud_dict = {}
    point_array = input_polydata.GetPointData().GetArray("CP ID")
    for i in range(point_array.GetNumberOfTuples()):
        if point_array.GetTuple(i)[0] not in point_cloud_dict:
            point_cloud_dict[point_array.GetTuple(i)[0]] = []
        point_cloud_dict[point_array.GetTuple(i)[0]].append(input_polydata.GetPoint(i))
    return point_cloud_dict


def get_grains_boundary(input_polydata):
    '''
    extract the boundary of each grain from the input_polydata(PointData)
    @param input_polydata: the input data (polydata)
    @return: a dict of boundary of each grain key is CP ID and value is the boundary
    '''
    boundary_dict = {}
    point_array = input_polydata.GetPointData().GetArray("CP ID")
    dis_point_array = input_polydata.GetPointData().GetArray("Distance Val")
    for i in range(point_array.GetNumberOfTuples()):
        if point_array.GetTuple(i)[0] not in boundary_dict:
            boundary_dict[point_array.GetTuple(i)[0]] = []
        # if the distance is 0, then it is a boundary point
        if dis_point_array.GetTuple(i)[0] <= 0.5:
            boundary_dict[point_array.GetTuple(i)[0]].append(input_polydata.GetPoint(i))
    return boundary_dict


def get_grain_polydata(input_polydata, grain_id):
    '''
    extract the grain polydata from the input_polydata(PointData)
    @param input_polydata: the input data (polydata)
    @param grain_id: the grain id
    @return: the grain polydata
    '''
    grain_polydata = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    point_array = input_polydata.GetPointData().GetArray("CP ID")
    dis_point_array = input_polydata.GetPointData().GetArray("Distance Val")
    # new array to store the distance value
    new_dis_point_array = vtk.vtkFloatArray()
    new_dis_point_array.SetName("Dist")
    cell_array = vtk.vtkCellArray()
    npts = 0
    for i in range(point_array.GetNumberOfTuples()):
        if point_array.GetTuple(i)[0] == grain_id:
            points.InsertNextPoint(input_polydata.GetPoint(i))
            new_dis_point_array.InsertNextTuple(dis_point_array.GetTuple(i))
            cell_array.InsertNextCell(1)
            cell_array.InsertCellPoint(npts)
            npts += 1
    grain_polydata.SetPoints(points)
    grain_polydata.SetVerts(cell_array)
    grain_polydata.GetPointData().AddArray(new_dis_point_array)
    return grain_polydata


def get_contact_network(input_polydata):
    '''
    extract the contact network from the input_polydata(PointData)
    @param input_polydata: the input data (polydata)
    @return: a dict of contact network of each grain key is CP ID and value is the
    list of tuples (contact point location,  other grain, distance value, CP ID of 2-saddle)
    '''
    contact_network_dict = {}
    contact_array_max_1 = input_polydata.GetPointData().GetArray("Max 1")
    contact_array_max_2 = input_polydata.GetPointData().GetArray("Max 2")
    contact_array_val   = input_polydata.GetPointData().GetArray("Val")
    saddle_2s           = input_polydata.GetPointData().GetArray("CP ID")
    for i in range(contact_array_max_1.GetNumberOfTuples()):
        if contact_array_max_1.GetTuple(i)[0] not in contact_network_dict:
            contact_network_dict[contact_array_max_1.GetTuple(i)[0]] = []
        if contact_array_max_2.GetTuple(i)[0] not in contact_network_dict:
            contact_network_dict[contact_array_max_2.GetTuple(i)[0]] = []
        
        contact_point_1 = ContactPoint(int(contact_array_max_1.GetTuple(i)[0]),
                                        input_polydata.GetPoint(i),
                                        int(contact_array_max_2.GetTuple(i)[0]),
                                        contact_array_val.GetTuple(i)[0],
                                        int(saddle_2s.GetTuple(i)[0]))
        contact_point_2 = ContactPoint(int(contact_array_max_2.GetTuple(i)[0]),
                                        input_polydata.GetPoint(i),
                                        int(contact_array_max_1.GetTuple(i)[0]),
                                        contact_array_val.GetTuple(i)[0],
                                        int(saddle_2s.GetTuple(i)[0]))

        contact_network_dict[contact_array_max_1.GetTuple(i)[0]].append(contact_point_1)
        contact_network_dict[contact_array_max_2.GetTuple(i)[0]].append(contact_point_2)
    return contact_network_dict


def get_saddle_contacts(input_polydata):
    '''
    returns the dict with <key := saddle id and value := list of grain cp_ids>
    @param input_polydata: the input data (polydata)
    @return: a dict of contact network of each grain key is CP ID and value is the
    list of CP ID of other grains
    '''
    saddle_contact_dict = {}
    saddle_array = input_polydata.GetPointData().GetArray("CP ID")
    grains_1 = input_polydata.GetPointData().GetArray("Max 1")
    grains_2 = input_polydata.GetPointData().GetArray("Max 2")
    for i in range(saddle_array.GetNumberOfTuples()):
        if saddle_array.GetTuple(i)[0] not in saddle_contact_dict:
            saddle_contact_dict[saddle_array.GetTuple(i)[0]] = set()
        saddle_contact_dict[saddle_array.GetTuple(i)[0]].add(grains_1.GetTuple(i)[0])
        saddle_contact_dict[saddle_array.GetTuple(i)[0]].add(grains_2.GetTuple(i)[0])
    return saddle_contact_dict


def get_pointcloud(input_data, id, point_array_name="CP ID"):
    """
    Get the point cloud of the input_data.
    @param input_data: the input data (unsructured grid)
    @param id: the id of the point cloud
    @return: the point cloud of the input_data

    example:
        input_data = utils.read_vtp_file(config.SEGMENTATION_FILE)
        point_cloud = utils.get_pointcloud(input_data, 376.0)

        fileutil.save(input_data, "single_grain.vtp")
    """
    point_cloud = vtk.vtkPolyData()
    point_array = input_data.GetPointData().GetArray(point_array_name)
    points = vtk.vtkPoints()
    for i in range(point_array.GetNumberOfTuples()):
        if point_array.GetTuple(i) == (id,):
            points.InsertNextPoint(input_data.GetPoint(i))
    cell_array = vtk.vtkCellArray()
    for i in range(points.GetNumberOfPoints()):
        cell_array.InsertNextCell(1)
        cell_array.InsertCellPoint(i)
    point_cloud.SetPoints(points)
    point_cloud.SetVerts(cell_array)
    return point_cloud


def get_centroid(ugrid):
    '''
    Get the centroid of the input_data.
    @param input_data: the input data (unsructured grid)
    @return: the centroid of the input_data
    '''

    # get the number of points
    cellCenters = vtk.vtkCellCenters()
    cellCenters.SetInputData(ugrid)
    cellCenters.Update()

    # get the number of points
    num_points = cellCenters.GetOutput().GetNumberOfPoints()

    # get the centroid
    centroid = [0, 0, 0]
    for i in range(num_points):
        point = cellCenters.GetOutput().GetPoint(i)
        centroid[0] += point[0]
        centroid[1] += point[1]
        centroid[2] += point[2]

    centroid[0] /= num_points
    centroid[1] /= num_points
    centroid[2] /= num_points

    return centroid


def compute_normals(input_data):
    '''
    Compute the point normals and cell normals
    @param input_data: Poly data
    @return: poly data with normals
    '''
    # use the face normals of the object to define the normals for the
    # texture map
    normals = vtk.vtkPPolyDataNormals()
    normals.SetInputData(input_data)
    normals.SetFeatureAngle(200)
    normals.ComputeCellNormalsOn()
    normals.ComputePointNormalsOn()
    # non manifold traversal on
    normals.NonManifoldTraversalOff()
    normals.SplittingOn()
    normals.ConsistencyOn()
    # normals.AutoOrientNormalsOn()
    normals.Update()
    return normals.GetOutput()


def set_interpolation(actor):
    '''
    set the shading interpolation to Phong, Gouraud, and Flat
    @param actor: the actor
    '''
    actor.GetProperty().SetInterpolationToPhong()
    # actor.GetProperty().SetInterpolationToGouraud()
    # actor.GetProperty().SetInterpolationToFlat()


def render_single_grain(particle_meshfile, maxima_pos, contact_list: list, isContactPts = True, renderer=None):
    '''
    Render the single grain.
    @param particle_meshfile: the particle mesh file
    @param maxima_pos: the maxima position
    @param contact_list: the list of ContactPoint objects
    @param isContactPts: whether to render the contact points (green points)
    '''
    global colors
    # set the bg color
    bg = map(lambda x: x / 255.0, [26, 51, 100, 255])
    colors.SetColor("BkgColor", *bg)

    # extracting id from the file name
    cp_id = int(particle_meshfile.split("/")[-1].split(".")[0])

    particle_src = read_file(particle_meshfile)
    maxima_sphere = vtk.vtkSphereSource()
    centroid_sphere = vtk.vtkSphereSource()
    particle_mapper = vtk.vtkPolyDataMapper()

    particle_src = compute_normals(particle_src)
    # print(normals)

    particle_mapper.SetInputData(particle_src)
    maxima_mapper = vtk.vtkPolyDataMapper()
    maxima_mapper.SetInputConnection(maxima_sphere.GetOutputPort())
    centroid_mapper = vtk.vtkPolyDataMapper()
    centroid_mapper.SetInputConnection(centroid_sphere.GetOutputPort())

    atext = vtk.vtkVectorText()
    atext.SetText(str(cp_id))
    textMapper = vtk.vtkPolyDataMapper()
    textMapper.SetInputConnection(atext.GetOutputPort())
    textActor = vtk.vtkFollower()
    textActor.SetMapper(textMapper)
    textActor.SetScale(0.8, 0.8, 0.8)
    textActor.GetProperty().SetColor(colors.GetColor3d('White'))
    
    if isContactPts:
        contact_pt_sphere = vtk.vtkSphereSource()
        contact_pt_mapper = vtk.vtkPolyDataMapper()
        contact_pt_mapper.SetInputConnection(contact_pt_sphere.GetOutputPort())

    # this actor is a grouping mechanism: besides the geometry (mapper)
    # it also has a property, transformation matrix, and/or texture map.
    # Here we set its color and rotate it 22.5 degrees
    particle_actor = vtk.vtkActor()

    # set interpolation to phong
    set_interpolation(particle_actor)

    maxima_actor = vtk.vtkActor()
    centroid_actor = vtk.vtkActor()
    contact_pt_actor = []
    for i in range(len(contact_list)):
        contact_pt_actor.append(vtk.vtkActor())

    particle_actor.SetMapper(particle_mapper)
    maxima_actor.SetMapper(maxima_mapper)
    centroid_actor.SetMapper(centroid_mapper)
    if isContactPts:
        for i in range(len(contact_list)):
            contact_pt_actor[i].SetMapper(contact_pt_mapper)

    # set object transparency
    particle_actor.GetProperty().SetOpacity(1.0)
    particle_actor.GetProperty().SetMaterialName("Particle_" + str(cp_id))
    textActor.GetProperty().SetMaterialName("Text")

    # interpolation shader
    # object_actor.GetProperty().SetInterpolationToPhong()
    # object_actor.GetProperty().SetInterpolationToFlat()
    # object_actor.GetProperty().SetInterpolationToGouraud()


    maxima_actor.GetProperty().SetMaterialName("Maxima")
    centroid_actor.GetProperty().SetMaterialName("Centroid")
    maxima_actor.GetProperty().SetColor(colors.GetColor3d("Red"))
    centroid_actor.GetProperty().SetColor(colors.GetColor3d("Blue"))

    # center_actor.GetProperty().SetColor(colors.GetColor3d("Green"))
    # translate the center
    maxima_actor.SetPosition(maxima_pos[0], maxima_pos[1], maxima_pos[2])
    centroid_pos = get_centroid(particle_src)
    centroid_actor.SetPosition(centroid_pos[0], centroid_pos[1], centroid_pos[2])
    textActor.AddPosition(centroid_pos[0], centroid_pos[1]-0.3, centroid_pos[2])
    textActor.SetCamera(renderer.GetActiveCamera())
    # Add the actor to the renderer, set the bg and size
    actor_list = []
    # renderer.AddActor(object_actor)
    # renderer.AddActor(maxima_actor)
    # renderer.AddActor(centroid_actor)
    actor_list.append(particle_actor)
    actor_list.append(maxima_actor)
    actor_list.append(centroid_actor)
    actor_list.append(textActor)

    if isContactPts:
        # enumerate the contact points
        for i, contact_pt in enumerate(contact_list):
            contact_pt_actor[i].GetProperty().SetColor(colors.GetColor3d("Green"))
            # name
            contact_pt_actor[i].GetProperty().SetMaterialName("Contact")
            contact_pt_actor[i].SetPosition(contact_pt.position)
            # renderer.AddActor(ellipse_actor[i])
            actor_list.append(contact_pt_actor[i])

    # print the contact points count and grain id
    if isContactPts:
        print("Grain " + str(cp_id) + ": " + str(len(contact_list)) + " contact points")

    return actor_list


def render_polydata(polydata):
    '''
    Render the polydata.
    @param polydata: the polydata
    '''
    colors = vtk.vtkNamedColors()

    # set the bg color
    bg = map(lambda x: x / 255.0, [26, 51, 100, 255])
    colors.SetColor("BkgColor", *bg)

    obj_mapper = vtk.vtkPolyDataMapper()
    obj_mapper.SetInputData(polydata)
    obj_actor = vtk.vtkActor()
    obj_actor.SetMapper(obj_mapper)
    obj_actor.GetProperty().SetColor(colors.GetColor3d("Red"))
    obj_actor.GetProperty().SetMaterialName("Particle")

    # Add the actor to the renderer, set the bg and size
    renderer = vtk.vtkRenderer()
    renderer.AddActor(obj_actor)
    renderer.SetBackground(colors.GetColor3d("BkgColor"))
    
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renderer.GetRenderWindow())
    iren.Initialize()
    iren.Start()


def get_bounding_cylinder(xyz_bounds):
    """
    Create a bounding cylinder from the xyz_bounds.
    @param xyz_bounds: list of xyz bounds
    @return: assembly of actors
    """
    colors = vtk.vtkNamedColors()
    print(xyz_bounds)
    # Create a cylinder
    x1 = xyz_bounds[0]
    x2 = xyz_bounds[1]
    # x1 = xyz_bounds[4]
    # x2 = xyz_bounds[5]
    y1 = xyz_bounds[2]
    y2 = xyz_bounds[3]
    z1 = xyz_bounds[4]
    z2 = xyz_bounds[5]
    # z1 = xyz_bounds[0]
    # z2 = xyz_bounds[1]
    cylinder = vtk.vtkCylinderSource()
    cylinder.SetRadius((x2 - x1) / 2)
    cylinder.SetHeight((z2 - z1) + 2)
    cylinder.SetResolution(50)

    # Create a mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cylinder.GetOutputPort())

    # Create an actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d("Silver"))
    # position the actor
    # rotate
    actor.RotateX(90)
    actor.SetPosition((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2)
    # actor.RotateZ(90)
    # actor.SetPosition((z1 + z2) / 2, (y1 + y2) / 2, (x1 + x2) / 2)
    # opacity
    actor.GetProperty().SetOpacity(0.1)

    # assembly
    assembly = vtk.vtkAssembly()
    assembly.AddPart(actor)

    return assembly


def get_actors_list(maxima_data, contact_points, particle_id, renderer, particle_meshfile, isContacts = True):
    '''
    Returns maxima, contacts points as spheres actors along with grain
    @param maxima_data: maxima point location
    @param contact_points: list of contact points of the grains
    @param particle_id: id of the particle
    @param renderer: vtk renderer
    @param particle_meshfile: mesh file of the particle
    @param isContacts: boolean to indicate if contacts(green points) are to be rendered
    @return: list of actors (particle, maxima point spheres, contact points spheres)
    '''
    cont_list = []
    try:
        cont_list = contact_points[particle_id]
    except KeyError:
        print("get_actors_list(): No contacts points present")
    
    return render_single_grain(
        particle_meshfile, maxima_data[particle_id][0], cont_list, isContactPts=isContacts, renderer=renderer)


def get_color_particle(filename):
    '''
    Get the color of the particle
    @param cp_id: id of the particle
    @return: color
    '''
    grain_data = read_file(filename)
    colors = grain_data.GetPointData().GetArray("Color")
    color = colors.GetTuple3(0)
    # convert (r,g,b) to hex
    hex_color = "#%02x%02x%02x" % (int(color[0]), int(color[1]), int(color[2]))
    return hex_color


def get_particle_pc_polydata(filename):
    '''
    Get the polydata(point cloud) of the particle
    @param filename: name of the file contains particle id
    @return: polydata
    '''
    input_data = vtk.vtkXMLPolyDataReader()
    input_data.SetFileName(filename)
    input_data.Update()
    return input_data.GetOutput()


def trimesh_to_polydata(tri_mesh):
    '''
    Convert the trimesh object to polydata
    @param tri_mesh: trimesh object
    @return: polydata
    '''
    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(vtk.vtkPoints())
    for vertex in tri_mesh.vertices:
        poly_data.GetPoints().InsertNextPoint(vertex)

    ca = vtk.vtkCellArray()
    for face in tri_mesh.faces:
        triangle = vtk.vtkTriangle()
        triangle.GetPointIds().SetId(0, face[0])
        triangle.GetPointIds().SetId(1, face[1])
        triangle.GetPointIds().SetId(2, face[2])
        ca.InsertNextCell(triangle)

    poly_data.SetPolys(ca)

    poly_data.Modified()

    return poly_data


def get_trimesh_from_polydata(poly_data):
    '''
    Get the trimesh object of the particle
    @param poly_data: polydata
    @return: trimesh object
    '''
    vertices = []
    for i in range(poly_data.GetNumberOfPoints()):
        vertices.append(poly_data.GetPoint(i))

    faces_list = []
    for i in range(poly_data.GetNumberOfCells()):
        face = poly_data.GetCell(i)
        faces_list.append([face.GetPointId(0), face.GetPointId(1), face.GetPointId(2)])

    return trimesh.Trimesh(vertices=vertices, faces=faces_list)


def get_trimesh(filename):
    '''
    Get the trimesh object of the particle
    @param filename: filename of the particle
    @return: trimesh object
    '''
    return get_trimesh_from_polydata(read_file(filename))


def copyfile(filename, input_folder, dest_folder):
    '''
    Copy the file from the source to the destination
    @param filename: filename of the particle
    @param input_folder: input folder
    @param dest_folder: destination folder
    '''
    # construct the full path of the source file
    src_file_path = os.path.join(input_folder, filename)

    # construct the full path of the destination file
    dest_file_path = os.path.join(dest_folder, filename)

    # copy the file from the source to the destination
    shutil.copy(src_file_path, dest_file_path)


def mesh_to_polydata(vertices, faces):
    '''
    Convert the mesh to polydata
    @param vertices: vertices of the mesh
    @param faces: faces of the mesh
    @return: polydata
    '''
    return trimesh_to_polydata(trimesh.Trimesh(vertices=vertices, faces=faces))


def make_watertight(file):
    '''
    Make the mesh watertight
    @param file: filename of the particle
    @return: polydata, filename, color
    '''
    print("Repairing: ", file)
    particle_color = get_color_particle(file)
    # converting str "#ffffff" to tuple (r, g, b)
    particle_color = tuple(int(particle_color[i:i+2], 16) for i in (1, 3, 5))
    mesh = get_trimesh(file)
    
    resolution = 20000
    vw, fw = pcu.make_mesh_watertight(mesh.vertices, mesh.faces, resolution=resolution)
    v_decimate, f_decimate, _, _ = pcu.decimate_triangle_mesh(vw, fw, fw.shape[0] // 120)

    return mesh_to_polydata(v_decimate, f_decimate), particle_color


def check_file(filename):
    '''
    Check if the file exists
    @param filename: filename of the particle
    @return: boolean
    '''
    return os.path.isfile(filename)


def delaunay3d_vtk(input_data, my_callback, display_progress=False, cb=None, alpha=3.0):
    '''
    Delaunay 3D using vtk
    @param input_data: input data point cloud
    @param my_callback: callback function
    @param display_progress: boolean to indicate if progress is to be displayed
    @param cb: callback function
    @param alpha: alpha value ( = 0 gives convex hull)
    @return: delaunay polydata
    '''
    # surface reconstruction using vtk
    delaunay = vtk.vtkDelaunay3D()
    delaunay.SetInputData(input_data)
    delaunay.SetAlpha(alpha)
    # tetrahedrons only
    delaunay.AlphaTetsOn()
    # triangle, edges, vertices off
    delaunay.AlphaTrisOff()
    delaunay.AlphaLinesOff()
    delaunay.AlphaVertsOff()
    delaunay.AddObserver("WarningEvent", my_callback)
    if display_progress:
        delaunay.AddObserver("ProgressEvent", cb)
    delaunay.Update()

    return delaunay.GetOutput()





