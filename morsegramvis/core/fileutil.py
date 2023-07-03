import SimpleITK as sitk
import numpy as np
import logging
import vtk


def write_to_mhd(img, space, origin, direction, filename, point_cloud, left_bound, right_bound):
    """
    Write the image to a mhd file
    :param img: the image to write
    :param space: the spacing of the image
    :param origin: the origin of the image
    :param direction: the direction of the image
    :param filename: the filename to write to
    :param point_cloud: the point cloud to write
    :param left_bound: the left bound of the point cloud
    :param right_bound: the right bound of the point cloud
    :return: the image
    """

    # make zero numpy array of the same size as the original image
    npa = np.zeros((right_bound[0] - left_bound[0], 
                    right_bound[1] - left_bound[1], 
                    right_bound[2] - left_bound[2]), dtype=np.float32)
    npa = npa - 3.0
    print(img.GetSize())
    # fill the array with the points in the point cloud
    for point in point_cloud:
        npa[point[0] - left_bound[0]-1, 
            point[1] - left_bound[1]-1, 
            point[2] - left_bound[2]-1] = img[point[0], point[1], point[2]]

    # print("Marked all points outside the point cloud as 0")

    # traspose the array to get the correct orientation
    npa = np.transpose(npa, (2, 1, 0))

    image = sitk.GetImageFromArray(npa)

    # crop the image
    # cropped_image = img[left_bound[0]:right_bound[0], left_bound[1]:right_bound[1], left_bound[2]:right_bound[2]]
    
    image.SetSpacing(space)
    image.SetOrigin(origin)
    image.SetDirection(direction)
    sitk.WriteImage(image, filename)

    return image


def crop_undersegmented_particle(distance_field_file, polydata, output_file):
    """
    Crop the undersegmented particle
    :param distance_field_file: the distance field file
    :param polydata: the polydata of undersegmented particle
    :return: the cropped image
    """

    logging.getLogger().info("Inside crop_undersegmented_particle")

    image_file_reader = sitk.ImageFileReader()
    image_file_reader.SetFileName(distance_field_file)
    image_file_reader.SetImageIO('')

    image = image_file_reader.Execute()

    logging.getLogger().info("Image size: " + str(image.GetSize()))
    logging.getLogger().info("Image spacing: " + str(image.GetSpacing()))
    logging.getLogger().info("Image origin: " + str(image.GetOrigin()))
    logging.getLogger().info("Image direction: " + str(image.GetDirection()))
    logging.getLogger().info("Image pixel type: " + str(image.GetPixelIDTypeAsString()))
    logging.getLogger().info("Image meta data keys: " + str(image.GetMetaDataKeys()))


    point_cloud = []

    logging.getLogger().info("Polydata points: " + str(polydata.GetNumberOfPoints()))

    bounds = polydata.GetBounds()
    offset = 0
    left_bound = (int(bounds[0]) - offset, 
                  int(bounds[2]) - offset, 
                  int(bounds[4]) - offset)
    
    right_bound = (int(bounds[1]) + offset + 1, 
                   int(bounds[3]) + offset + 1, 
                   int(bounds[5]) + offset + 1)

    points = polydata.GetPoints()
    for i in range(points.GetNumberOfPoints()):
        point = points.GetPoint(i)
        # body center coordinate is point
        # add all corner points of the voxel to the point cloud
        for x in range(int(point[0]), int(point[0]) + 2):
            for y in range(int(point[1]), int(point[1]) + 2):
                for z in range(int(point[2]), int(point[2]) + 2):
                    point_cloud.append((x, y, z))


    cropped_image = write_to_mhd(image, image.GetSpacing(), 
                                 left_bound, image.GetDirection(), 
                                 output_file, 
                                 point_cloud, 
                                 left_bound, right_bound)

    logging.getLogger().info("Cropped image size: " + str(cropped_image.GetSize()))


def save(input_data, filename):
    """
    Save to a file
    :param input_data: the data to save
    :param filename: the filename to save to
    """
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(filename)
    writer.SetInputData(input_data)
    writer.Write()


def save_to_vtp(Ugrid, filename, color):
    '''
    Save the unstructured grid to vtp file.
    @param Ugrid: the unstructured grid.
    @param filename: the filename containing the id of the particle
    @param color: the color of the unstructured grid.
    '''
    
    # filename = 'data/CPs/CP_' + str(curr_cp) + '.vtp' 
    curr_cp = int(filename.split('/')[-1].split('.')[0])

    color_scalar = vtk.vtkUnsignedCharArray()
    color_scalar.SetNumberOfComponents(3)
    color_scalar.SetName("Color")
    for i in range(Ugrid.GetNumberOfPoints()):
        color_scalar.InsertNextTuple3(color[0], color[1], color[2])

    Ugrid.GetPointData().SetScalars(color_scalar)

    # add a unique id to each point
    id_scalar = vtk.vtkIdTypeArray()
    id_scalar.SetNumberOfComponents(1)
    id_scalar.SetName("CP ID")
    for i in range(Ugrid.GetNumberOfPoints()):
        id_scalar.InsertNextTuple1(curr_cp)

    Ugrid.GetPointData().AddArray(id_scalar)

    # add a unique id to each cell
    id_scalar = vtk.vtkIdTypeArray()
    id_scalar.SetNumberOfComponents(1)
    id_scalar.SetName("CP ID")
    for i in range(Ugrid.GetNumberOfCells()):
        id_scalar.InsertNextTuple1(curr_cp)

    Ugrid.GetCellData().AddArray(id_scalar)

    Ugrid.Modified()
    # print(Ugrid)
    save(Ugrid, filename)


