import skimage.io as io
from skimage.segmentation import morphological_chan_vese
import SimpleITK as sitk
from skimage.filters import threshold_otsu,threshold_local,rank
from skimage.morphology import cube
import numpy as np


#dist_file_name="chamfer_dist.mhd"

main_file_name="Steel_Deposition_362_352_502.mhd"

raw_writer = sitk.ImageFileWriter()

reader=sitk.ImageFileReader()
reader.SetImageIO("MetaImageIO")
reader.SetFileName(main_file_name)

image=reader.Execute()

#reader=sitk.ImageFileReader()
#reader.SetImageIO("MetaImageIO")
#reader.SetFileName(dist_file_name)

#dist_image=reader.Execute()

#dist_image=sitk.GetArrayFromImage(dist_image)


otsuFilter=sitk.OtsuThresholdImageFilter()

#thresholdFilter=sitk.BinaryThresholdImageFilter()

otsuFilter.Execute(image)

print('otsu done')

dist_image=image - otsuFilter.GetThreshold()

dist_image=sitk.GetArrayFromImage(dist_image)

image=sitk.GetArrayFromImage(image)

print('ready to start chan vese')

ls = morphological_chan_vese(image, 5, init_level_set=dist_image, lambda1=5,smoothing=0)
                                 
print('chan vese done')
         
ls_sitk=sitk.GetImageFromArray(ls)

#print('got image from array')

raw_writer.SetFileName('chan_vese_standard_'+main_file_name)
raw_writer.Execute(ls_sitk)

print('file written')

