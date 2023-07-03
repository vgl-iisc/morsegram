from PySide6 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib
import numpy as np
import pyqtgraph as pg
# use Qt5Agg backend
try:
    matplotlib.use("QtAgg")
except ValueError:
    matplotlib.use("Qt5Agg")


class TaskType:
    '''
    Task type enum
    like plot for displaying contact area bar graph
    and plot for selecting volume threshold to clean data
    '''
    CONTACT_AREA = 0
    CLEAN_DATA = 1

class Task:
    '''
    Task class containing data and task type
    '''

    def __init__(self, data : dict, task_type : TaskType):
        '''
        Initialize task

        @param data: data to be plotted
        @param task_type: task type
        '''
        self.data = data
        self.task_type = task_type

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        # fig bg color
        fig.patch.set_facecolor('black')
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor('black')
        # text color
        self.axes.tick_params(axis='y', colors='white')
        self.axes.tick_params(axis='x', colors='white')
        super().__init__(fig)


# dialog class
class PlotDialog(QtWidgets.QDialog):
    '''
    Plot dialog shows bar graph
    '''

    def __init__(self, task : Task, parent=None):
        '''
        Initialize dialog

        @param task: task containing data and task type
        @param parent: parent widget
        '''
        super(PlotDialog, self).__init__(parent)
        if task.task_type == TaskType.CONTACT_AREA:
            self.setWindowTitle("Bar Graph : " + str(task.data['grain_id']))
            self.setMinimumSize(600, 400)
            self.data = task.data['data']

            sc = MplCanvas(self, width=5, height=4, dpi=100)

            # title to plot
            # sc.axes.set_title("Bar Graph : " + str(grain_id))
            # sc.axes.plot([0, 1, 2, 3], [0, 1, 2, 3])

            # histogram
            # data = {123: (30, "#ff0000"), 456: (50, "#00ff00"), 789: (10, "#0000ff"), 101: (60, "#ffff00")}
            # x - axis is index of data
            x = np.arange(len(self.data))
            # y - axis is value of data
            # print([d[0] for d in self.data.values()])
            y = np.array([d[0] for d in self.data.values()])
            # plot histogram with bar in different color
            sc.axes.bar(x, y, align="center", color=[c[1] for c in self.data.values()])
        
            if y.size > 0:
                max_y = max(y)

            # legend for each bar
            for i, v in enumerate(self.data):
                if max_y < 10:
                    # in order to properly display the text
                    sc.axes.text(x[i], y[i] + 0.1, str(v), ha="center", color="white")
                else:
                    sc.axes.text(x[i], y[i] + 1, str(v), ha="center", color="white")

            # hide x axis values
            sc.axes.set_xticks([])
            # ya-xis label
            sc.axes.set_ylabel("Number of Quads in Contact Region", color="white")

            self.layout = QtWidgets.QVBoxLayout()
            try:
                self.layout.addWidget(sc)
                self.setLayout(self.layout)
            except TypeError:

                win = pg.plot()
                win.setWindowTitle("Bar Graph : " + str(task.data['grain_id']))
                # adding legend
                win.addLegend()
                # set properties of the label for y axis
                win.setLabel('left', 'Number of Quads in Contact Region', 'Quads')
                # set properties of the label for x axis
                win.setLabel('bottom', 'CP ID', 'CP ID')
                
                # bar graph with different color
                self.graphWidget = pg.BarGraphItem(x=x, height=y, width=0.5, brushes=[c[1] for c in self.data.values()])
                win.addItem(self.graphWidget)
                ax = win.getAxis('bottom')
                keys = list(self.data.keys())
                ax.setTicks([[(i, str(keys[i])) for i in range(len(self.data))]])

        elif task.task_type == TaskType.CLEAN_DATA:
            # TODO : code for clean data
            # histogram using np for [1,2,3,4,5,6,7,8,9,10]
            min_val = min(task.data['data'])
            max_val = max(task.data['data'])
            bins = np.linspace(min_val, max_val, len(task.data['data']) // 100)
            
            win = pg.plot()
            win.setWindowTitle("Clean Data")
            # plt1 = win.addPlot()
            # adding legend
            win.addLegend()
            # set properties of the label for y axis
            win.setLabel('left', 'Number of grains', 'Grains')
            # set properties of the label for x axis
            win.setLabel('bottom', 'Volume', 'Voxels')

            # update the x and y axis
            hist_data = np.histogram(task.data['data'], bins=bins)

            y = hist_data[0]
            x = hist_data[1]

            win.plot(x, y, stepMode=True, fillLevel=0, brush=(0,0,255,150))
            # win.show()
            # self.graphWidget = pg.BarGraphItem(x=x, height=y, width=0.15)
            # win.addItem(self.graphWidget)


def main(task : Task, parent=None):
    '''
    Open Plot dialog

    @param task: task containing data and task type
    @param parent: parent widget
    '''
    dialog = PlotDialog(task, parent)
    parent.contact_area_bar_graph_dialog = dialog
    # position the dialog right of the parent
    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())
    # resize dialog to fit the content
    dialog.resize(dialog.sizeHint())
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()