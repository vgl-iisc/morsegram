from PySide6 import QtWidgets, QtGui
import core.clustering as clustering
import os
from settings import Config
import logging


class Card(QtWidgets.QFrame):
    '''
    Card widget to display cluster information
    '''

    def __init__(self, title, description, parent=None):
        super(Card, self).__init__(parent)

        # title
        self.title = QtWidgets.QLabel(title)
        self.title.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))

        # description
        self.description = QtWidgets.QLabel(description)
        self.description.setFont(QtGui.QFont("Arial", 15, QtGui.QFont.Normal))

        # layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.description)

        # layout color
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # rectangle border
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)

        # set layout
        self.setLayout(layout)


def get_ui():
    '''
    list of cards of cluster
    @return: scroll area widget, cluster data
    '''

    # button
    button = QtWidgets.QPushButton("Compute Cluster")
    button.setFont(QtGui.QFont("Arial", 15, QtGui.QFont.Bold))
    button.setFixedHeight(50)
    # on click event
    button.clicked.connect(compute_cluster)

    # scroll area
    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidgetResizable(True)

    # widget
    widget = QtWidgets.QWidget()
    scroll_area.setWidget(widget)

    # layout
    layout = QtWidgets.QVBoxLayout()
    widget.setLayout(layout)

    # add button
    layout.addWidget(button)

    cluster_data = {}

    # iterate over files in config.COMM_DIR
    try:
        for file in os.listdir(Config.COMM_DIR):
            # get file path
            file_path = os.path.join(Config.COMM_DIR, file)
            # check if file is a file
            if os.path.isfile(file_path):
                # get file name
                file_name = os.path.splitext(file)[0]

                content = ""

                # read the content of the file
                with open(file_path, "r") as file:
                    content = file.read()

                # parse [ int , int, ..]
                content = content.replace("[", "")
                content = content.replace("]", "")
                content = content.replace(" ", "")
                content = content.split(",")

                content = [int(x) for x in content]

                # add card
                card = Card( "Cluster Number : " + file_name, "Population : " + str(len(content)))
                layout.addWidget(card)

                # add to cluster data
                cluster_data[file_name] = len(content)

    except Exception as e:
        logging.getLogger().error("Error while reading files in " + Config.COMM_DIR + " : " + str(e))
        # e is file not found
        if isinstance(e, FileNotFoundError):
            layout.addWidget(QtWidgets.QLabel("No cluster computed yet"))

    return scroll_area, cluster_data


def compute_cluster():
    '''
    Perform louvain clustering
    '''
    clustering.perform_louvain()

    # display message
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText("Cluster computed")
    msg.setWindowTitle("Cluster")
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()


