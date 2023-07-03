import vtk
import os
from core import fileutil, utils


def generate_simplified_maximas(pipe, contacts_file, particles_mesh_dir, simplified_dir):
    """
    Generate the graph containing the simplified maximas along
    with the 2-saddle points.

    @param pipe: the pipe to send the progress to
    @param contacts_file: the contacts file
    @param particles_mesh_dir: the particles mesh directory
    @param simplified_dir: the directory to save the simplified saddle graph
    """
    all_contacts_data = utils.read_file(contacts_file)
    
    tot_points = all_contacts_data.GetNumberOfPoints()

    cp2_cpi_id_index_dict = {}
    cp2_cp_ids = all_contacts_data.GetPointData().GetArray("CP ID")
    max1_ids = all_contacts_data.GetPointData().GetArray("Max 1")
    max2_ids = all_contacts_data.GetPointData().GetArray("Max 2")
    vals = all_contacts_data.GetPointData().GetArray("Val")
    max1_vals = all_contacts_data.GetPointData().GetArray("Max 1 Val")
    max2_vals = all_contacts_data.GetPointData().GetArray("Max 2 Val")
    for i in range(tot_points):
        cp2_cpi_id_index_dict[cp2_cp_ids.GetValue(i)] = i

    
    remainingPoints = vtk.vtkIdList()
    remainingPoints.SetNumberOfIds(tot_points)

    for i in range(tot_points):
        remainingPoints.SetId(i, i)

    files = os.listdir(particles_mesh_dir)
    num_files = len(files)

    for i, f in enumerate(files):
        pipe.send(("sd"+str(int((i+1) * 100 / num_files))).encode('utf-8'))
        polydata = utils.read_file(os.path.join(particles_mesh_dir, f))
        

        # enclosed points filter
        enclosedPoints = vtk.vtkSelectEnclosedPoints()
        enclosedPoints.SetInputData(all_contacts_data)
        enclosedPoints.SetSurfaceData(polydata)
        enclosedPoints.Update()

        simpliedPoints = vtk.vtkPoints()
        ca = vtk.vtkCellArray()
        # scalar int
        cp_type = vtk.vtkIntArray()
        cp_type.SetName("CP Type")

        cp_id, max1_id, max2_id = vtk.vtkIntArray(), vtk.vtkIntArray(), vtk.vtkIntArray()
        val, max1_val, max2_val = vtk.vtkFloatArray(), vtk.vtkFloatArray(), vtk.vtkFloatArray()
        cp_id.SetName("CP ID")
        max1_id.SetName("Max1 ID")
        max2_id.SetName("Max2 ID")
        val.SetName("CP Value")
        max1_val.SetName("Max1 Value")
        max2_val.SetName("Max2 Value")
        count  = 0
        points_inside = []
        for i in range(remainingPoints.GetNumberOfIds()):
            if enclosedPoints.IsInside(remainingPoints.GetId(i)):
                simpliedPoints.InsertNextPoint(all_contacts_data.GetPoint(remainingPoints.GetId(i)))
                cp_type.InsertNextValue(2)
                cp_id.InsertNextValue(cp2_cp_ids.GetValue(remainingPoints.GetId(i)))
                max1_id.InsertNextValue(max1_ids.GetValue(remainingPoints.GetId(i)))
                max2_id.InsertNextValue(max2_ids.GetValue(remainingPoints.GetId(i)))
                val.InsertNextValue(vals.GetValue(remainingPoints.GetId(i)))
                max1_val.InsertNextValue(max1_vals.GetValue(remainingPoints.GetId(i)))
                max2_val.InsertNextValue(max2_vals.GetValue(remainingPoints.GetId(i)))
                ca.InsertNextCell(1)
                ca.InsertCellPoint(count)
                count += 1
                points_inside.append(i)

        
        # remove the points from the remaining points
        for i in points_inside:
            remainingPoints.DeleteId(i)

        # structured grid
        f_simplied_maximas_polydata = vtk.vtkPolyData()
        f_simplied_maximas_polydata.SetPoints(simpliedPoints)
        f_simplied_maximas_polydata.SetVerts(ca)
        f_simplied_maximas_polydata.GetPointData().AddArray(cp_type)
        f_simplied_maximas_polydata.GetPointData().AddArray(cp_id)
        f_simplied_maximas_polydata.GetPointData().AddArray(max1_id)
        f_simplied_maximas_polydata.GetPointData().AddArray(max2_id)
        f_simplied_maximas_polydata.GetPointData().AddArray(val)
        f_simplied_maximas_polydata.GetPointData().AddArray(max1_val)
        f_simplied_maximas_polydata.GetPointData().AddArray(max2_val)

        fileutil.save(f_simplied_maximas_polydata, os.path.join(simplified_dir, f))