import itk
import SimpleITK as sitk
import numpy as np

main_file_name="chan_vese_standard_Steel_Deposition_362_352_502.mhd"

raw_writer = sitk.ImageFileWriter()

reader=sitk.ImageFileReader()
reader.SetImageIO("MetaImageIO")
reader.SetFileName(main_file_name)

image=reader.Execute()

arr_image=sitk.GetArrayFromImage(image)

itk_image=itk.GetImageFromArray(np.array(arr_image).astype(np.float32))

antialiasfilter = itk.AntiAliasBinaryImageFilter.New(itk_image)
antialiasfilter.SetInput(itk_image)
antialiasfilter.Update()
antialias_image=antialiasfilter.GetOutput()

#print(itk_image)

isoContourFilter=itk.IsoContourDistanceImageFilter.New(antialias_image)

isoContourFilter.SetLevelSetValue(0.1)

isoContourFilter.SetInput(antialias_image)

isoContourFilter.Update()

isoContour_image=isoContourFilter.GetOutput()

#print(isoContour_image)

chamferFilter=itk.FastChamferDistanceImageFilter.New(isoContour_image)

print(chamferFilter.GetMaximumDistance())

chamferFilter.SetMaximumDistance(100.0)

print(chamferFilter.GetMaximumDistance())

chamferFilter.Update()

print(chamferFilter.GetMaximumDistance())

chamferFilter.SetInput(isoContour_image)

chamferFilter.Update()

#print(chamferFilter.GetMaximumDistance())

chamf_image=chamferFilter.GetOutput()

#isocontour_arr=itk.GetArrayFromImage(

chamf_arr=itk.GetArrayFromImage(chamf_image)

dist_image=sitk.GetImageFromArray(chamf_arr)

raw_writer = sitk.ImageFileWriter()
raw_writer.SetFileName('chamf_distance_'+main_file_name)
raw_writer.Execute(dist_image)


#print(chamf_image)




