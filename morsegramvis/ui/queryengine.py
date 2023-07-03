from PySide6 import QtCore, QtWidgets, QtWebEngineWidgets
from settings import Config
import os
import atexit
import subprocess as sp


def kill_server(p):
    '''
    Kill server

    @param p: process
    '''
    if os.name == 'nt':
        # p.kill is not adequate
        sp.call(['taskkill', '/F', '/T', '/PID', str(p.pid)])
    elif os.name == 'posix':
        p.kill()
    else:
        pass


class QueryEngine(QtWidgets.QDialog):
    '''
    Query Engine dialog to interact with the data
    '''

    def __init__(self, parent=None):
        '''
        Initialize Query Engine dialog

        @param parent: parent widget
        '''
        
        super(QueryEngine, self).__init__(parent)

        # minimize, maximize and close buttons
        self.setWindowFlags(QtCore.Qt.Window | 
            QtCore.Qt.WindowMinimizeButtonHint | 
            QtCore.Qt.WindowMaximizeButtonHint | 
            QtCore.Qt.WindowCloseButtonHint)

        # ref to parent
        self.parent = parent
        self.setWindowTitle("Data Query Engine")
        # minimum size
        # self.setMinimumSize(600, 600)
        # self.setStyleSheet("background-color: #f0f0f0")

        # cmd = f'streamlit hello --server.headless=True'
        # encode file path to avoid spaces
        # Config.QUERY_ENGINE_CODE = Config.QUERY_ENGINE_CODE.replace(" ", "\ ")
        cmd = ['streamlit', 
                            'run', 
                            Config.QUERY_ENGINE_CODE,
                            '--server.headless=True',
                            '--server.port=8501',
                            '--',
                            '--csv',
                            Config.PARTICLE_STATS_FILE]
        # print(cmd)
        self.pid = sp.Popen(cmd, stdout=sp.DEVNULL)
        atexit.register(kill_server, self.pid)

        hostname = 'localhost'
        port = 8501

        # url = 'https://python.org'

        # web view
        self.web_view = QtWebEngineWidgets.QWebEngineView()
        self.web_view.load(QtCore.QUrl(f'http://{hostname}:{port}'))

        # layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.web_view)
        self.setLayout(self.layout)



    def close_app(self):
        '''
        Close dialog and destroy it
        '''
        self.close()
        # destroy Qwidget QApplication
        self.destroy()

    def closeEvent(self, event):
        '''
        Close event

        @param event: event
        '''
        # kill server
        kill_server(self.pid)
        # close app
        self.close_app()


def main(parent=None):
    '''
    Open Query Engine dialog

    @param parent: parent widget
    '''
    dialog = QueryEngine(parent)

    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()