from PySide6 import QtCore, QtGui, QtWidgets
from settings import Config
import os
import sys
import ui.ensembleview as ensembleview
import ui.viewparticles as viewparticles
import ui.surface_reconstruction_ui as surface_reconstruction_ui
import ui.under_segmentation as under_segmentation
import ui.insights as insights
import ui.queryengine as queryengine
import logging
import core.utils as utils
import ui.configure as configure
import ui.misc_ui as misc_ui
import error_msgs


# Custon Widget Button with image and text
class Button(QtWidgets.QPushButton):
    '''
    Custom button with image and text

    :param text: text to be displayed on the button
    :param icon: path to the icon image
    :param on_click: function to be called on click
    :param parent: parent widget
    '''
    def __init__(self, text, icon, on_click, parent=None):
        super(Button, self).__init__(parent)
        self.setText(text)
        self.setFixedHeight(120)
        self.setFont(QtGui.QFont("Arial", 15, QtGui.QFont.Bold))
        self.setIcon(QtGui.QIcon(icon))
        self.setIconSize(QtCore.QSize(100, 100))
        self.clicked.connect(on_click)


def fix_button_width_align(layout):
    '''
    Fix the button width and align to left

    :param layout: layout to be fixed
    '''
    for i in range(layout.count()):
        layout.itemAt(i).widget().setFixedWidth(400)
        # align buttons to center
        layout.itemAt(i).widget().setStyleSheet("text-align: left;")


class Start(QtWidgets.QMainWindow):
    """
    This class is the main window of the application
    """

    def __init__(self, parent=None):
        super(Start, self).__init__(parent)

        # application font
        self.app_font = QtGui.QFont("Arial", 18, QtGui.QFont.Bold)
        self.vr = False
        self.initUI()

    def initUI(self):
        '''
        Initialise the UI
        '''
        num_cols = 4

        # grid layout
        grid = QtWidgets.QGridLayout()

        # vertical layout
        vlayout = QtWidgets.QVBoxLayout()

        # App banner label
        banner = QtWidgets.QLabel(Config.APP_BANNER)
        banner.setAlignment(QtCore.Qt.AlignCenter)
        banner.setFixedHeight(30)
        banner.setFont(self.app_font)

        # App content label
        content = QtWidgets.QLabel(Config.APP_NAME)
        content.setAlignment(QtCore.Qt.AlignCenter)
        content.setFixedHeight(100)
        content.setFont(QtGui.QFont("Arial", 50, QtGui.QFont.Bold))

        # App footer label
        footer = QtWidgets.QLabel(Config.APP_FOOTER)
        footer.setAlignment(QtCore.Qt.AlignCenter)
        footer.setFixedHeight(30)
        footer.setFont(self.app_font)

        # add widgets to vertical layout
        # vlayout.addWidget(banner)
        vlayout.addWidget(content)
        vlayout.addWidget(footer, alignment=QtCore.Qt.AlignLeft)

        hlayout = QtWidgets.QHBoxLayout()

        # add logo
        # Load logos
        logo_left = QtGui.QPixmap(Config.ICONS_DIR + 'IISc_B.png')
        logo_left = logo_left.scaled(350, 200, QtCore.Qt.KeepAspectRatio)
        logo_right = QtGui.QPixmap(Config.ICONS_DIR + 'vgl_hires.ico')
        logo_right = logo_right.scaled(150, 150, QtCore.Qt.KeepAspectRatio)


        # Create QLabel widgets for logos
        label_left = QtWidgets.QLabel()
        label_left.setPixmap(logo_left)
        label_right = QtWidgets.QLabel()
        label_right.setPixmap(logo_right)

        # Add logos on either side of the content
        hlayout.addWidget(label_left)
        hlayout.addStretch(1)
        hlayout.addLayout(vlayout)
        hlayout.addStretch(1)
        hlayout.addWidget(label_right, alignment=QtCore.Qt.AlignRight)
        hlayout.addStretch(1)


        # Add vertical layout to grid layout
        grid.addLayout(hlayout, 0, 0, 1, num_cols)

        # horizontal line
        hline = QtWidgets.QFrame()
        hline.setFrameShape(QtWidgets.QFrame.HLine)
        hline.setFrameShadow(QtWidgets.QFrame.Sunken)
        grid.addWidget(hline, 1, 0, 1, num_cols)

        # ================== Buttons Row 1 ==================

        # horizontal layout
        hlayout = QtWidgets.QHBoxLayout()
        dt_button =                 Button("     Surface Reconstruction    ", \
                                                Config.ICONS_DIR + "mesh.png", self.sr_button)
        self.ens_vis_button =       Button("     Ensemble Visualization    ", \
                                                Config.ICONS_DIR + "ensemble.png", self.ensembleview_button)
        particle_vis_button =       Button("Single/Multi \nParticle Visualization", \
                                                Config.ICONS_DIR + "viewparticle.png", self.viewgrain_button)

        # add widgets to horizontal layout
        hlayout.addWidget(dt_button)
        hlayout.addWidget(self.ens_vis_button)
        hlayout.addWidget(particle_vis_button)

        # fix width of buttons
        fix_button_width_align(hlayout)


        # Add horizontal layout to grid layout
        grid.addLayout(hlayout, 2, 0, 1, num_cols)

        # ================== Buttons Row 2 ==================

        # horizontal layout
        hlayout = QtWidgets.QHBoxLayout()
        ug_button =             Button("   Under Segmentation         ", \
                                        Config.ICONS_DIR + "incorrect.png", self.under_segmentation_action)
        config_button =         Button("        Configure  ", \
                                        Config.ICONS_DIR + "configure.png", self.configure_action)
        ins_button =            Button("        Insights / Analysis   ", \
                                        Config.ICONS_DIR + "analysis.png", self.insights_action)

        # add widgets to horizontal layout
        hlayout.addWidget(ug_button)
        hlayout.addWidget(config_button)
        hlayout.addWidget(ins_button)

        # fix width of buttons
        fix_button_width_align(hlayout)

        # Add horizontal layout to grid layout
        grid.addLayout(hlayout, 3, 0, 1, num_cols)

        # ================== Buttons Row 3 ==================

        # horizontal layout
        hlayout = QtWidgets.QHBoxLayout()
        query_button =          Button("     Query Engine           ", \
                                        Config.ICONS_DIR + "query.png", self.queryengine_button)
        vr_button =             Button("     Virtual Reality         ", \
                                        Config.ICONS_DIR + "vr.png", self.not_implemented)
        misc_button =           Button("     Miscellaneous Tools      ", \
                                        Config.ICONS_DIR + "misc.png", self.misc_tools_action)
        
        # add widgets to horizontal layout
        hlayout.addWidget(query_button)
        hlayout.addWidget(vr_button)
        hlayout.addWidget(misc_button)

        # fix width of buttons
        fix_button_width_align(hlayout)

        # Add horizontal layout to grid layout
        grid.addLayout(hlayout, 4, 0, 1, num_cols)

        # set layout
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(grid)

        # padding
        self.widget.setContentsMargins(10, 10, 10, 10)

        # show widget
        # self.widget.show()

        # set central widget
        self.setCentralWidget(self.widget)

        # show the window
        self.show()

    def not_implemented(self):
        '''
        This function is called when the user clicks on the Miscellaneous Tools button
        '''

        # TODO: add misc tools
        QtWidgets.QMessageBox.information(self, "Not Implemented", "This feature is not implemented yet")

    def enable_vr(self):
        '''
        Enables Virtual Reality mode
        '''
        self.vr = not self.vr

    def misc_tools_action(self):
        '''
        Opens the miscellaneous tools window
        '''
        misc_ui.main(self)

    def file_read_progress_handler(self, obj, event):
        QtWidgets.QApplication.processEvents()
        # multiply by 100 to get percentage and round off to 2 decimal places
        data = str(round(obj.GetProgress() * 100, 2))

        # round off to 2 decimal places and add %
        data = str(round(float(data), 2))

        # format string to show percentage
        data = data + "%"

        self.ens_vis_button.setText("Reading file " + data)

        if data == "100.0%":
            self.ens_vis_button.setText("     Ensemble Visualization    ")

    def sr_button(self):
        '''
        Opens the surface reconstruction window
        '''
        if not self.isinit():
            return
        
        surface_reconstruction_ui.main(self)

    def ensembleview_button(self):
        '''
        Displays the ensemble visualization window
        '''
        if not self.isinit():
            return
        
        # read the file and show progress
        self.load_ensemble_file()

        try:
            # show the ensemble visualization window
            ensembleview.main(self)
        except Exception as e:
            print(e)
            pass

    def load_ensemble_file(self):
        '''
        This function loads the ensemble file
        '''
        if not self.isinit():
            return
        
        # read the file and show progress
        try:
            self.ensemble = utils.read_file(Config.ENSEMBLE_FILE, self.file_read_progress_handler)
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(self, "Error", error_msgs.SR_MSG)
            return

    def viewgrain_button(self):
        '''
        Displays the single/multi particle visualization window
        '''
        if not self.isinit():
            return
        
        try:
            viewparticles.main(self)
        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(self, "Error", error_msgs.SR_MSG)

    def under_segmentation_action(self):
        '''
        Displays the under segmented particles
        '''
        if not self.isinit():
            return
        
        if not os.path.exists(Config.PARTICLES_MESH_DIR):
            QtWidgets.QMessageBox.critical(self, "Error", error_msgs.SR_MSG)
            return
        
        try:
            under_segmentation.main(self)
        except Exception as e:
            logging.getLogger().exception(e)
    
    def configure_action(self):
        '''
        Configure by choosing the input data folder
        to be used for the program
        '''
        try:
            configure.main(self)
        except Exception as e:
            print(e)

    def insights_action(self):
        '''
        overview of the data and various plots
        '''
        if not self.isinit():
            return

        try:
            insights.main(self)
        except Exception as e:
            print(e)

    def queryengine_button(self):
        '''
        Query Engine to interactively query the data
        '''
        if not self.isinit():
            return
        
        try:
            queryengine.main(self)
        except Exception as e:
            print(e)

    def isinit(self):
        '''
        This function checks if the program has been initialized.
        If not, it shows an error message and returns False.
        '''
        if not Config.isinit():
            QtWidgets.QMessageBox.critical(self, "Error", "Configure the program")
            return False

        if not os.path.exists(Config.INPUT_DIR):
            os.makedirs(Config.INPUT_DIR)
        
        if not os.path.exists(Config.CHAMFER_DIR):
            os.makedirs(Config.CHAMFER_DIR)
        
        if not os.path.exists(Config.SIMPLIFIED_DIR):
            os.makedirs(Config.SIMPLIFIED_DIR)

        return True


def main():
    # create app data for storing config and logs
    if not os.path.exists(Config.APP_DATA_DIR):
        os.makedirs(Config.APP_DATA_DIR)

    app = QtWidgets.QApplication(sys.argv)

    # logo
    app.setWindowIcon(QtGui.QIcon(Config.ICONS_DIR + "vgl_hires.ico"))

    # set app name
    app.setApplicationName(Config.APP_NAME)

    start = Start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()