from PySide6 import QtCore, QtWidgets, QtGui
from settings import Config
import os
import logging


class UnderSegmentationDialog(QtWidgets.QDialog):
    '''
    Under segmentation dialog containing the under segmented particles
    '''

    def __init__(self, parent=None):
        '''
        Initialize the dialog

        @param parent: parent widget
        '''
        super(UnderSegmentationDialog, self).__init__(parent)
        # ref to parent
        self.parent = parent
        self.setWindowTitle("Under Segmented Grains")
        # minimum size
        self.setMinimumSize(400, 400)
        # self.setStyleSheet("background-color: #f0f0f0")

        # create layout
        self.layout = QtWidgets.QVBoxLayout()


        # display file icons and names
        # present in the under segmentation folder
        self.under_segmentation_files = QtWidgets.QListWidget()
        self.under_segmentation_files.setStyleSheet("background-color: #f0f0f0")
        # self.under_segmentation_files.setFixedHeight(300)
        # self.under_segmentation_files.setFixedWidth(400)
        self.under_segmentation_files.setSpacing(10)
        self.under_segmentation_files.setFlow(QtWidgets.QListView.LeftToRight)
        self.under_segmentation_files.setWrapping(True)
        self.under_segmentation_files.setResizeMode(QtWidgets.QListView.Adjust)
        self.under_segmentation_files.setMovement(QtWidgets.QListView.Static)
        self.under_segmentation_files.setViewMode(QtWidgets.QListView.IconMode)
        self.under_segmentation_files.setUniformItemSizes(True)
        self.under_segmentation_files.setIconSize(QtCore.QSize(100, 100))

        # add items to list
        try:
            for file in os.listdir(Config.UNDER_SEGMENTATION_DIR):
                if file.endswith(".mhd"):
                    item = QtWidgets.QListWidgetItem()
                    item.setIcon(QtGui.QIcon(Config.ICONS_DIR + "rawfile.png"))
                    item.setText(file)
                    item.setWhatsThis(file)
                    # text color
                    item.setForeground(QtGui.QColor(0, 0, 0))
                    self.under_segmentation_files.addItem(item)
        except Exception as e:
            logging.getLogger().error("Error while loading under segmentation files: " + str(e))
        
        # item clicked
        self.under_segmentation_files.itemClicked.connect(self.under_segmentation_item_clicked)

        # add to layout
        self.layout.addWidget(self.under_segmentation_files)


        # close button
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.close_app)
        self.layout.addWidget(self.close_button)

        # set layout
        self.setLayout(self.layout)

    def under_segmentation_item_clicked(self, item):
        '''
        # TODO: show the under segmented particles

        When an under segmentation file is clicked

        @param item: QListWidgetItem
        '''
        # get the file name
        file_name = item.text()
        # get the full path
        file_path = os.path.join(Config.UNDER_SEGMENTATION_DIR, file_name)
        
        print(file_path, "clicked", item.text())

        # whats this
        print(item.whatsThis())

    def close_app(self):
        '''
        Close the dialog
        '''
        self.close()
        # destroy Qwidget QApplication
        self.destroy()


def main(parent=None):
    '''
    Open the under segmentation dialog
    containing the under segmented particles
    '''
    dialog = UnderSegmentationDialog(parent)
    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()