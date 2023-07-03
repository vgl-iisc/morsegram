from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QComboBox, QVBoxLayout, QWidget
import xml.etree.ElementTree as ET
import vtk


class ColormapChooserWidget(QWidget):
    """
    Widget for choosing a colormap
    """

    def __init__(self, colormaps, width, parent=None):
        super().__init__()
        self.parent_widget = parent

        self.colormaps = colormaps
        self.color_width = int(width)
        # Create the UI components
        self.colormap_label = QLabel()
        self.colormap_label.setFixedSize(self.color_width, 50)
        self.colormap_dropdown = QComboBox()
        for cmap in colormaps:
            self.colormap_dropdown.addItem(cmap.name)
        self.colormap_dropdown.currentIndexChanged.connect(self.on_colormap_changed)

        # Set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.colormap_label)
        layout.addWidget(self.colormap_dropdown)
        self.setLayout(layout)

        # Set the default colormap
        self.set_colormap(0)

    def set_colormap(self, cmap_index):
        '''
        Set the colormap to the given index
        @param cmap_index: The index of the colormap to set
        '''
        # Load the colormap preview image
        cmap = self.colormaps[cmap_index]
        pixmap = QPixmap(cmap.preview_loc)
        # resize the image to fit the label size and change the aspect ratio
        pixmap = pixmap.scaled(self.colormap_label.size())
        self.colormap_label.setPixmap(pixmap)
        self.parent_widget.update_cmap(self.get_colormap())

    def on_colormap_changed(self, index):
        '''
        Called when the colormap is changed
        @param index: The index of the new colormap
        '''
        self.set_colormap(index)
        self.parent_widget.update_cmap(self.get_colormap())

    def get_colormap(self):
        '''
        Get the colormap from the current index
        @return: The colormap
        '''
        tree = ET.parse(self.colormaps[self.colormap_dropdown.currentIndex()].file_loc)
        root = tree.getroot()
        
        root = root.find("ColorMap")

        ctf = vtk.vtkColorTransferFunction()
        ctf.SetColorSpaceToDiverging()

        # Get the points
        for point in root.findall("Point"):
            ctf.AddRGBPoint(float(point.attrib["x"]), 
                            float(point.attrib["r"]), 
                            float(point.attrib["g"]), 
                            float(point.attrib["b"]))
        
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(self.color_width)
        lut.Build()

        for i in range(self.color_width):
            rgb = list(ctf.GetColor(float(i)/self.color_width)) + [1]
            lut.SetTableValue(i, rgb)

        return lut


class ColorMap():
    """
    Color map with name, file location, and preview location
    """
    def __init__(self, name, file_loc, preview_loc):
        self.name = name
        self.file_loc = file_loc
        self.preview_loc = preview_loc


