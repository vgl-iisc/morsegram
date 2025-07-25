# external and inbuilt modules
import argparse
from matplotlib import pyplot as plt
import numpy as np
import os
import vtk
import tkinter as tk
from tkinter.filedialog import askopenfilename

# PYMS3d related modules
from convert_store_data import write_polydata, write_img_from_arr
from persistence_calculation import compute_pers_diagm
import pyms3d_core as pyms3d
from utilities import bimode_log_min, check_segmentation
from utilities import get_dims, read_msc_to_img
from utilities import get_saddles, compute_contact_regions
from utilities import get_cp, get_extremum_graph
from utilities import get_segmentation_index_dual
import pandas as pd

def disp_pers_curve(data_file_name, dim, msc_file_name, output_path_name, mode):
    '''
    Display the persistence curve

    Args:
        data_file_name (str): raw file with distance field
        dim (tuple): dimensions of distance field
        msc_file_name (str): name of the msc file
        output_path_name (str): path to store the output

    Returns:
        float: persistence threshold
    '''
    print("Computing Persistence Curve")
    # compute the persistence diagram and curve
    
    # get the persistence threshold
    percent_pers = compute_pers_diagm(data_file_name, dim, mode)
    if mode == "manual":
        percent_pers = float(input("enter the knee point : "))
    else:
        if percent_pers == None:
            print("Auto detection failed")
            percent_pers = float(input("enter the knee point : "))
        else:
            print("detected knee point value is " + str(percent_pers))
    with open(output_path_name + msc_file_name + '.txt', 'w') as f:
        f.write(str(percent_pers))
    return percent_pers


def initial_msc(data_file_name, dim, msc_file_name, output_path_name):
    '''
    Compute the initial msc

    Args:
        data_file_name (str): raw file with distance field
        dim (tuple): dimensions of distance field
        msc_file_name (str): name of the msc file
        output_path_name (str): path to store the output

    Returns:
        msc: initial msc
    '''
    print("Computing initial Morse-Smale Complex")
        # compute the mscomplex
    msc = pyms3d.MsComplexPyms3D()
        # compute the mscomplex from a structured grid with scalars
    msc.compute_bin(data_file_name, dim)
        # save the initial Morse-Smale complex
    msc.save(output_path_name+msc_file_name)
    return msc


def simplify_msc(dim, percent_pers, msc):
    '''
    Simplify the msc

    Args:
        dim (tuple): dimensions of distance field
        percent_pers (float): persistence threshold
        msc (msc): initial msc

    Returns:
        img: msc vert function to image
    '''
    print("Computing Simplified Morse-Smale Complex")
        # msc vert function to image
    img = read_msc_to_img(msc, dim)
        # simplify mscomplex with manually selected threshold
    print('Writing Critical Points : (3)')
    write_polydata(get_cp(msc, 3), "../Outputs/cps_3.vtp")
    print('Writing Critical Points : (2)')
    write_polydata(get_cp(msc, 2), "../Outputs/cps_2.vtp")
    _, all_saddles = compute_contact_regions(msc, img, False)
    print('compute contact regions done')
    all_contacts, _ = get_saddles(msc, all_saddles)
    print('Writing All Contacts')
    write_polydata(all_contacts, output_path_name +
                       base_name + '_contacts_all.vtp')
    msc.simplify_pers(thresh=percent_pers, is_nrm=False)

    print('MSC Simplified')
    return img


def compute_contact_reg(base_name, output_path_name, msc, img):
    '''
    Compute the contact regions

    Args:
        base_name (str): base name of the output
        output_path_name (str): path to store the output
        msc (msc): initial msc
        img (img): msc vert function to image

    Returns:
        maxs (list): list of maxima
    '''


    print('Computing Contact Regions')
        # remove saddles that lie in the backgraound
        # also remove the voxels of descending manifold in the background
    des_man, surv_sads = compute_contact_regions(msc, img)  # issues
    print('Contact Regions Extracted')
        # contacts from surviving saddles
    contacts, maxs = get_saddles(msc, surv_sads)
    print('Contacts Computed')
        # grain centers in critical point cell ids
    grain_centres = get_cp(msc, 3)
    print('Grain Centres Computed')
        # connectivity network
    connectivity_network = get_extremum_graph(msc, surv_sads)
    print('Connectivity Network Computed')
    write_polydata(grain_centres, output_path_name +
                       base_name + '_grain_centres.vtp')
    write_polydata(contacts, output_path_name +
                       base_name + '_contacts.vtp')
    write_polydata(des_man, output_path_name +
                       base_name + '_contact_regions.vtp')
    write_polydata(connectivity_network, output_path_name + base_name +
                       '_connectivity_network.vtp')
                   
    return maxs


def compute_seg(base_name, output_path_name, msc, img):
    '''
    Compute the segmentation

    Args:
        base_name (str): base name of the output
        output_path_name (str): path to store the output
        msc (msc): initial msc
        img (img): msc vert function to image

    Returns:
        segmentation (vtp): segmentation
        centers (list): list of centers
        maximas (list): list of maximas
        labs (list): list of labels
        vols (list): list of volumes
    '''
    
    segmentation,centers,maximas,labs,vols = None,None,None,None,None
    print("Computing Segmentation")
    try:
        rind = int(input("Output type (0 -- vtp, 1 -- numpy): \n"))
    except:
        print("Wrong number, numpy array will be computed")
        rind = 1

    rtype = "VTP" if (rind == 0) else "NP"

    if rind == 0:
        segmentation = get_segmentation_index_dual(msc, img, rtype)
        write_polydata(segmentation, output_path_name +
                           base_name + '_segmentation.vtp')
    else:
        segmentation, centers, maximas, labs, vols = \
                get_segmentation_index_dual(msc, img, rtype)
    print('Segmentation Computed')
    return segmentation,centers,maximas,labs,vols


if __name__ == "__main__":
    # get the arguments from command line -- data_file
    parser = argparse.ArgumentParser()
    parser.add_argument('data_file', type=str, help='raw distance field file name')
    parser.add_argument('--mode', type=str, help='automatic / manual pipeline', required=False, default="manual")

    # capture the arguments in args
    args = parser.parse_args()
    data_file_name, dim = args.data_file, get_dims(args.data_file)

    # get the base name for storing other variables
    base_name = os.path.splitext(os.path.basename(data_file_name))[0]

    msc_file_name = 'msc_' + base_name + '_initial'

    # output path name -- if not make the output path directory
    output_path_name = '../Outputs/'
    if not os.path.exists(output_path_name):
        os.makedirs(output_path_name)
    
    while(True):
        # this if statement is for the auto mode of the program
        if args.mode == "auto":
            percent_pers = disp_pers_curve(data_file_name, dim, msc_file_name, output_path_name, args.mode)
            msc = initial_msc(data_file_name, dim, msc_file_name, output_path_name)
            img = simplify_msc(dim, percent_pers, msc)
            maxs = compute_contact_reg(base_name, output_path_name, msc, img)
            segmentation = get_segmentation_index_dual(msc, img, "VTP")
            write_polydata(segmentation, output_path_name +
                            base_name + '_segmentation.vtp')
            break

        print(pyms3d.get_hw_info())

        val = int(input("1. Display Persistence Curve\n"
                        "2. Compute initial Morse-Smale Complex\n"
                        "3  Simplify Morse-Smale Complex\n"
                        "4. Compute Contact Information\n"
                        "5. Compute Segmentation\n"
                        "6. Clean Up Segmentation\n"
                        "7. Check Segmentation\n"
                        "8. Load Stored MSC\n"
                        "9. Exit\n"))

        if (val == 1):
            percent_pers = disp_pers_curve(data_file_name, dim, msc_file_name, output_path_name, args.mode)
        if (val == 2):
            msc = initial_msc(data_file_name, dim, msc_file_name, output_path_name)
        if (val == 3):
            img = simplify_msc(dim, percent_pers, msc)
        if(val == 4):
            maxs = compute_contact_reg(base_name, output_path_name, msc, img)
        if(val == 5):
            segmentation, centers, maximas, labs, vols = compute_seg(base_name, output_path_name, msc, img)

        if (val == 6):
            print("Cleaning up the segmentation")
            del_list = []
            plt.figure()
            plt.hist(np.log(vols), bins=30)
            plt.show()

            vol_cutoff = float(input('The cutoff value: '))  # bimode_log_min(vols)
            # print(f'Volume cutoff is: {vol_cutoff}')
            for ii, mid in enumerate(labs):
                if (mid not in maxs) and (vols[ii] < vol_cutoff):
                    segmentation[segmentation == mid] = 0
                    del_list.append(ii)

            print(f'Number of deleted labels: {len(del_list)}')
            centers = [centers[ii]
                    for ii in range(len(centers)) if ii not in del_list]
            maximas = [maximas[ii]
                    for ii in range(len(maximas)) if ii not in del_list]
            labs = [labs[ii] for ii in range(len(labs)) if ii not in del_list]
            vols = [vols[ii] for ii in range(len(vols)) if ii not in del_list]
            print(f'Number of labels: {len(labs)}')

            pa1, pa2, ia, fa = vtk.vtkPoints(), vtk.vtkPoints(),\
                vtk.vtkIntArray(), vtk.vtkFloatArray()
            ca = vtk.vtkCellArray()
            ia.SetName("Label")
            fa.SetName("Volume")
            for i, (center, maxima, lab, vol)\
                    in enumerate(zip(centers, maximas, labs, vols)):
                pa1.InsertNextPoint(center)
                pa2.InsertNextPoint(maxima)
                ia.InsertNextValue(lab)
                fa.InsertNextValue(vol)
                ca.InsertNextCell(1)
                ca.InsertCellPoint(i)
            pd = vtk.vtkPolyData()
            pd.SetPoints(pa2)
            pd.SetVerts(ca)
            pd.GetPointData().AddArray(ia)
            pd.GetPointData().AddArray(fa)
            write_polydata(pd, output_path_name +
                        base_name + "_LabelProperties.vtp")
            write_img_from_arr(
                segmentation, output_path_name + base_name + '_Segmentation')

        if (val == 7):
            print('Writing marked images in files: ', '( ', base_name, ' )')
            root = tk.Tk()
            root.withdraw()
            raw_file_name = askopenfilename(
                initialdir='./convert_downsample', title='Select mhd raw file')
            check_segmentation(raw_file_name, centers)

        if (val == 8):
            root = tk.Tk()
            root.withdraw()
            file_name = askopenfilename(
                initialdir='../Outputs', title='Select initial Morse complex file')
            # file_name = input("Enter Path For Initial Morse-Smale Complex: \n")
            msc = pyms3d.mscomplex()
            msc.load(file_name)
            with open(output_path_name + msc_file_name + '.txt', 'r') as f:
                percent_pers = float(f.read())
                print("The last stored persistence threshold is: ", percent_pers)
            print("Compute the Simplified Morse-Smale Complex")
        
        if (val == 9):
            print("exiting")
            break
