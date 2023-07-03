import argparse
import utils, fileutil


if __name__=='__main__':

    # read cmd line args
    parser = argparse.ArgumentParser(description='Make watertight mesh')
    parser.add_argument('--input', type=str, help='input file')

    args = parser.parse_args()

    polydata, color = utils.make_watertight(args.input)

    # read input file
    fileutil.save_to_vtp(polydata, args.input, color)

    print("Done")