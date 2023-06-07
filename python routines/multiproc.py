import vtk
import numpy as np
from tqdm import tqdm


def get_vals(pt, arr_3d):
    '''
    this function returns the values of the 8 points
    surrounding the point pt
    Args:
        pt (np.array): point
        arr_3d (np.array): 3d array
    Returns:
        np.array: values of the 8 points surrounding the point pt
    '''
    coords = []
    for x_inc in [-0.5, 0.5]:
        for y_inc in [-0.5, 0.5]:
            for z_inc in [-0.5, 0.5]:
                coords.append((int(pt[0] + x_inc), int(pt[1] + y_inc), int(pt[2] + z_inc)))
    return np.array([arr_3d[coord] for coord in coords])


def save_grain_vtp(cp_id, msc, dp, img, ensem_dir):
    '''
    this function traverses the des_geom of a critical point and
    saves the points in a vtp file
    Args:
        cp_id (int): critical point id
        msc (pyms3d.mscomplex): mscomplex object
        dp (np.array): dual points
        img (np.array): distance field
        ensem_dir (str): directory to save the vtp file
    '''
    if(msc.cp_func(cp_id) <= 0):
        return

    pa, cp_ids = vtk.vtkPoints(), vtk.vtkIntArray()
    ca = vtk.vtkCellArray()
    val = vtk.vtkFloatArray()
    cp_ids.SetName("CP ID")
    val.SetName('Distance Val')

    des_geom = msc.des_geom(cp_id)
    for cube_id in des_geom:
        dual_pt = dp[cube_id]
        vals = get_vals(dual_pt, img)
        if (max(vals) < 0):
            continue
        val.InsertNextValue(
            img[int(dual_pt[0]), int(dual_pt[1]), int(dual_pt[2])])
        pa.InsertNextPoint(dual_pt)
        cp_ids.InsertNextValue(cp_id)
        ca.InsertNextCell(1)
        ca.InsertCellPoint(pa.GetNumberOfPoints() - 1)
        
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(pa)
    polydata.GetPointData().AddArray(val)
    polydata.GetPointData().AddArray(cp_ids)
    polydata.SetVerts(ca)

    # Write the file
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(ensem_dir + "/grain_%d.vtp" % cp_id)
    writer.SetInputData(polydata)
    writer.Write()


def proc_work(list_cp_ids, msc, dp, img, ensem_dir):
    '''
    this function traverses the des_geom of a critical point and
    saves the points in a vtp file.
    this function is used for multiprocessing.
    Args:
        list_cp_ids (list): list of critical point ids
        msc (pyms3d.mscomplex): mscomplex object
        dp (np.array): dual points
        img (np.array): distance field
        ensem_dir (str): directory to save the vtp file
    '''
    for cp_id in tqdm(list_cp_ids):
        save_grain_vtp(cp_id, msc, dp, img, ensem_dir)


def contact_region_task(pid, save_dir, list_2_saddle, msc, primal_pts, image, isDesManifold):
    '''
    this function extracts the survival saddles, critical point ids and
    descending manifold quadrants for a given process id.
    this function is used for multiprocessing.
    Args:
        pid (int): process id
        save_dir (str): directory to save the data
        list_2_saddle (list): list of 2-saddle points
        msc (pyms3d.mscomplex): mscomplex object
        primal_pts (np.array): primal points
        image (np.array): distance field
        isDesManifold (bool): flag to extract descending manifold
    '''
    surv_sads = np.array([])
    cp_ids = np.array([])
    des_man_quads = []
    for s in tqdm(list_2_saddle):
        # ignore the saddles in background
        # or saddle which is connected to just one maxima
        if (msc.cp_func(s) < 0) or (len(msc.asc(s)) != 2):
            # print("Saddle belongs to background")
            continue

        # if (msc.cp_func(msc.asc(s)[0, 0]) < 0) or (msc.cp_func(msc.asc(s)[1, 0]) < 0):
        #     print("This maxima point lies in the background.")

        # Descending manifold geometry of 2-saddle point
        # surv_sads.append(int(s))  # added inplace of exract surv saddle
        surv_sads = np.append(surv_sads, int(s))
        if isDesManifold:
            des_man = msc.des_geom(s)
            for elem in des_man:
                # check if elem in descending manifold belongs to background
                ind = np.ravel_multi_index(
                    primal_pts[elem].astype(int).transpose(), image.shape)
                dist_vals = image.ravel()[ind]
                if (np.min(dist_vals) <= 0):
                    continue

                # for a  correct elem stores the cp_id and des_man_quad
                # cp_ids.append(int(s))
                cp_ids = np.append(cp_ids, int(s))
                des_man_quads.append(elem)
                # des_man_quads = np.append(des_man_quads, elem)
    
    des_man_quads = np.array(des_man_quads)
    # save the data
    np.save(save_dir + "/surv_sads_%d.npy" % pid, surv_sads)
    np.save(save_dir + "/cp_ids_%d.npy" % pid, cp_ids)
    np.save(save_dir + "/des_man_quads_%d.npy" % pid, des_man_quads)