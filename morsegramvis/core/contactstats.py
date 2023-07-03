import core.utils as utils
import vtk
import os
from core import particlestats
from dataclasses import asdict, dataclass
import pandas as pd
import time
import logging
import core.fileutil as fileutil


@dataclass
class Contact(particlestats.Stats):
    '''
    contact stats
    '''
    quads: int  # number of quads in the contact region


def contact_region_task(cr_id, contact_region_dict, contact_region_data, saddle_contact_region_ids, dest_dir):
    '''
    generate contact region for a given contact region
    :param cr_id: contact region id
    :param contact_region_dict: contact region dict
    :param contact_region_data: contact region data
    :param saddle_contact_region_ids: saddle contact region ids
    :param dest_dir: destination directory
    '''
    cellArray = vtk.vtkCellArray()
    points = vtk.vtkPoints()
    npts = 0
    points_dict = {}
    try:
        for cellPtIds in contact_region_dict[cr_id]:
            for pt_ind in cellPtIds:
                if pt_ind not in points_dict:
                    points_dict[pt_ind] = npts
                    npts += 1
        
        npts = 0
        
        for pt_ind in points_dict.keys():
            points.InsertNextPoint(contact_region_data.GetPoints().GetPoint(pt_ind))
        
        for cellPtIds in contact_region_dict[cr_id]:
            cellArray.InsertNextCell(4)
            for i in range(4):
                cellArray.InsertCellPoint(points_dict[cellPtIds[i]])
        
    except KeyError:
        logging.getLogger().error("(contactstats) KeyError: " + str(cr_id))
    
    cr_polydata = vtk.vtkPolyData()
    cr_polydata.SetPoints(points)
    cr_polydata.SetPolys(cellArray)

    fileutil.save(cr_polydata, dest_dir + "/" + str(int(cr_id)) + ".vtp")

    # ========= contact stats =========
    evec_val = particlestats.get_eigen_vectors_values(cr_polydata.GetPoints())
    try:
        numQuads = len(contact_region_dict[cr_id])
    except KeyError:
        logging.getLogger().error("(contactstats) KeyError: " + str(cr_id))
        numQuads = 0
    return Contact( cp_id=cr_id, 
                    centroid=particlestats.compute_centroid(cr_polydata.GetPoints()),
                    eig_vals=evec_val[1],
                    eig_vecs=evec_val[0],
                    quads=numQuads,
                    neighbours=list(saddle_contact_region_ids))


def generate_contact_region(pipe, cont_reg_file, cont_net_file, cont_reg_dir, data_dir):
    '''
    generate contact regions for all the contact points(2-saddle points)
    @param pipe: pipe to send progress
    @param cont_reg_file: contact region file
    @param cont_net_file: contact net file
    @param cont_reg_dir: contact region directory
    @param data_dir: data directory
    '''

    contact_region_data = utils.read_file(cont_reg_file)
    utils.print_all_arrays_point_data(contact_region_data)
    utils.print_all_arrays_cell_data(contact_region_data)

    # cell array RegionId
    regionIdCellArray = contact_region_data.GetCellData().GetArray("RegionId")
    cpIdCellArray = contact_region_data.GetCellData().GetArray("CP ID")

    cell_type_set = set()

    contactstats = {}
    regionIds_dict = {}
    contact_region_dict = {}

    for i in range(contact_region_data.GetNumberOfCells()):
        cell_type_set.add(contact_region_data.GetCell(i).GetCellType())
        regionId = regionIdCellArray.GetValue(i)
        cpId = cpIdCellArray.GetValue(i)

        if cpId not in contact_region_dict:
            contact_region_dict[cpId] = []
        contact_region_dict[cpId].append((  contact_region_data.GetCell(i).GetPointId(0),
                                            contact_region_data.GetCell(i).GetPointId(1),
                                            contact_region_data.GetCell(i).GetPointId(2),
                                            contact_region_data.GetCell(i).GetPointId(3)))

        if cpId not in contactstats:
            contactstats[cpId] = (regionId, 1)
        else:
            contactstats[cpId] = (regionId, contactstats[cpId][1] + 1)
        if regionId not in regionIds_dict:
            regionIds_dict[regionId] = set()
        regionIds_dict[regionId].add(cpId)
        # print(regionId, cpId)

    assert len(cell_type_set) == 1
    print("All cells are of type: ", cell_type_set.pop())

    saddle_contact_region_dict = utils.get_saddle_contacts(utils.read_file(cont_net_file))
    contact_stats_df = pd.DataFrame(columns=[x for x in Contact.__dataclass_fields__.keys()])

    # create folder for contact region
    if not os.path.exists(cont_reg_dir):
        os.makedirs(cont_reg_dir)

    count = 0

    tot_keys = len(saddle_contact_region_dict.keys())
    for key in saddle_contact_region_dict.keys():
        
        prog = (count / tot_keys) * 100
        msg = 'cs{}'.format(int(prog))
        pipe.send(msg.encode('utf-8'))

        # print(key, len(contact_region_dict[key]))
        # write the cell data to a file
        contact_stats_df.loc[count] = asdict(contact_region_task(key,
            contact_region_dict, contact_region_data, saddle_contact_region_dict[key], cont_reg_dir))
        count += 1

    pipe.send('cs100'.encode('utf-8'))

    contact_stats_df.to_csv(data_dir + "contact_stats_" +
     time.strftime("%Y%m%d-%H%M%S") + ".csv", index=True)


def contact_region_actors(cp_ids, cont_reg_dir):
    '''
    This function returns the all the contact regions for the given cp ids
    @param cp_ids: list of cp ids
    @param cont_reg_dir: contact region directory
    @return: list of actors
    '''
    actors = []
    for cp_id in cp_ids:

        try:
            cont_data = utils.read_file(cont_reg_dir + str(cp_id) + ".vtp")
            cont_mapper = vtk.vtkPolyDataMapper()
            cont_mapper.SetInputData(cont_data)

            actor = vtk.vtkActor()
            actor.SetMapper(cont_mapper)
            # material name
            actor.GetProperty().SetMaterialName("Contact Region")
            actors.append(actor)
        except Exception as e:
            logging.getLogger().error("Error in reading contact region \
            file for cp id: " + str(cp_id))
            # if exception is file not found, raise it
            if type(e) == FileNotFoundError:
                raise e
    return actors


def num_cells_contact_region(cp_id, cont_reg_dir):
    '''
    The contact region is a polydata with cells
    the number of cells is the number of quads in the contact region
    @param cp_id: cp id of particle
    @param cont_reg_dir: contact region directory
    @return: number of cells
    '''
    contact_data = utils.read_file(cont_reg_dir + str(cp_id) + ".vtp")
    return contact_data.GetNumberOfCells()




