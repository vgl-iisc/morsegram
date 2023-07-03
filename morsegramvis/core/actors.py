import vtk
from settings import Config
from core import utils


SIM_TEXT_ACTOR_NAME = "simplified_triples_text_"


def get_extremum_graph_actor(root, adj_list, maxima_data):
    '''
    Extremum graph - particle - [(saddle, neighbour),(),...]
    If multiple saddle points are connected to the same neighbour, then
    the saddle point with maximum scalar value is chosen.
    @param root: reference particle
    @param adj_list: list containing [(saddle, neighbour),(),...]
    @param maxima_data: maxima data - {max_index_3: (position, scalar value)}
    @return: vtkActor containing the edges as tubes
    '''
    nodes = [root]
    dict_neighbours_with_max_saddle = {}

    for contact_pt in adj_list:
        if contact_pt.sibling_cp_id not in dict_neighbours_with_max_saddle:
            dict_neighbours_with_max_saddle[contact_pt.sibling_cp_id] = (contact_pt.position, contact_pt.distance_val)
        else:
            # choosing the saddle point with maximum distance value
            if contact_pt.distance_val > dict_neighbours_with_max_saddle[contact_pt.sibling_cp_id][1]:
                dict_neighbours_with_max_saddle[contact_pt.sibling_cp_id] = (
                    contact_pt.position, contact_pt.distance_val)
                
    for k, v in dict_neighbours_with_max_saddle.items():
        nodes.append(v[0])
        nodes.append(maxima_data[k][0])
    points = vtk.vtkPoints()
    for node in nodes:
        points.InsertNextPoint(node[0], node[1], node[2])
    # lines
    lines = vtk.vtkCellArray()
    # 0 - root, 1,3,5,7 - saddle, 2,4,6,8 - neighbours
    for i in range(len(nodes)-1):
        if i % 2 == 1:
            # root and saddle line
            lines.InsertNextCell(2)
            lines.InsertCellPoint(0)
            lines.InsertCellPoint(i)
        else:
            # saddle and neighbour line
            lines.InsertNextCell(2)
            lines.InsertCellPoint(i + 1)
            lines.InsertCellPoint(i + 2)

    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)

    # tube filter
    tube_filter = vtk.vtkTubeFilter()
    tube_filter.SetInputData(poly_data)
    tube_filter.SetRadius(0.1)
    tube_filter.SetNumberOfSides(20)
    tube_filter.Update()

    # mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(tube_filter.GetOutputPort())

    # actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    # specular lighting
    actor.GetProperty().SetSpecular(1)
    actor.GetProperty().SetSpecularPower(100)
    # name
    actor.GetProperty().SetMaterialName("graph")

    return actor


class Triples():
    '''
    this class stores the triples(max3, saddle, max3) data
    to be used in the study of simplification( pairing saddle - max3 pairs)
    and also, to compute the alpha value(a contact metric).
    '''
    def __init__(self):
        self.pos1 = (0,0,0)
        self.pos2 = (0,0,0)
        self.pos3 = (0,0,0)
        self.val1 = 0
        self.val2 = 0
        self.val3 = 0
        self.alpha = 0


def get_simplified_triples(particle_id, parent):
    '''
    this function creates the simplified triples actor (max_3, saddle, max_3)
    , the text actor for alpha values of the triples and add actors to the renderer
    of the parent class.
    
    @param particle_id: particle id
    @param parent: parent class - Viewparticles
    '''
    data = utils.read_file(Config.SIMPLIFIED_DIR + str(particle_id) + ".vtp")
    utils.print_all_arrays_point_data(data)

    max1_ids = data.GetPointData().GetArray("Max1 ID")
    max2_ids = data.GetPointData().GetArray("Max2 ID")
    vals = data.GetPointData().GetArray("CP Value")
    max1_value = data.GetPointData().GetArray("Max1 Value")
    max2_value = data.GetPointData().GetArray("Max2 Value")

    cp3_data = utils.read_file(Config.CP3_FILE)
    cp3_ids = cp3_data.GetPointData().GetArray("CP ID")
    cp3_id_pos_dict = {}
    for i in range(cp3_data.GetNumberOfPoints()):
        cp3_id_pos_dict[cp3_ids.GetValue(i)] = cp3_data.GetPoint(i)

    numPoints = data.GetNumberOfPoints()
    list_triples = []
    # adding the position of saddle points
    for i in range(numPoints):
        triple = Triples()
        triple.pos1 = cp3_id_pos_dict[max1_ids.GetValue(i)]
        triple.pos2 = data.GetPoint(i)
        triple.pos3 = cp3_id_pos_dict[max2_ids.GetValue(i)]
        triple.val1 = max1_value.GetValue(i)
        triple.val2 = vals.GetValue(i)
        triple.val3 = max2_value.GetValue(i)
        if triple.val1 > triple.val3:
            triple.alpha = 1 - (triple.val2 / triple.val3)
        else:
            triple.alpha = 1 - (triple.val2 / triple.val1)
        list_triples.append(triple)
    
    # creating the actor
    points = vtk.vtkPoints()
    for triple in list_triples:
        points.InsertNextPoint(triple.pos1[0], triple.pos1[1], triple.pos1[2])
        points.InsertNextPoint(triple.pos2[0], triple.pos2[1], triple.pos2[2])
        points.InsertNextPoint(triple.pos3[0], triple.pos3[1], triple.pos3[2])

    # lines
    lines = vtk.vtkCellArray()
    # 0,1,2 - triple, 3,4,5 - triple, ...
    for i in range(len(list_triples)):
        lines.InsertNextCell(2)
        lines.InsertCellPoint(3*i)
        lines.InsertCellPoint(3*i+1)
        lines.InsertNextCell(2)
        lines.InsertCellPoint(3*i+1)
        lines.InsertCellPoint(3*i+2)
    
    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)

    # tube filter
    tube_filter = vtk.vtkTubeFilter()
    tube_filter.SetInputData(poly_data)
    tube_filter.SetRadius(0.01)
    tube_filter.SetNumberOfSides(20)
    tube_filter.Update()

    # mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(tube_filter.GetOutputPort())

    # actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    # specular lighting
    actor.GetProperty().SetSpecular(1)
    actor.GetProperty().SetSpecularPower(100)
    # name
    actor.GetProperty().SetMaterialName("simplified_triples")
    parent.ren.AddActor(actor)

    # # composite actor
    # composite_actor = vtk.vtkPropAssembly()
    # composite_actor.AddPart(actor)

    # sphere actor
    for triple in list_triples:
        # create a sphere
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetCenter(triple.pos2[0], triple.pos2[1], triple.pos2[2])
        sphereSource.SetRadius(0.1)
        sphereSource.Update()

        # mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        
        # actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        # color - pink
        actor.GetProperty().SetColor(1, 0, 1)
        # specular lighting
        actor.GetProperty().SetSpecular(1)
        actor.GetProperty().SetSpecularPower(100)
        # name
        actor.GetProperty().SetMaterialName("simplified_triples_sphere")
        # composite_actor.AddPart(actor)
        parent.ren.AddActor(actor)

        # add text
        text = vtk.vtkVectorText()
        text.SetText(str(round(triple.alpha, 2)))
        text.Update()

        # mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(text.GetOutputPort())

        # actor
        text_follower = vtk.vtkFollower()
        text_follower.SetMapper(mapper)
        text_follower.SetPosition(triple.pos2[0], triple.pos2[1], triple.pos2[2])
        # size
        text_follower.SetScale(0.5, 0.5, 0.5)
        text_follower.SetCamera(parent.ren.GetActiveCamera())
        # name
        text_follower.GetProperty().SetMaterialName(SIM_TEXT_ACTOR_NAME + str(triple.alpha))
        curr_alpha_range = parent.alpha_range
        if curr_alpha_range[0] <= triple.alpha <= curr_alpha_range[1] and parent.show_simplified_text_actor:
            text_follower.SetVisibility(True)
        else:
            text_follower.SetVisibility(False)

        # # add to composite actor
        # composite_actor.AddPart(t_actor)
        parent.ren.AddActor(text_follower)

    parent.show_simplified_saddle_actor = True
    # return composite_actor


def alpha_hist(list_triples):
    '''
    this function prints the histogram of alpha values
    @param list_triples: list of triples(max3, saddle, max3)
    '''
    print("===================== Alpha =====================")
    print("Number of triples: ", len(list_triples))
    print("min alpha: ", min(list_triples, key=lambda x: x.alpha).alpha)
    print("max alpha: ", max(list_triples, key=lambda x: x.alpha).alpha)
    histogram = {}
    # keys - (0.0, 0.1), (0.1, 0.14), (0.14, 0.2), ...
    histogram[(0.0, 0.1)] = 0
    histogram[(0.1, 0.14)] = 0
    histogram[(0.14, 0.2)] = 0
    for i in range(8):
        histogram[(0.2 + 0.1*i, 0.2 + 0.1*(i+1))] = 0
    
    for triple in list_triples:
        for key in histogram.keys():
            if key[0] <= triple.alpha < key[1]:
                histogram[key] += 1
    for key in histogram.keys():
        print(key, " : ", histogram[key])
    print("=================================================")


