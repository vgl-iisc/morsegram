import argparse
import numpy as np
import os
import SimpleITK as sitk
from utilities import read_input_file
from utilities import bd_extraction
from utilities import dist_field_comp

if __name__ == "__main__":
    # positional arguments for the command line
    parser = argparse.ArgumentParser()
    parser.add_argument('data_file', type=str, help='data file name')
    parser.add_argument('factor', type=int, help='downscaling factor')
    args = parser.parse_args()

    # filter input
    while True:
        print("Please select the filter to be used in boundary extraction")
        print("Press 1 : Otsu")
        print("Press 2 : Adaptive")
        x = input("Input:> ")
        if x == "1":
            filtername = "Otsu"
            break
        elif x == "2":
            filtername = "Adaptive"
            break
        else:
            print("Please enter the correct input")

    # slicewise input
    while True:
        x = input("Should the boundary extraction be slicewise ? (yY/nN)")
        if x.lower() == 'y':
            slicewise = True
            break
        elif x.lower() == 'n':
            slicewise = False
            break
        else:
            print("Please enter the correct input")


    # get the inputs
    input_file_name, factor = args.data_file, int(args.factor)

    # name of the file without pathname and extension
    dirpath = os.path.dirname(input_file_name)
    base_name = os.path.basename(input_file_name)
    base_name = os.path.splitext(base_name)[0]

    # read the mat file and get the data -- optionally downsample
    arr = read_input_file(input_file_name, factor)

    # adjust data range (contrast adjustment - imadjust)
    low, upp, typ = np.quantile(arr, 0.01), np.quantile(arr, 0.99), arr.dtype
    arr = (2**16 - 1) * (arr - low) / (upp - low)
    arr = (np.clip(arr, 0, 2**16-1)).astype(typ)


    # write the downsampled file for visualization
    sitk.WriteImage(sitk.GetImageFromArray(arr), dirpath + '/' + base_name + '_ds_'+ str(factor) + '.mhd')

    # get the binary volume
    ls = bd_extraction(arr, slicewise=slicewise, filterName=filtername)
    # get the distance field
    dist_field = dist_field_comp(ls)

    print('Writing File')
    output_path_name = '../ChamferDistance/'
    if not os.path.exists(output_path_name):
        os.makedirs(output_path_name)
    sitk.WriteImage(sitk.GetImageFromArray(dist_field),
                    output_path_name+'chamf_distance_'+base_name+'.mhd')

    print('File Written')
