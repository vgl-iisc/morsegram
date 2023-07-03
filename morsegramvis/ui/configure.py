from PySide6 import QtCore, QtWidgets
from settings import Config
import core.xmlutils as xmlutils
import os


def get_HLine():
    '''
    get a horizontal line

    @return: the horizontal line
    '''
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.HLine)
    frame.setFrameShadow(QtWidgets.QFrame.Sunken)
    return frame


def selectFolder():
    '''
    Open a file dialog to select a folder
    @return: the selected folder
    '''
    # Open a file dialog to select a folder
    folder = QtWidgets.QFileDialog.getExistingDirectory()
    return folder


def get_form(parent=None):
    '''
    get the form

    @param parent: the parent widget
    @return: the form
    '''
    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout()
    label = QtWidgets.QLabel("Select a folder")
    # Create the button and line edit
    button = QtWidgets.QPushButton("Select Folder")
    parent.lineEdit = QtWidgets.QLineEdit()

    # connect lineEdit to button click
    button.clicked.connect(lambda: parent.lineEdit.setText(selectFolder()))

    # Set the alignment of the text in the line edit to center
    parent.lineEdit.setAlignment(QtCore.Qt.AlignCenter)

    # add the button and line edit to the layout
    folder_layout = QtWidgets.QHBoxLayout()
    folder_layout.addWidget(label)
    folder_layout.addWidget(parent.lineEdit)
    folder_layout.addWidget(button)

    layout.addLayout(folder_layout)

    # add seperator as horizontal line
    
    layout.addWidget(get_HLine())

    # add rgb sliders
    # vertical layout
    rgb_layout = QtWidgets.QVBoxLayout()
    parent.rgb = {'red' : None, 'green' : None, 'blue' : None}
    for c in parent.rgb.keys():
        # horizontal layout
        h_layout = QtWidgets.QHBoxLayout()
        # label
        c_label = QtWidgets.QLabel(c)
        # size
        c_label.setFixedSize(50, 20)
        h_layout.addWidget(c_label)
        # slider
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 255)
        # label / numerical value corresponding to slider
        slider_label = QtWidgets.QLabel("0")
        slider_label.setFixedSize(50, 20)
        # connect slider to label and add to dict
        slider.valueChanged.connect(lambda value, label=slider_label: label.setText(str(value)))
        h_layout.addWidget(slider)
        h_layout.addWidget(slider_label)
        # add to vertical layout
        rgb_layout.addLayout(h_layout)
        parent.rgb[c] = slider

    layout.addLayout(rgb_layout)
    layout.addWidget(get_HLine())

    # lighting sliders - ambient(0, 1), diffuse(0, 1), 
    # specular(0, 1), specular power(0, 100)
    lighting_dict = {   'ambient': [0, 100], 
                        'diffuse': [0, 100],
                        'specular': [0, 100],
                        'specular power': [0, 100]}
    # vertical layout
    lighting_layout = QtWidgets.QVBoxLayout()
    
    parent.lighting = {k : None for k in lighting_dict.keys()}

    for k, v in lighting_dict.items():
        # horizontal layout
        h_layout = QtWidgets.QHBoxLayout()
        # label
        c_label = QtWidgets.QLabel(k)
        # size
        c_label.setFixedSize(120, 20)
        h_layout.addWidget(c_label)
        # slider
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(v[0], v[1])

        label_text = ""
        if k == 'ambient':
            slider.setValue(50)
            label_text = "50"
        elif k == 'diffuse':
            slider.setValue(50)
            label_text = "50"
        elif k == 'specular':
            slider.setValue(100)
            label_text = "100"
        elif k == 'specular power':
            slider.setValue(100)
            label_text = "100"
        # label / numerical value corresponding to slider
        slider_label = QtWidgets.QLabel(label_text)
        slider_label.setFixedSize(50, 20)
        # connect slider to label
        slider.valueChanged.connect(lambda value, label=slider_label: label.setText(str(value)))
        h_layout.addWidget(slider)
        h_layout.addWidget(slider_label)
        # add to vertical layout
        lighting_layout.addLayout(h_layout)
        parent.lighting[k] = slider

    layout.addLayout(lighting_layout)
    layout.addWidget(get_HLine())

    # ambient occlusion factor and kernel size input text
    ao_dict = {'ambient occlusion factor' : 0, 'kernel size' : 128}
    # vertical layout
    ao_layout = QtWidgets.QVBoxLayout()
    parent.ao = {k : None for k in ao_dict.keys()}
    for k, v in ao_dict.items():
        # horizontal layout
        h_layout = QtWidgets.QHBoxLayout()
        # label
        c_label = QtWidgets.QLabel(k)
        # size
        c_label.setFixedSize(200, 20)
        h_layout.addWidget(c_label)
        # input text
        input_text = QtWidgets.QLineEdit()
        input_text.setFixedSize(50, 20)
        input_text.setText(str(v))
        h_layout.addWidget(input_text)
        # add to vertical layout
        ao_layout.addLayout(h_layout)
        parent.ao[k] = input_text

    # TODO : wide and dark theme for query engine

    layout.addLayout(ao_layout)
    layout.addWidget(get_HLine())

    window.setLayout(layout)
    return window


def get_proj_card(data, parent):
    '''
    Card that contains the project name and the load button

    @param data: the project data
    @type data: dict
    @param parent: the parent widget
    @type parent: QtWidgets.QWidget
    @return: the card
    '''
    # create card
    card = QtWidgets.QFrame()
    card.setFrameShape(QtWidgets.QFrame.StyledPanel)
    # create layout
    layout = QtWidgets.QHBoxLayout()
    # add stretch factor to make the layout resizable
    layout.addStretch()
    # create vertical layout
    v_layout = QtWidgets.QVBoxLayout()
    # create horizontal layout
    h_layout = QtWidgets.QHBoxLayout()
    # create label
    label = QtWidgets.QLabel(data['settings']['base_folder'])
    # set word wrap to True to allow automatic line wrapping
    label.setWordWrap(True)

    # create button
    button = QtWidgets.QPushButton("Load Project")
    button.clicked.connect(lambda: parent.load_settings(data))

    # add to layout
    h_layout.addWidget(label)

    # add to layout
    v_layout.addLayout(h_layout)
    v_layout.addWidget(button)

    # add to layout
    layout.addLayout(v_layout)

    # add stretch factor to make the layout resizable
    layout.addStretch()

    # add to card
    card.setLayout(layout)

    return card


# dialog class
class Configure(QtWidgets.QDialog):
    """
    Initialize the dataset for the first time and configure it
    for subsequent use.
    """

    def __init__(self, parent=None):
        super(Configure, self).__init__(parent)

        # window buttons
        self.setWindowFlags(QtCore.Qt.Window
                            | QtCore.Qt.WindowMinimizeButtonHint
                            | QtCore.Qt.WindowMaximizeButtonHint
                            | QtCore.Qt.WindowCloseButtonHint)

        # ref to parent
        self.parent = parent
        self.setWindowTitle("Configure Settings")

        # create layout
        self.layout = QtWidgets.QHBoxLayout()

        # add frame to layout
        self.get_existing_config_frame()

        config_form_frame = QtWidgets.QFrame()
        config_form_frame.setLayout(QtWidgets.QVBoxLayout())
        # border
        config_form_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)

        # add form to frame
        config_form_frame.layout().addWidget(get_form(self))

        # add form to layout
        self.layout.addWidget(config_form_frame)

        # stretch layout
        self.layout.setStretch(0, 2)
        self.layout.setStretch(1, 3)

        # horizontal layout
        h_layout = QtWidgets.QHBoxLayout()

        # update settings
        self.update_button = QtWidgets.QPushButton("Done")
        # add icon to button
        self.update_button.setIcon(
            QtWidgets.QApplication.style().standardIcon(
                QtWidgets.QStyle.SP_DialogApplyButton))
        self.update_button.clicked.connect(self.update_settings)
        h_layout.addWidget(self.update_button)

        # close button
        self.close_button = QtWidgets.QPushButton("Close")
        # add icon to button
        self.close_button.setIcon(
            QtWidgets.QApplication.style().standardIcon(
                QtWidgets.QStyle.SP_DialogCloseButton))
        self.close_button.clicked.connect(self.close_app)
        h_layout.addWidget(self.close_button)

        # add to form frame
        config_form_frame.layout().addLayout(h_layout)

        # set layout
        self.setLayout(self.layout)

    def update_settings(self):
        '''
        Update the settings for the dataset
        '''
        # ==== input folder check =====
        check = True
        # validate input
        if self.lineEdit.text() == "":
            check = False
        elif os.path.exists(self.lineEdit.text()) == False:
            check = False
        
        if check == False:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid input for folder")
            return
        # =============================

        # ==== check for ao ===========
        check = True
        for k, v in self.ao.items():
            try:
                int(v.text())
            except:
                check = False
                break
        
        if check == False:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid input for ambient occlusion")
            return
        # ==============================

        xmlutils.save_settings(self)
        self.close_app()

    def close_app(self):
        '''
        Close dialog window
        '''
        self.close()
        self.destroy()

    def load_settings(self, data):
        '''
        Load the settings from the given data

        @param data: the project data
        @type data: dict
        '''
        try:
            Config.set_base_folder(data)
            self.close_app()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", 
                "There was an error loading the settings: {}".format(e))
            xmlutils.remove_settings(data['settings']['base_folder'])

            # reload settings
            self.get_existing_config_frame()

    def get_existing_config_frame(self):
        '''
        this function creates a frame that contains a scroll area
        that contains a list of project cards

        @param parent: the parent widget
        @type parent: QtWidgets.QWidget
        '''

        # empty frame
        existing_config_frame = QtWidgets.QFrame()

        # add scroll area to frame
        existing_config_frame.setLayout(QtWidgets.QVBoxLayout())

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)

        # add widget to scroll area
        list_widget = QtWidgets.QWidget()
        scroll_area.setWidget(list_widget)

        list_layout = QtWidgets.QVBoxLayout()
        list_widget.setLayout(list_layout)

        for proj_setting in xmlutils.get_settings():
            list_layout.addWidget(get_proj_card(proj_setting, self))
        
        list_layout.setAlignment(QtCore.Qt.AlignCenter)
        # make list start at top
        list_layout.addStretch()

        # add scroll area to frame
        existing_config_frame.layout().addWidget(scroll_area)

        # add to layout in the first position
        if self.layout.count() > 1:
            self.layout.removeWidget(self.layout.itemAt(0).widget())
        self.layout.insertWidget(0, existing_config_frame)

        # stretch layout
        self.layout.setStretch(0, 2)
        self.layout.setStretch(1, 3)


def main(parent=None):
    '''
    Open the configure settings dialog to load the new dataset
    and configure it for subsequent use.
    '''
    dialog = Configure(parent)
    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()