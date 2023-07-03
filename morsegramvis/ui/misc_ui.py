from PySide6 import QtCore
from PySide6.QtWidgets import QLabel
from PySide6 import QtWidgets
from PySide6.QtGui import QColor, QPainter, QPixmap, QFont
from core import utils, fileutil
from core.particleseg import Label
from core import multiproc
import settings
import vtk
import h5py
from scipy import io
import numpy as np
import SimpleITK as sitk
import os
import glob
import multiprocessing
import pickle
from tqdm import tqdm
from ui import form_nav
from enum import Enum


def create_convert_mat_to_mhd_ui(parent_widget):
    """
    this function creates the UI for the convert mat to mhd tool
    
    @param parent_widget: the parent widget
    @return: the frame containing the UI
    """

    # Create the Qt Frame to hold the UI
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    frame.setFrameShadow(QtWidgets.QFrame.Sunken)

    # Create the Form Elements
    input_label = QtWidgets.QLabel("Input File:")
    parent_widget.convert_input_line_edit = QtWidgets.QLineEdit()
    parent_widget.convert_input_line_edit.setReadOnly(True)
    input_browse_button = QtWidgets.QPushButton("Browse")
    # input_browse_button.clicked.connect(parent_widget.show_file_picker)
    input_browse_button.clicked.connect(lambda: parent_widget.show_file_picker(parent_widget.convert_input_line_edit))

    output_label = QtWidgets.QLabel("Output File:")
    parent_widget.convert_output_line_edit = QtWidgets.QLineEdit()
    parent_widget.convert_output_line_edit.setReadOnly(True)
    output_browse_button = QtWidgets.QPushButton("Browse")
    # output_browse_button.clicked.connect(parent_widget.save_file_picker)
    output_browse_button.clicked.connect(lambda: parent_widget.save_file_picker(parent_widget.convert_output_line_edit))

    # input array name
    input_array_name_label = QtWidgets.QLabel("Input Array Name:")
    parent_widget.input_array_name_line_edit = QtWidgets.QLineEdit()
    parent_widget.input_array_name_line_edit.setText("data")

    # checkbox for transpose
    parent_widget.transpose_checkbox = QtWidgets.QCheckBox("Transpose")
    parent_widget.transpose_checkbox.setChecked(True)

    parent_widget.convert_button = QtWidgets.QPushButton("Convert")
    parent_widget.convert_button.clicked.connect(parent_widget.onConvertButtonClicked)

    # Create the Layout
    layout = QtWidgets.QGridLayout()
    layout.addWidget(input_label, 0, 0)
    layout.addWidget(parent_widget.convert_input_line_edit, 0, 1)
    layout.addWidget(input_browse_button, 0, 2)

    layout.addWidget(output_label, 1, 0)
    layout.addWidget(parent_widget.convert_output_line_edit, 1, 1)
    layout.addWidget(output_browse_button, 1, 2)

    layout.addWidget(input_array_name_label, 2, 0)
    layout.addWidget(parent_widget.input_array_name_line_edit, 2, 1)

    layout.addWidget(parent_widget.transpose_checkbox, 3, 0)

    layout.addWidget(parent_widget.convert_button, 4, 0, alignment=QtCore.Qt.AlignCenter)

    # Set the Layout
    frame.setLayout(layout)

    return frame


def create_extract_particle_pc_ui(parent_widget):
    """
    this function creates the UI for the extract particle point cloud tool
    
    @param parent_widget: the parent widget
    @return: the frame containing the UI
    """
    # Create the Qt Frame to hold the UI
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    frame.setFrameShadow(QtWidgets.QFrame.Sunken)

    # Create the Form Elements
    input_label = QtWidgets.QLabel("Input Particle Id:")
    parent_widget.pc_input_line_edit = QtWidgets.QLineEdit()

    output_label = QtWidgets.QLabel("Output File:")
    parent_widget.pc_output_line_edit = QtWidgets.QLineEdit()
    parent_widget.pc_output_line_edit.setReadOnly(True)
    output_browse_button = QtWidgets.QPushButton("Browse")
    output_browse_button.clicked.connect(lambda: parent_widget.save_file_picker(parent_widget.pc_output_line_edit))

    parent_widget.extract_button = QtWidgets.QPushButton("Extract")
    parent_widget.extract_button.clicked.connect(parent_widget.onExtractPCClicked)

    # Create the Layout
    layout = QtWidgets.QGridLayout()
    layout.addWidget(input_label, 0, 0)
    layout.addWidget(parent_widget.pc_input_line_edit, 0, 1)

    layout.addWidget(output_label, 1, 0)
    layout.addWidget(parent_widget.pc_output_line_edit, 1, 1)
    layout.addWidget(output_browse_button, 1, 2)

    layout.addWidget(parent_widget.extract_button, 2, 0, alignment=QtCore.Qt.AlignCenter)

    # Set the Layout
    frame.setLayout(layout)

    return frame


def convert_file(filepath1, filepath2, array_name="data", transpose=True):
    '''
    this function converts file 1 format to file 2 format

    :param filepath1: the input file
    :param filepath2: the output file
    '''
    format1 = filepath1.split(".")[-1]
    format2 = filepath2.split(".")[-1]

    is_7_3_mat_file = False
    if format1 == "mat" and format2 == "mhd":
        try:
            # reading 7.3 MAT-file
            input_file = h5py.File(filepath1, 'r')
            is_7_3_mat_file = True
        except:
            # reading 4.2 MAT-file
            input_file = io.loadmat(filepath1)

        array_names = [key for key in input_file.keys() if not key.startswith("__")]

        if array_name not in array_names:
            raise Exception("Invalid array name")

        data = input_file.get(array_name)
        data = np.array(data)
        if transpose:
            data = np.transpose(data, (2, 1, 0))

        # write the data to a mhd file
        writer = sitk.ImageFileWriter()
        writer.SetFileName(filepath2)
        writer.Execute(sitk.GetImageFromArray(data))

        return data.shape

    else:
        raise Exception("Invalid file format")


def crop_image(filepath1, filepath2, crop_size):
    '''
    this function crops the image

    :param filepath1: the input file
    :param filepath2: the output file
    :param crop_size: the size of the crop
    '''
    format1 = filepath1.split(".")[-1]
    format2 = filepath2.split(".")[-1]

    if format1 == "mhd" and format2 == "mhd":
        # read the image
        reader = sitk.ImageFileReader()
        reader.SetFileName(filepath1)
        image = reader.Execute()

        # crop the image
        image = sitk.Crop(image, crop_size)

        # write the image
        writer = sitk.ImageFileWriter()
        writer.SetFileName(filepath2)
        writer.Execute(image)

    else:
        raise Exception("Invalid file format")


def crop_image_ui(parent_widget):
    '''
    this function creates the UI for the crop image tool

    :param parent_widget: the parent widget
    :return: the frame containing the UI
    '''
    # Create the Qt Frame to hold the UI
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    frame.setFrameShadow(QtWidgets.QFrame.Sunken)

    # Create the Form Elements
    input_label = QtWidgets.QLabel("Input File:")
    parent_widget.input_line_edit = QtWidgets.QLineEdit()
    input_browse_button = QtWidgets.QPushButton("Browse")
    input_browse_button.clicked.connect(parent_widget.show_file_picker)

    # load the file button
    parent_widget.load_button = QtWidgets.QPushButton("Load")
    parent_widget.load_button.clicked.connect(parent_widget.onLoadClicked)

    # input_image_label
    parent_widget.input_image_label = QtWidgets.QLabel("Input Image Size:")

    output_label = QtWidgets.QLabel("Output File:")
    parent_widget.output_line_edit = QtWidgets.QLineEdit()
    parent_widget.output_line_edit.setReadOnly(True)
    output_browse_button = QtWidgets.QPushButton("Browse")
    output_browse_button.clicked.connect(parent_widget.save_file_picker)

    crop_size_label = QtWidgets.QLabel("Crop Size:")
    # x, y, z
    parent_widget.crop_size_line_edit = QtWidgets.QLineEdit()

    parent_widget.crop_button = QtWidgets.QPushButton("Crop")
    parent_widget.crop_button.clicked.connect(parent_widget.onCropClicked)

    # Create the Layout
    layout = QtWidgets.QGridLayout()
    r = 0
    layout.addWidget(input_label, r, 0)
    layout.addWidget(parent_widget.input_line_edit, r, 1)
    layout.addWidget(input_browse_button, r, 2)
    layout.addWidget(parent_widget.load_button, r, 3)

    r += 1
    layout.addWidget(parent_widget.input_image_label, r, 0)

    r += 1
    layout.addWidget(output_label, r, 0)
    layout.addWidget(parent_widget.output_line_edit, r, 1)
    layout.addWidget(output_browse_button, r, 2)

    r += 1
    layout.addWidget(crop_size_label, r, 0)
    layout.addWidget(parent_widget.crop_size_line_edit, r, 1)

    r += 1
    layout.addWidget(parent_widget.crop_button, r, 0, alignment=QtCore.Qt.AlignCenter)

    # Set the Layout
    frame.setLayout(layout)

    return frame


def get_image_size(filepath):
    '''
    this function gets the size of the image

    :param filepath: the input file
    '''
    format1 = filepath.split(".")[-1]

    if format1 == "mhd":
        # read the image
        reader = sitk.ImageFileReader()
        reader.SetFileName(filepath)
        image = reader.Execute()

        return image.GetSize()

    else:
        raise Exception("Invalid file format")


def convert_vtp_to_other_formats_ui(parent_widget):
    '''
    this function creates the UI for the convert vtp to other formats tool

    :param parent_widget: the parent widget
    :return: the frame containing the UI
    '''
    # Create the Qt Frame to hold the UI
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    frame.setFrameShadow(QtWidgets.QFrame.Sunken)

    # Create the Form Elements
    # choose input folder containing vtp files
    input_label = QtWidgets.QLabel("Input Folder:")
    parent_widget.input_line_edit_cf = QtWidgets.QLineEdit()
    input_browse_button = QtWidgets.QPushButton("Browse")
    input_browse_button.clicked.connect(lambda: parent_widget.show_folder_picker(parent_widget.input_line_edit_cf))

    # choose output folder
    output_label = QtWidgets.QLabel("Output Folder:")
    parent_widget.output_line_edit = QtWidgets.QLineEdit()
    output_browse_button = QtWidgets.QPushButton("Browse")
    output_browse_button.clicked.connect(parent_widget.save_folder_picker)

    # choose the format
    format_label = QtWidgets.QLabel("Output Format:")
    parent_widget.format_combo_box = QtWidgets.QComboBox()
    parent_widget.format_combo_box.addItems(["stl", "ply", "obj", "vtk", "vtp"])

    # convert button
    parent_widget.convert_button = QtWidgets.QPushButton("Convert")
    parent_widget.convert_button.clicked.connect(parent_widget.onConvertClicked)

    # Create the Layout
    layout = QtWidgets.QGridLayout()
    r = 0
    layout.addWidget(input_label, r, 0)

    r += 1
    layout.addWidget(parent_widget.input_line_edit_cf, r, 0)
    layout.addWidget(input_browse_button, r, 1)

    r += 1
    layout.addWidget(output_label, r, 0)

    r += 1
    layout.addWidget(parent_widget.output_line_edit, r, 0)
    layout.addWidget(output_browse_button, r, 1)

    r += 1
    layout.addWidget(format_label, r, 0)
    layout.addWidget(parent_widget.format_combo_box, r, 1)

    r += 1
    layout.addWidget(parent_widget.convert_button, r, 0, alignment=QtCore.Qt.AlignCenter)

    # Set the Layout
    frame.setLayout(layout)

    return frame


def convert_vtp_to_other_formats_worker(vtp_file, output_folder, format):
    """
    This function converts a VTP file to the specified format.

    :param vtp_file: The VTP file to convert.
    :param output_folder: The folder to write the converted file to.
    :param format: The format to convert the VTP file to.
    """
    # Load the VTP file
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(vtp_file)
    reader.Update()
    poly_data = reader.GetOutput()

    # Convert to the specified format
    if format == 'stl':
        writer = vtk.vtkSTLWriter()
    elif format == 'ply':
        writer = vtk.vtkPLYWriter()
    elif format == 'obj':
        writer = vtk.vtkOBJExporter()
    else:
        raise ValueError(f'Unsupported format: {format}')

    # Set the output file name and write the file
    output_file = os.path.join(output_folder, os.path.splitext(os.path.basename(vtp_file))[0] + f'.{format}')
    writer.SetFileName(output_file)
    writer.SetInputData(poly_data)
    writer.Write()


def convert_vtp_to_other_formats(input_folder, output_folder, format):
    """
    This function converts all VTP files in the specified input folder to the specified format.

    :param input_folder: The folder containing the VTP files to convert.
    :param output_folder: The folder to write the converted files to.
    :param format: The format to convert the VTP files to.
    """
    # Get a list of all VTP files in the input folder
    vtp_files = glob.glob(os.path.join(input_folder, '*.vtp'))

    # Use multiprocessing to convert the VTP files to the specified format in parallel
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    for vtp_file in vtp_files:
        pool.apply_async(convert_vtp_to_other_formats_worker, args=(vtp_file, output_folder, format))
    pool.close()
    pool.join()


def export_simplified_saddle_graph_ui(parent_widget):
    '''
    this function creates the UI for the export simplified 2saddle-maxima graph

    :param parent_widget: the parent widget
    :return: the frame containing the UI
    '''
    # Create the Qt Frame to hold the UI
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    frame.setFrameShadow(QtWidgets.QFrame.Sunken)

    label_0 = QtWidgets.QLabel("Data Folder:")
    parent_widget.data_folder = QtWidgets.QLineEdit()
    browse_button_0 = QtWidgets.QPushButton("Browse")
    # browse_button_0.clicked.connect(parent_widget.show_folder_picker)
    # connect function using lambda
    browse_button_0.clicked.connect(lambda: parent_widget.show_folder_picker(parent_widget.data_folder))

    # Create the Form Elements
    # choose folder to export correctly segmented particles
    label_1 = QtWidgets.QLabel("Correctly Segmented Particles Folder:")
    parent_widget.corr_seg_folder = QtWidgets.QLineEdit()
    browse_button_1 = QtWidgets.QPushButton("Browse")
    # browse_button_1.clicked.connect(parent_widget.show_folder_picker)
    # connect function using lambda
    browse_button_1.clicked.connect(lambda: parent_widget.show_folder_picker(parent_widget.corr_seg_folder))

    # choose folder to export incorrectly segmented particles
    label_2 = QtWidgets.QLabel("Incorrectly Segmented Particles Folder:")
    parent_widget.incorr_seg_folder = QtWidgets.QLineEdit()
    browse_button_2 = QtWidgets.QPushButton("Browse")
    # browse_button_2.clicked.connect(parent_widget.show_folder_picker)
    # connect function using lambda
    browse_button_2.clicked.connect(lambda: parent_widget.show_folder_picker(parent_widget.incorr_seg_folder))

    # choose pickle file to export saddle graph
    label_3 = QtWidgets.QLabel("Choose pickle file containing manual classification of particles :")
    parent_widget.pickle_file = QtWidgets.QLineEdit()
    browse_button_3 = QtWidgets.QPushButton("Browse")
    # browse_button_3.clicked.connect(parent_widget.show_file_picker)
    # connect function using lambda
    browse_button_3.clicked.connect(lambda: parent_widget.show_file_picker(parent_widget.pickle_file))

    # convert button
    parent_widget.export_button = QtWidgets.QPushButton("Export")
    parent_widget.export_button.clicked.connect(parent_widget.onSaddleGraphExportClicked)

    # Create the Layout
    layout = QtWidgets.QGridLayout()
    r = 0
    layout.addWidget(label_0, r, 0)

    r += 1
    layout.addWidget(parent_widget.data_folder, r, 0)
    layout.addWidget(browse_button_0, r, 1)

    r += 1
    layout.addWidget(label_1, r, 0)

    r += 1
    layout.addWidget(parent_widget.corr_seg_folder, r, 0)
    layout.addWidget(browse_button_1, r, 1)

    r += 1
    layout.addWidget(label_2, r, 0)

    r += 1
    layout.addWidget(parent_widget.incorr_seg_folder, r, 0)
    layout.addWidget(browse_button_2, r, 1)

    r += 1
    layout.addWidget(label_3, r, 0)

    r += 1
    layout.addWidget(parent_widget.pickle_file, r, 0)
    layout.addWidget(browse_button_3, r, 1)

    r += 1
    layout.addWidget(parent_widget.export_button, r, 0, alignment=QtCore.Qt.AlignCenter)

    # Set the Layout
    frame.setLayout(layout)

    return frame


def get_hor_bar(x, y, width, height):
    """
    This function creates a horizontal bar with two colors.

    :param x: The x value.
    :param y: The y value.
    :param width: The width of the bar.
    :param height: The height of the bar.
    :return: The horizontal bar as a QPixmap.
    """
    # Calculate the percentage of x and y
    total = x + y
    x_percentage = x / total
    y_percentage = y / total

    # Create a QPixmap to draw the horizontal bar
    pixmap = QPixmap(width, height)
    pixmap.fill(QtCore.Qt.transparent)

    # Create a QPainter to draw on the QPixmap
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Draw the green bar for x
    x_width = int(x_percentage * width)
    x_color = QColor(QtCore.Qt.green)
    painter.fillRect(0, 0, x_width, height, x_color)

    # Draw the red bar for y
    y_width = int(y_percentage * width)
    y_color = QColor(QtCore.Qt.red)
    painter.fillRect(x_width, 0, y_width, height, y_color)

    # End painting
    painter.end()

    return pixmap


def get_label(x, y):
    """
    This function creates a QLabel to display the x and y values.

    :param x: The x value.
    :param y: The y value.
    :return: The QLabel.
    """
    label = QLabel()
    label.setText(f"<span style='color: green;'># of water tight meshes - {x}</span><br>"
                  f"<span style='color: red;'># of non water tight meshes - {y}</span>")

    # Set font properties
    font = QFont()
    font.setPointSize(12)
    label.setFont(font)

    return label


def water_tight_mesh_ui(parent_widget):
    '''
    this function creates the UI for the water tight mesh tool

    :param parent_widget: the parent widget
    :return: the frame
    '''
        # Create the Qt Frame to hold the UI
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    frame.setFrameShadow(QtWidgets.QFrame.Sunken)

    # Create the Form Elements
    # choose input folder containing vtp files
    input_label = QtWidgets.QLabel("Input Folder:")
    parent_widget.input_line_edit = QtWidgets.QLineEdit()
    input_browse_button = QtWidgets.QPushButton("Browse")
    input_browse_button.clicked.connect(lambda: parent_widget.show_folder_picker())

    # convert button
    parent_widget.convert_button = QtWidgets.QPushButton("Check Water Tightness")
    parent_widget.convert_button.clicked.connect(parent_widget.onWaterTightCompute)
    # size of the button
    parent_widget.convert_button.setFixedSize(200, 30)

    # repair mesh button
    parent_widget.repair_mesh_button = QtWidgets.QPushButton("Repair Mesh")
    parent_widget.repair_mesh_button.clicked.connect(parent_widget.onRepairMeshClicked)
    # size of the button
    parent_widget.repair_mesh_button.setFixedSize(200, 30)
    # disable the button
    parent_widget.repair_mesh_button.setEnabled(False)

    # progress bar
    parent_widget.progress_bar = QtWidgets.QProgressBar()
    parent_widget.progress_bar.setGeometry(50, 50, 200, 30)

    # Create a QLabel to display the horizontal bar
    parent_widget.hr = QLabel()
    parent_widget.hr.setGeometry(50, 50, 200, 30)

    # Create a QLabel to display the x and y values
    parent_widget.hr_label = get_label(0, 0)

    # Create the Layout
    layout = QtWidgets.QGridLayout()
    r = 0
    layout.addWidget(input_label, r, 0)

    r += 1
    layout.addWidget(parent_widget.input_line_edit, r, 0)
    layout.addWidget(input_browse_button, r, 1)

    r += 1
    layout.addWidget(parent_widget.convert_button, r, 0, alignment=QtCore.Qt.AlignCenter)

    r += 1
    layout.addWidget(parent_widget.repair_mesh_button, r, 0, alignment=QtCore.Qt.AlignCenter)

    r += 1
    layout.addWidget(parent_widget.progress_bar, r, 0, alignment=QtCore.Qt.AlignCenter)

    r += 1
    layout.addWidget(parent_widget.hr, r, 0, alignment=QtCore.Qt.AlignCenter)

    r += 1
    layout.addWidget(parent_widget.hr_label, r, 0, alignment=QtCore.Qt.AlignCenter)

    # Set the Layout
    frame.setLayout(layout)

    return frame


def convert_file_form(parent_ref):
    """
    this function creates the form for the convert file tool
    
    @param parent_ref: the parent widget
    @return: the form
    """
    f = form_nav.Form("Convert File")
    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    vl.addWidget(create_convert_mat_to_mhd_ui(parent_ref))

    f.form_widget.setLayout(vl)

    return f


def extract_pc_form(parent_ref):
    """
    this function creates the form for the extract particle point cloud tool

    @param parent_ref: the parent widget
    @return: the form
    """
    f = form_nav.Form("Extract Point Cloud")    
    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    vl.addWidget(create_extract_particle_pc_ui(parent_ref))

    f.form_widget.setLayout(vl)

    return f


def crop_image_form(parent_ref):
    """
    this function creates the form for the crop image tool

    @param parent_ref: the parent widget
    @return: the form
    """
    f = form_nav.Form("Crop Image")
    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    vl.addWidget(crop_image_ui(parent_ref))

    f.form_widget.setLayout(vl)

    return f


def convert_vtp_to_others_form(parent_ref):
    """
    this function creates the form for the convert vtp to other formats tool

    @param parent_ref: the parent widget
    @return: the form
    """
    f = form_nav.Form("Convert VTP to Other Formats")   
    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    vl.addWidget(convert_vtp_to_other_formats_ui(parent_ref))

    f.form_widget.setLayout(vl)

    return f


def export_simplified_saddle_graph_form(parent_ref):
    """
    this function creates the form for the export simplified 2saddle-maxima graph tool

    @param parent_ref: the parent widget
    @return: the form
    """
    f = form_nav.Form("Export Simplified Saddle Graph") 
    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    vl.addWidget(export_simplified_saddle_graph_ui(parent_ref))

    f.form_widget.setLayout(vl)

    return f


def water_tight_form(parent_ref):
    """
    this function creates the form for the water tight mesh tool

    @param parent_ref: the parent widget
    @return: the form
    """
    f = form_nav.Form("Water Tight Mesh")
    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    vl.addWidget(water_tight_mesh_ui(parent_ref))

    f.form_widget.setLayout(vl)

    return f


class WaterTightTaskType(Enum):
    '''
    this class represents the water tight task type
    '''
    CHECK = 0
    REPAIR = 1


class WaterTightTask:
    '''
    this class represents a water tight task
    contains the task type and the input file
    '''

    def __init__(self, task_type, input_file):
        """
        this function initializes the class

        @param task_type: the task type
        @param input_file: the input file
        """
        self.task_type = task_type
        self.input_file = input_file


class MiscTools(form_nav.Form_Nav):
    '''
    this class represents the miscellaneous tools 
    related to the file conversion (vtp to stl, ...),
    and extracting point cloud and so on
    '''

    def __init__(self, parent=None):
        """
        this function initializes the class

        @param parent: the parent widget
        """
        super().__init__("Miscellaneous Tools", parent)

        # ref to parent
        self.parent_ref = parent

        self.add_form(convert_file_form(self))
        self.add_form(extract_pc_form(self))
        self.add_form(crop_image_form(self))
        self.add_form(convert_vtp_to_others_form(self))
        self.add_form(export_simplified_saddle_graph_form(self))
        self.add_form(water_tight_form(self))

        self.num_of_water_tight = 0
        self.num_of_non_water_tight = 0
        self.non_water_tight_files = []


    def updateUI(self, text:str):
        '''
        update the ui (progress bar)

        @param text: the text to update
        '''
        # throw implementation error
        if not ("repair" in text):
            text = text.split("|")
            if text[0] == "wt":
                self.num_of_water_tight += 1
            elif text[0] == "nwt":
                self.num_of_non_water_tight += 1
                self.non_water_tight_files.append(text[1])

            # update the progress bar
            prog = (self.num_of_water_tight + self.num_of_non_water_tight)/len(self.files)*100
            self.progress_bar.setValue(prog)

            if prog == 100:
                # update the label
                # Set the horizontal bar pixmap based on x and y values
                self.hr.setPixmap(get_hor_bar(self.num_of_water_tight, self.num_of_non_water_tight, 200, 30))
                self.hr.setScaledContents(True)

                # set the new label
                self.hr_label.setText(get_label(self.num_of_water_tight, self.num_of_non_water_tight).text())
                
                # enable the button
                self.repair_mesh_button.setEnabled(True)
            
        elif "repair" in text:
            # update the progress bar
            self.repair_count = self.repair_count + 1
            prog = self.repair_count/len(self.non_water_tight_files)*100
            self.progress_bar.setValue(prog)

    def show_file_picker(self, line_edit=None):
        '''
        this function shows the file picker dialog

        @param line_edit: the line edit to update
        '''
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        # choose an existing file
        self.input_filepath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose a file", "",
                                "All Files (*);;", options=options)
        # update the text of the input line edit
        if line_edit != None:
            line_edit.setText(self.input_filepath)
        else:
            self.input_line_edit.setText(self.input_filepath)
        print("input_filepath: " + self.input_filepath)

    def save_file_picker(self, line_edit=None):
        '''
        this function shows the file picker dialog

        @param line_edit: the line edit to update
        '''
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        # choose a file to save to
        self.output_filepath, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Choose a file", "",
                                "All Files (*);;", options=options)
        # update the text of the output line edit
        if line_edit != None:
            line_edit.setText(self.output_filepath)
        else:
            self.output_line_edit.setText(self.output_filepath)
        print("output_filepath: " + self.output_filepath)

    def onConvertButtonClicked(self):
        '''
        this function converts the mat file to mhd file
        '''
        try:
            data_shape = convert_file(self.input_filepath, 
                        self.output_filepath, self.input_array_name_line_edit.text(), 
                        self.transpose_checkbox.isChecked())
            QtWidgets.QMessageBox.information(self, "Success", "File converted successfully!" +
                                              "\nData shape: " + str(data_shape))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def onExtractPCClicked(self):
        '''
        this function extracts point cloud and save
        it in a file(e.g : 67389.vtp)
        '''
        particle_id = int(self.pc_input_line_edit.text())
        input_data = utils.read_file(settings.Config.SEGMENTATION_FILE)
        point_cloud = utils.get_grain_polydata(input_data, particle_id)

        # Write the file
        fileutil.save(point_cloud, self.pc_output_line_edit.text())

        QtWidgets.QMessageBox.information(self, "Success", "Point cloud extracted successfully!")

    def onCropClicked(self):
        '''
        this function crops the image and save it in a file
        '''
        # get the input file path
        input_file = self.input_line_edit.text()
        # get the output file path
        output_file = self.output_line_edit.text()
        # get the crop size
        crop_size = [int(i) for i in self.crop_size_line_edit.text().split(",")]

        crop_image(input_file, output_file, crop_size)

        QtWidgets.QMessageBox.information(self, "Success", "Image cropped successfully!")

    def onLoadClicked(self):
        '''
        this function loads the image and display it
        '''
        # get the input file path
        inp_size = get_image_size(self.input_line_edit.text())
        self.input_image_label.setText("Input Image Size: " + str(inp_size)) 

    def show_folder_picker(self, line_edit = None):
        '''
        this function shows the folder picker dialog

        @param line_edit: the line edit to update
        '''
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        # choose an existing folder
        self.input_filepath = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose a folder", "",
                                options=options)
        # update the text of the input line edit
        if line_edit == None:
            self.input_line_edit.setText(self.input_filepath)
        else:
            line_edit.setText(self.input_filepath)
        print("input_filepath: " + self.input_filepath)

    def save_folder_picker(self):
        '''
        this function shows the folder picker dialog
        '''
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        # choose a folder to save to
        self.output_filepath = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose a folder", "",
                                options=options)
        # update the text of the output line edit
        self.output_line_edit.setText(self.output_filepath)
        print("output_filepath: " + self.output_filepath)

    def onConvertClicked(self):
        '''
        this function converts vtp file to other formats
        '''
        # get the input file path
        input_folder = self.input_line_edit_cf.text()
        # get the output file path
        output_folder = self.output_line_edit.text()
        # get the output format
        output_format = self.format_combo_box.currentText()

        convert_vtp_to_other_formats(input_folder, output_folder, output_format)

        QtWidgets.QMessageBox.information(self, "Success", "File converted successfully!")

    def onSaddleGraphExportClicked(self):
        '''
        this function exports the simplified saddle graph
        to the desired folders
        '''
        print("onSaddleGraphExportClicked", 
              self.data_folder.text(), 
              self.corr_seg_folder.text(), 
              self.incorr_seg_folder.text(),
              self.pickle_file.text())
        # read the pickle file
        with open(self.pickle_file.text(), 'rb') as f:
            data = pickle.load(f)

        list_incorr = []
        list_corr = []

        for k, v in data.items():
            if v == Label.INCORRECT_SEGMENTATION:
                list_incorr.append(k)
            elif v == Label.CORRECT_SEGMENTATION:
                list_corr.append(k)

        print("Number of incorrect segmentations: ", len(list_incorr))
        print("Number of correct segmentations: ", len(list_corr))

        for particle_id in tqdm(list_incorr):
            filename = str(particle_id) + ".vtp"
            utils.copyfile(filename, self.data_folder.text(), self.incorr_seg_folder.text())

        for particle_id in tqdm(list_corr):
            filename = str(particle_id) + ".vtp"
            utils.copyfile(filename, self.data_folder.text(), self.corr_seg_folder.text())

        QtWidgets.QMessageBox.information(self, "Success", "Saddle graph exported successfully!")

    def onRepairMeshClicked(self):
        '''
        this function repairs the non water tight meshes
        and make them water tight
        '''
        print("onRepairMeshClicked", self.non_water_tight_files)
    
        self.repair_count = 0

        for file in self.non_water_tight_files:
            self.queue.put(WaterTightTask(WaterTightTaskType.REPAIR, file))

    def onWaterTightCompute(self):
        '''
        This function computes number of water tight particles
        '''
        # get the input folder
        input_folder = self.input_line_edit.text()

        self.files = os.listdir(input_folder)

        self.non_water_tight_files = []

        self.proc_pool = multiproc.MultiProc(self.child_conn, self.queue)

        # start the processes
        for p in range(self.proc_pool.get_num_procs()):
            self.proc_pool.add_task(multiproc.water_tight_task)

        # reading all the files in the folder
        for i, file in enumerate(self.files):
            if file.endswith(".vtp") or file.endswith(".stl"):
                self.queue.put(WaterTightTask(WaterTightTaskType.CHECK, input_folder + "/" + file))


def main(parent=None):
    '''
    Opens miscellanous tools dialog
    
    :param parent: the parent widget
    '''
    dialog = MiscTools(parent)
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()



