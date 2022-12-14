import vtk
from tqdm import tqdm

def save_grain_vtp(cp_id, msc, dp, img, ensem_dir):
    if(msc.cp_func(cp_id) <= 0):
        return

    pa, cp_ids = vtk.vtkPoints(), vtk.vtkIntArray()
    val = vtk.vtkDoubleArray()
    cp_ids.SetName("CP ID")
    val.SetName('Distance Val')

    des_geom = msc.des_geom(cp_id)
    for cube_id in des_geom:
        dual_pt = dp[cube_id]
        if (max(img[int(dual_pt[0] - 0.5), int(dual_pt[1] - 0.5), int(dual_pt[2] - 0.5)],
                img[int(dual_pt[0] + 0.5), int(dual_pt[1] - 0.5), int(dual_pt[2] - 0.5)],
                img[int(dual_pt[0] - 0.5), int(dual_pt[1] + 0.5), int(dual_pt[2] - 0.5)],
                img[int(dual_pt[0] + 0.5), int(dual_pt[1] + 0.5), int(dual_pt[2] - 0.5)],
                img[int(dual_pt[0] - 0.5), int(dual_pt[1] - 0.5), int(dual_pt[2] + 0.5)],
                img[int(dual_pt[0] + 0.5), int(dual_pt[1] - 0.5), int(dual_pt[2] + 0.5)],
                img[int(dual_pt[0] - 0.5), int(dual_pt[1] + 0.5), int(dual_pt[2] + 0.5)],
                img[int(dual_pt[0] + 0.5), int(dual_pt[1] + 0.5), int(dual_pt[2] + 0.5)]) < 0):
            continue
        val.InsertNextValue(
            img[int(dual_pt[0]), int(dual_pt[1]), int(dual_pt[2])])
        pa.InsertNextPoint(dual_pt)
        cp_ids.InsertNextValue(cp_id)
        
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(pa)
    polydata.GetPointData().AddArray(val)
    polydata.GetPointData().AddArray(cp_ids)

    # Write the file
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(ensem_dir + "/grain_%d.vtp" % cp_id)
    writer.SetInputData(polydata)
    writer.Write()


def proc_work(list_cp_ids, msc, dp, img, ensem_dir):
    for cp_id in tqdm(list_cp_ids):
        save_grain_vtp(cp_id, msc, dp, img, ensem_dir)

