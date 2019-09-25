from scipy.io import loadmat
from skimage.measure import block_reduce
import SimpleITK as sitk
import numpy as np

img_arr=loadmat('Mixed_Glass_Epoxy.mat')
img_arr=img_arr['volm']

print(np.shape(img_arr))

fac=(2,2,2)
downsampled_img=block_reduce(img_arr,fac,func=np.mean)

print(np.shape(downsampled_img))

downsampled_img=sitk.GetImageFromArray(downsampled_img)

raw_writer=sitk.ImageFileWriter()
raw_writer.SetFileName('Mixed_Glass_Epoxy_362_352_502.mhd')
raw_writer.Execute(downsampled_img)

