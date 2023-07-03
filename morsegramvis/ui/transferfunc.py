from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget,\
    QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PySide6.QtGui import QPainter, QBrush, QPen, QPolygonF, \
    QPainterPath, QLinearGradient, QColor
from PySide6.QtCore import Qt, QPoint
import vtk
import random
from settings import Config
from ui import cmapdropdown
import os
from qtrangeslider import QRangeSlider


QSS = """
QSlider {
    min-height: 20px;
}
QSlider::groove:horizontal {
    border: 0px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #888, stop:1 #ddd);
    height: 20px;
    border-radius: 10px;
}
QSlider::handle {
    background: qradialgradient(cx:0, cy:0, radius: 1.2, fx:0.35,
                                fy:0.3, stop:0 #eef, stop:1 #002);
    height: 20px;
    width: 20px;
    border-radius: 10px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #227, stop:1 #77a);
    border-top-left-radius: 10px;
    border-bottom-left-radius: 10px;
}
QRangeSlider {
    qproperty-barColor: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #227, stop:1 #77a);
}
"""


def make_lut(table_size):
    '''
    this function creates a vtk lookup table with random colors

    @param table_size: the size of the lookup table
    @return: the lookup table
    '''
    table = vtk.vtkLookupTable()
    table.SetNumberOfTableValues(table_size)
    table.SetTableRange(0, table_size)
    table.Build()

    nc = vtk.vtkNamedColors()

    # Set the colors in the lookup table with random colors
    for i in range(table_size):
        table.SetTableValue(i, random.random(), random.random(), random.random(), 1.0)
        # print(table.GetTableValue(i))

    return table


class TransferFunctionWidget(QWidget):
    '''
    this class is used to create the transfer function widget
    '''

    def __init__(self, parent=None):
        '''
        Initialize the transfer function widget

        @param parent: the parent widget
        '''
        super(TransferFunctionWidget, self).__init__(parent)
        self.parent_widget = parent
        self.setFixedSize(parent.widget_width, parent.widget_height)
        self.points = []
        self.new_points = []
        self.selected_point = None
        # Load the vtk color map
        self.lut = make_lut(256)
        self.reset()

    def add_point(self, x, y):
        '''
        this function adds a new point in the transfer function

        @param x: the x coordinate of the point
        @param y: the y coordinate of the point
        '''
        self.new_points.append(QPoint(x, y))
        self.update()

    def paintEvent(self, event):
        '''
        Draws the lines and points in the widget

        @param event: the paint event
        '''
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(Qt.white))
        painter.drawLine(0, self.height(), self.width(), self.height())
        painter.drawLine(0, 0, 0, self.height())

        polygon = QPolygonF(self.points)
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        painter.drawPolyline(polygon)

        for point in self.points:
            painter.setPen(QPen(Qt.red, 5, Qt.SolidLine))
            painter.drawPoint(point)

        if self.selected_point:
            painter.setPen(QPen(Qt.blue, 5, Qt.SolidLine))
            painter.drawPoint(self.selected_point)

        # fill the transfer function
        self.fill_transfer_function(painter)

    def mousePressEvent(self, event):
        '''
        this function is called when the mouse is pressed in the widget

        @param event: the mouse event
        '''
        curr_pos = event.position()
        for point in self.points:
            if (curr_pos - point).manhattanLength() <= 5:
                self.selected_point = point
                break
        else:
            # add new point in the sorted order of x
            for i, point in enumerate(self.points):
                if curr_pos.x() < point.x():
                    self.points.insert(i, curr_pos)
                    self.update()
                    return
            
            self.add_point(curr_pos.x(), curr_pos.y())

    def fill_transfer_function(self, painter : QPainter):
        '''
        this function fills the transfer function with the color map

        @param painter: the painter object
        '''
        path = QPainterPath()
        path.moveTo(0, self.height())

        for point in self.points:
            path.lineTo(point)

        path.lineTo(self.width(), self.height())
        path.closeSubpath()

        # Create the gradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        num_of_colors = self.lut.GetNumberOfTableValues()
        for i in range(num_of_colors):
            color = [0, 0, 0]
            self.lut.GetColor(float(i)/num_of_colors, color)
            gradient.setColorAt(float(i)/num_of_colors, QColor(color[0]*255, color[1]*255, color[2]*255))

        painter.fillPath(path, QBrush(gradient))

    def mouseMoveEvent(self, event):
        '''
        this function is called when the mouse is moved in the widget

        @param event: the mouse event
        '''
        if self.selected_point:
            curr_pos = event.position()
            # make sure the point between next and previous point
            if self.selected_point != self.points[0]:
                prev_point = self.points[self.points.index(self.selected_point) - 1]
                if curr_pos.x() < prev_point.x():
                    curr_pos.setX(prev_point.x())
            if self.selected_point != self.points[-1]:
                next_point = self.points[self.points.index(self.selected_point) + 1]
                if curr_pos.x() > next_point.x():
                    curr_pos.setX(next_point.x())

            # check if the point is in the widget
            if curr_pos.x() < 0:
                curr_pos.setX(0)
            if curr_pos.x() > self.width():
                curr_pos.setX(self.width())
            
            if curr_pos.y() < 0:
                curr_pos.setY(0)
            if curr_pos.y() > self.height():
                curr_pos.setY(self.height())

            self.selected_point.setX(curr_pos.x())
            self.selected_point.setY(curr_pos.y())
            self.update()
            self.parent_widget.update()

    def update_cmap(self, cmap):
        '''
        this function updates the color map

        @param cmap: the color map
        '''
        self.lut = cmap
        self.update()
        self.parent_widget.update()

    def set_control_points(self, range_value):
        '''
        this function sets the control points

        @param range_value: the range of the control points
        '''
        d = 0.01
        x1 = self.width() * range_value[0] / 100
        if x1 > d:
            x2 = self.width() * range_value[1] / 100
            y1 = self.height() / 2
            y2 = self.height() / 2
            self.points = [ QPoint(0, self.height()),
                            QPoint(x1-d, self.height()),
                            QPoint(x1, y1),
                            QPoint(x2, y2),
                            QPoint(x2+d, self.height()),
                            QPoint(self.width(), self.height())]
            for pt in self.new_points:
                # add new point in the sorted order of x
                for i, point in enumerate(self.points):
                    if pt.x() < point.x():
                        self.points.insert(i, pt)
                        break
            self.update()

    def get_color(self, x):
        '''
        this function returns the color at the given x coordinate

        @param x: the x coordinate
        @return: the color at the given x coordinate
        '''
        color = [0, 0, 0]
        self.lut.GetColor(float(x)/self.size().width(), color)
        return (color[0], color[1], color[2])

    def reset(self):
        '''
        this function resets the transfer function
        '''
        self.new_points = []
        self.points = [ 
                        QPoint(0, self.parent_widget.widget_height),
                        QPoint(self.parent_widget.widget_width, 0)]
        self.update()


class RangeSlider(QWidget):
    '''
    this class is used to create the range slider widget
    '''

    def __init__(self, parent=None, cb=None):
        '''
        Initialize the range slider widget

        @param parent: the parent widget
        @param cb: the callback function
        '''
        super(RangeSlider, self).__init__(parent)
        self.parent_widget : TransferFunctionWithColorMap = parent
        if os.name == 'nt':
            # windows
            self.styled_range_hslider = QRangeSlider()
        else:
            # linux
            self.styled_range_hslider = QRangeSlider(Qt.Horizontal)
        self.styled_range_hslider.setFixedWidth(self.parent_widget.widget_width)
        self.styled_range_hslider.setRange(0, 100)
        self.styled_range_hslider.setValue((0, 100))
        self.styled_range_hslider.setStyleSheet(QSS)
        self.slider_cb = cb

        # create labels
        self.label_left = QLabel("0", self)
        self.label_right = QLabel("100", self)
        self.label_min = QLabel("Min: 0", self)
        self.label_max = QLabel("Max: 0", self)

        # create layout
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.label_left)
        hbox1.addStretch(1)
        hbox1.addWidget(self.label_right)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.label_min)
        hbox2.addStretch(1)
        hbox2.addWidget(self.label_max)

        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox1)
        vbox.addWidget(self.styled_range_hslider)
        vbox.addLayout(hbox2)

        # on slider value change
        self.styled_range_hslider.valueChanged.connect(self.on_slider_value_change)

        self.layout = vbox

    def on_slider_value_change(self, range_value):
        '''
        this function is called when the slider value is changed

        @param range_value: the range value
        '''
        range_value = self.styled_range_hslider.value()
        if self.slider_cb is not None:
            lv, rv = self.slider_cb(range_value)
            self.label_left.setText(str(lv))
            self.label_right.setText(str(rv))

    def reset(self):
        '''
        this function resets the range slider
        '''
        self.styled_range_hslider.setValue((0, 100))
        self.label_left.setText("0")
        self.label_right.setText("100")

    def label_minmax(self, a, b):
        '''
        this function sets the min and max label

        @param a: the min value
        @param b: the max value
        '''
        self.label_min.setText("Min: " + str(int(a)))
        self.label_max.setText("Max: " + str(int(b)))


class ControlPoint():
    '''
    this class is used to create a control point
    '''

    def __init__(self, x, opacity, color):
        '''
        Initialize the control point

        @param x: the x coordinate
        @param opacity: the opacity
        @param color: the color
        '''
        self.x = x
        self.opacity = opacity
        self.color = color


def get_frame(widgets, layout):
    '''
    this function returns a frame with the given widgets

    @param widgets: the widgets to add in the frame
    @param layout: the layout of the frame
    @return: the frame
    '''
    frame = QtWidgets.QFrame()
    frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
    frame.setFrameShadow(QtWidgets.QFrame.Raised)
    frame.setLineWidth(1)
    frame.setMidLineWidth(1)

    frame_layout = layout(frame)
    for widget in widgets:
        frame_layout.addWidget(widget, alignment=Qt.AlignCenter)
        
    # frame.setFixedHeight(height)
    return frame


class TransferFunctionWithColorMap(QWidget):
    '''
    this class is used to create the transfer function with color map widget
    '''

    def __init__(self, parent=None):
        '''
        Initialize the transfer function with color map widget

        @param parent: the parent widget
        '''
        super(TransferFunctionWithColorMap, self).__init__(parent)
        self.parent_widget = parent
        self.widget_width = parent.width() / 2
        self.widget_height = parent.width() / 2

        self.layout = QVBoxLayout(self)
        self.transfer_function_widget = TransferFunctionWidget(self)
        self.transfer_function_widget.add_point(0, self.widget_height)
        self.transfer_function_widget.add_point(self.widget_width, 0)
        # self.layout.addWidget(self.transfer_function_widget, alignment=Qt.AlignCenter)
        
        colormaps = []
        for i in os.listdir(Config.COLORMAPS_DIR):
            if i.endswith(".png"):
                filename = i.split(".")[0]
                colormaps.append(cmapdropdown.ColorMap(filename, 
                                        os.path.join(Config.COLORMAPS_DIR, filename + ".xml"), 
                                        os.path.join(Config.COLORMAPS_DIR, i)))

        self.color_map_widget = cmapdropdown.ColormapChooserWidget(colormaps,
                                                self.widget_width,
                                                self.transfer_function_widget)
        # self.layout.addWidget(self.color_map_widget, alignment=Qt.AlignCenter)

        # frame to add transfer function and color map
        # self.layout.addWidget(get_frame([self.transfer_function_widget, self.color_map_widget],
        #                                 QtWidgets.QHBoxLayout))
        
        

        self.reset_button = QPushButton("Reset Transfer Function")
        self.reset_button.setFixedWidth(200)
        self.reset_button.clicked.connect(self.reset)
        # self.layout.addWidget(self.reset_button, alignment=Qt.AlignCenter)

        self.styled_range_hslider = RangeSlider(self)
        self.styled_range_hslider.label_minmax(self.get_parent_window().scalar_range[0],
                                                self.get_parent_window().scalar_range[1])
        frame1 = get_frame([self.transfer_function_widget,
                            self.styled_range_hslider], QtWidgets.QVBoxLayout)
        frame2 = get_frame([self.color_map_widget, self.reset_button], QtWidgets.QVBoxLayout)
        self.layout.addWidget(get_frame([frame1, frame2], QtWidgets.QHBoxLayout))

    def reset(self):
        '''
        this function resets the transfer function with color map widget
        '''
        self.transfer_function_widget.reset()
        self.styled_range_hslider.reset()

    def update(self):
        '''
        this function updates the transfer function with color map widget
        '''
        ctrl_points = []
        for i in range(len(self.transfer_function_widget.points)):
            ctrl_points.append(ControlPoint(float(self.transfer_function_widget.points[i].x()) / self.widget_width, 
                        float(self.widget_height - self.transfer_function_widget.points[i].y()) / self.widget_height,
            self.transfer_function_widget.get_color(self.transfer_function_widget.points[i].x())))
        # print(ctrl_points)
        self.get_parent_window().update_range(ctrl_points)

    def get_selected_range(self, range_value):
        '''
        this function returns the selected range

        @param range_value: the range value
        @return: the selected range
        '''
        lv = range_value[0] * (self.get_parent_window().scalar_range[1] - 
                         self.get_parent_window().scalar_range[0]) / 100
        rv = range_value[1] * (self.get_parent_window().scalar_range[1] - 
                         self.get_parent_window().scalar_range[0]) / 100
        self.transfer_function_widget.set_control_points(range_value)
        self.update()
        return int(lv), int(rv)

    def get_parent_window(self):
        '''
        returns the parent window of the widget
        e.g : single particle view or ensemble view
        '''
        return self.parent_widget.parent_widget
    


