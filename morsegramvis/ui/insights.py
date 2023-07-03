from PySide6 import QtCore, QtWidgets, QtGui, QtCharts
from settings import Config
from ui import clusters_ui, form_nav
import numpy as np
import pandas as pd
from core import ensembleinfo
import os


def overview_form() -> form_nav.Form:
    """
    Overview form contains the information about the ensemble
    like name, dimension, number of particles, etc.

    @return: The form
    """
    f = form_nav.Form("Overview")
    f.form_widget = QtWidgets.QWidget()
    
    vl = QtWidgets.QVBoxLayout()
    vl.addWidget(get_overview_widget())

    f.form_widget.setLayout(vl)

    return f


def get_series_cdf(data, normalize=False):
    '''
    Returns a series of the cummulative distribution function of the data

    @param data: The data
    @param normalize: Normalize the commulative count
    @return: The series
    '''
    data = np.sort(data)
    unique_data = np.unique(data)
    data = np.array([np.sum(data <= value) for value in data])

    if normalize:
        data = data / len(data)

    series = QtCharts.QLineSeries()
    for i in range(len(unique_data)):
        series.append(unique_data[i], data[i])

    return series


def save_chart(chart_view: QtCharts.QChartView):
    '''
    Save the chart as an image

    @param chart_view: The chart view
    '''
    file_name = QtWidgets.QFileDialog.getSaveFileName(
        chart_view, "Save Chart", os.path.expanduser("~"), "PNG (*.png);;JPEG (*.jpg)")

    if file_name[0] != "":
        chart_view.grab().save(file_name[0])


def shape_param_form() -> form_nav.Form:
    '''
    draw cdf of shape parameters like EI, FI, S, C
    EI - Elongation Index
    FI - Flatness Index
    S - Sphericity
    C - Compactness

    @return: The form
    '''
    f = form_nav.Form("Shape Parameters")

    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    
    try:
        data = pd.read_csv(Config.PARTICLE_STATS_FILE)
        cols = ["EI", "FI", "S", "C"]
        data = data[cols].to_numpy()
        
        # create chart
        chart = QtCharts.QChart()
        chart.setTitle("Shape Parameters")
        chart.setAnimationOptions(QtCharts.QChart.SeriesAnimations)
        # default axis
        chart.createDefaultAxes()

        series = []
        for i in range(len(cols)):
            series.append(get_series_cdf(data[:, i], True))
            series[i].setName(cols[i])
            chart.addSeries(series[i])

        # add axis
        axis_x = QtCharts.QValueAxis()
        axis_x.setLabelFormat("%.2f")
        axis_x.setTitleText("Value")
        chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
        series[0].attachAxis(axis_x)

        axis_y = QtCharts.QValueAxis()
        axis_y.setLabelFormat("%.2f")
        axis_y.setTitleText("Cumulative Count")
        chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
        series[0].attachAxis(axis_y)

        # create chart view
        chart_view = QtCharts.QChartView(chart)
        chart_view.setRenderHint(QtGui.QPainter.Antialiasing)

        # button to save chart
        save_button = QtWidgets.QPushButton("Save Chart")
        # ask for file name
        save_button.clicked.connect(lambda: save_chart(chart_view))

        vl.addWidget(chart_view)
        vl.addWidget(save_button)

    except FileNotFoundError:
        vl.addWidget(QtWidgets.QLabel("Particle stats file not found"))

    f.form_widget.setLayout(vl)

    return f


def shape_char_dist_form() -> form_nav.Form:
    '''
    draw normal distribution of shape parameters like EI, FI, S, C
    EI - Elongation Index
    FI - Flatness Index
    S - Sphericity
    C - Compactness

    @return: The form
    '''
    f = form_nav.Form("Shape Characteristic Distribution")

    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()

    try:
        data = pd.read_csv(Config.PARTICLE_STATS_FILE)
        cols = ["EI", "FI", "S", "C"]
        data = data[cols].to_numpy()

        # create chart
        chart = QtCharts.QChart()
        chart.setTitle("Shape Characteristic Distribution")
        chart.setAnimationOptions(QtCharts.QChart.SeriesAnimations)
        # default axis
        chart.createDefaultAxes()

        series = []
        max_y = 0
        for i in range(len(cols)):
            series.append(QtCharts.QSplineSeries())

            # create bins and histogram
            bins = np.linspace(np.min(data[:, i]), np.max(data[:, i]), 100)
            hist, _ = np.histogram(data[:, i], bins=bins)
            # update max y
            max_y = max(max_y, np.max(hist))

            # add data to series
            for j in range(len(bins) - 1):
                series[i].append(bins[j], hist[j])

            series[i].setName(cols[i])
            chart.addSeries(series[i])

        # # add axis
        axis_x = QtCharts.QValueAxis()
        axis_x.setLabelFormat("%.2f")
        axis_x.setTitleText("Value")
        chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
        series[-1].attachAxis(axis_x)

        axis_y = QtCharts.QValueAxis()
        axis_y.setLabelFormat("%.2f")
        axis_y.setTitleText("Probability")
        chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
        # set max y
        axis_y.setRange(0, max_y)
        series[-1].attachAxis(axis_y)

        # create chart view
        chart_view = QtCharts.QChartView(chart)
        chart_view.setRenderHint(QtGui.QPainter.Antialiasing) 

        # button to save chart
        save_button = QtWidgets.QPushButton("Save Chart")
        # ask for file name
        save_button.clicked.connect(lambda: save_chart(chart_view))

        vl.addWidget(chart_view)
        vl.addWidget(save_button)
    
    except FileNotFoundError:
        vl.addWidget(QtWidgets.QLabel("Particle stats file not found"))

    f.form_widget.setLayout(vl)

    return f


def clusters_form() -> form_nav.Form:
    '''
    draw pie chart of clusters

    @return: The form
    '''
    f = form_nav.Form("Clusters")

    c_gui, c_data = clusters_ui.get_ui()
    c_layout = c_gui.widget().layout()
    # insert the plot widget
    c_layout.insertWidget(0, get_piechart(c_data))

    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    vl.addWidget(c_gui)

    f.form_widget.setLayout(vl)

    return f


def coordination_number_form() -> form_nav.Form:
    '''
    draw line chart of coordination number

    @return: The form
    '''
    f = form_nav.Form("Coordination Number")

    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    
    try:
        data = pd.read_csv(Config.PARTICLE_STATS_FILE)
        data = data["cn"].to_numpy()
        # x is unique values of data
        x = np.unique(data)
        # y is the number of occurences of each value in x
        y = np.array([np.sum(data == value) for value in x])

        chart_view = get_linechart(x, y, \
            "Coordination Number", "Number of Neighbours", "Number of Particles")
        # button to save chart
        save_button = QtWidgets.QPushButton("Save Chart")
        # ask for file name
        save_button.clicked.connect(lambda: save_chart(chart_view))

        vl.addWidget(chart_view)
        vl.addWidget(save_button)
    except FileNotFoundError:
        vl.addWidget(QtWidgets.QLabel("Particle stats file not found"))

    f.form_widget.setLayout(vl)

    return f


def volume_voxels_form() -> form_nav.Form:
    '''
    draw bar graph of volume in voxels

    @return: The form
    '''
    f = form_nav.Form("Volume (Voxels)")

    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    
    try:
        data = pd.read_csv(Config.PARTICLE_STATS_FILE)
        data = data["volume"].to_numpy()

        chart_view = get_bargraph(data)

        # button to save chart
        save_button = QtWidgets.QPushButton("Save Chart")
        # ask for file name
        save_button.clicked.connect(lambda: save_chart(chart_view))

        vl.addWidget(chart_view)
        vl.addWidget(save_button)

    except FileNotFoundError:
        vl.addWidget(QtWidgets.QLabel("Particle stats file not found"))

    f.form_widget.setLayout(vl)

    return f


def sphericity_form() -> form_nav.Form:
    '''
    Distribution of sphericity

    @return: The form
    '''
    f = form_nav.Form("Sphericity")

    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    
    try:
        data = pd.read_csv(Config.PARTICLE_STATS_FILE)
        data = data["S"].to_numpy()

        vl.addWidget(get_bargraph(data))
    except FileNotFoundError:
        vl.addWidget(QtWidgets.QLabel("Particle stats file not found"))

    f.form_widget.setLayout(vl)

    return f


def compactness_form() -> form_nav.Form:
    '''
    Distribution of compactness

    @return: The form
    '''
    f = form_nav.Form("Compactness")

    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()
    
    try:
        data = pd.read_csv(Config.PARTICLE_STATS_FILE)
        data = data["C"].to_numpy()

        vl.addWidget(get_bargraph(data))
    except FileNotFoundError:
        vl.addWidget(QtWidgets.QLabel("Particle stats file not found"))

    f.form_widget.setLayout(vl)

    return f


def display_image(filename):
    '''
    Display an image using dialog

    @param filename: The filename of the image
    '''
    # create image
    img = QtGui.QImage(filename)
    # create pixmap
    pixmap = QtGui.QPixmap.fromImage(img)
    # create label
    label = QtWidgets.QLabel()
    label.setPixmap(pixmap)

    # label auto resize
    label.setScaledContents(True)

    # create dialog
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Image")

    # create layout
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(label)

    dialog.setLayout(layout)

    dialog.exec_()


def get_overview_widget():
    '''
    Overview widget

    @return: The widget
    '''

    widget = QtWidgets.QWidget()

    ens_info = ensembleinfo.EnsembleInfo.load()

    # table widget to display data
    table = QtWidgets.QTableWidget()

    # set number of rows and columns
    table.setRowCount(len(ens_info.__dict__))
    table.setColumnCount(2)

    # set headers
    table.setHorizontalHeaderLabels(["Key", "Value"])

    # set the size of the table
    table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    # add ensemble info
    for i, key in enumerate(ens_info.__dict__):
        # set key
        table.setItem(i, 0, QtWidgets.QTableWidgetItem(key))

        # align key to center
        table.item(i, 0).setTextAlignment(QtCore.Qt.AlignCenter)

        if key != "pers_curve":
            # set value
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(ens_info.__dict__[key])))
            # align value to center
            table.item(i, 1).setTextAlignment(QtCore.Qt.AlignCenter)
        else:
            # add picture
            label = QtWidgets.QLabel()

            if Config.PERS_CURVE_FILE is not None:
                label.setPixmap(QtGui.QPixmap(Config.PERS_CURVE_FILE))
                label.setScaledContents(True)
                label.mousePressEvent = lambda event: display_image(Config.PERS_CURVE_FILE)
            else:
                label.setText("Persistence curve file not found")

            table.setCellWidget(i, 1, label)


    # set layout
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(table)
    widget.setLayout(layout)

    return widget


def get_bargraph(data):
    '''
    returns a bargraph widget with animation

    @param data: list of values
    @return: The widget chart
    '''

    # Create the histogram bins
    bins = np.linspace(min(data), max(data), 50)
    x_vals = bins[:-1] + (bins[1] - bins[0]) / 2
    y_vals = np.histogram(data, bins)[0]

    # Create a bar set with the histogram data
    bar_set = QtCharts.QBarSet("")
    for y_val in y_vals:
        bar_set.append(y_val)

    # Create a bar series
    bar_series = QtCharts.QBarSeries()
    bar_series.append(bar_set)

    # Create a chart object and set the bar series as its data
    chart = QtCharts.QChart()
    chart.addSeries(bar_series)

    # set animation
    chart.setAnimationOptions(QtCharts.QChart.SeriesAnimations)

    # Set the x-axis as a value axis (for histograms)
    x_axis = QtCharts.QValueAxis()
    chart.addAxis(x_axis, QtCore.Qt.AlignBottom)
    bar_series.attachAxis(x_axis)

    # Set the y-axis as a value axis (for histograms)
    y_axis = QtCharts.QValueAxis()
    y_axis.setRange(0, max(y_vals))
    chart.addAxis(y_axis, QtCore.Qt.AlignLeft)
    bar_series.attachAxis(y_axis)

    # Create a chart view to display the chart
    chart_view = QtCharts.QChartView(chart)
    chart_view.setRubberBand(QtCharts.QChartView.RectangleRubberBand)

    # title
    chart.setTitle("Volume(min: {:.2f}, max: {:.2f})".format(min(data), max(data)))

    # antialiasing
    chart_view.setRenderHint(QtGui.QPainter.Antialiasing)

    return chart_view


def get_linechart(x, y, title="Line Chart", x_axis="x", y_axis="y"):
    '''
    returns a linechart widget with animation

    @param x: list of x values
    @param y: list of y values
    @param title: title of the chart
    @param x_axis: x axis label
    @param y_axis: y axis label
    @return: The widget chart
    '''

    # Create a line series
    line_series = QtCharts.QLineSeries()

    # add data x, y
    for i, value in enumerate(y):
        line_series.append(QtCore.QPointF(x[i], value))

    # Create a chart object and set the line series as its data
    chart = QtCharts.QChart()
    chart.addSeries(line_series)
    chart.createDefaultAxes()

    # Create a chart view to display the chart
    chart_view = QtCharts.QChartView(chart)
    chart_view.setRenderHint(QtGui.QPainter.Antialiasing)

    # title
    chart.setTitle(title)

    # x axis
    chart.axisX().setTitleText(x_axis)

    # y axis
    chart.axisY().setTitleText(y_axis)

    # set animation
    chart.setAnimationOptions(QtCharts.QChart.SeriesAnimations)

    return chart_view


def get_piechart(data):
    '''
    returns a piechart widget with animation

    @param data: list of values
    @return: The widget pie chart
    '''
    # Create a pie series
    pie_series = QtCharts.QPieSeries()

    # add data
    for key, value in data.items():
        pie_series.append(key, value)

    # Create a chart object and set the pie series as its data
    chart = QtCharts.QChart()
    chart.addSeries(pie_series)

    # Create a chart view to display the chart
    chart_view = QtCharts.QChartView(chart)
    chart_view.setRenderHint(QtGui.QPainter.Antialiasing)

    # set animation
    chart.setAnimationOptions(QtCharts.QChart.SeriesAnimations)

    # set title
    chart.setTitle("Pie Chart")

    # minimum size
    chart_view.setMinimumSize(300, 300)

    return chart_view


class Insights(form_nav.Form_Nav):
    '''
    Insights window which contains forms like overview, 
    shape parameters, etc.
    '''
    def __init__(self, parent=None):
        super().__init__("Insights", parent)

        # ref to parent
        self.parent_ref = parent

        self.add_form(overview_form())
        self.add_form(shape_param_form())
        self.add_form(shape_char_dist_form())
        self.add_form(clusters_form())
        self.add_form(coordination_number_form())
        self.add_form(volume_voxels_form())
        self.add_form(sphericity_form())
        self.add_form(compactness_form())

    def updateUI(self, text:str):
        '''
        update the ui
        '''
        # throw implementation error
        raise NotImplementedError


def main(parent=None):
    '''
    Open the insights window
    '''
    dialog = Insights(parent)

    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()


