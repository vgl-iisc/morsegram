from scipy.io import loadmat
from skimage.measure import block_reduce
import SimpleITK as sitk
import numpy as np

parser=argparse.ArgumentParser()

parser.add_argument('data_file',type=str,help='data file name')

parser.add_argument('factor',type=str,help='downsampling factor')

args=parser.parse_args()

data_file_name = args.data_file

factor = args.factor

fac = (factor, factor, factor)

reader = sitk.ImageFileReader()
reader.SetImageIO("MetaImageIO")
writerreader.SetFileName(data_file_name)
img_arr = reader.Execute()

img_arr=sitk.GetArrayFromImage(img_arr)

print(np.shape(img_arr))

downsampled_img=block_reduce(img_arr,fac,func=np.mean)

print(np.shape(downsampled_img)) 

downsampled_img=sitk.GetImageFromArray(downsampled_img)

output_path_name='../Outputs/'
if not os.path.exists(output_path_name):
    os.makedirs(output_path_name)

base_name=os.path.basename(data_file_name)
base_name=os.path.splitext(base_name)[0]

raw_writer=sitk.ImageFileWriter()
raw_writer.SetFileName(output_path_name+'downsampled_'+base_name+'.mhd')
raw_writer.Execute(downsampled_img)

