from PySide6 import QtCore, QtWidgets, QtGui
from multiprocessing import Pipe, Queue
from core import multiproc
from settings import Config


class NavigationItem(QtWidgets.QListWidgetItem):
    """
    Custom QListWidgetItem with a name.
    """

    def __init__(self, text, parent=None):
        '''
        Initialize the item

        @param text: The text to be displayed
        @param parent: The parent widget
        '''
        super(NavigationItem, self).__init__(text, parent)

        # set font
        self.setFont(QtGui.QFont("Arial", 15, QtGui.QFont.Bold))

        # set the size of the item
        self.setSizeHint(QtCore.QSize(0, 50))

        # set text alignment
        self.setTextAlignment(QtCore.Qt.AlignCenter)


class Form():
    """
    Form class contains the form widget and the navigation item
    form widget is the widget that will be displayed 
    when the navigation item is clicked and form widget
    contains all the input fields and buttons
    """

    def __init__(self, name, parent=None):
        '''
        Initialize the form

        @param name: The name of the form
        @param parent: The parent widget
        '''

        self.parent_ref = parent
        self.name = name
        self.nav = NavigationItem(self.name)
        self.form_widget : QtWidgets.QWidget = None


class Form_Nav(QtWidgets.QDialog):
    """
    Form_Nav class contains the navigation widget and the form widget.
    """

    def __init__(self, win_title = "Form Navigation Window", parent=None):
        '''
        Initialize the form navigation window

        @param win_title: The title of the window
        @param parent: The parent widget
        '''
        super(Form_Nav, self).__init__(parent)

        self.win_title = win_title

        self.success_styleSheet = "QProgressBar::chunk {background-color: #00FF00;}" + \
                                "QProgressBar {border: 2px solid grey; border-radius:" + \
                                    " 5px; text-align: center;}"

        # create a communication pipe
        self.parent_conn, self.child_conn = Pipe()
        self.queue = Queue()
        # create a thread to listen to the pipe
        self.emitter = multiproc.Emitter(self.parent_conn)
        self.emitter.daemon = True
        self.emitter.start()
        self.emitter.ui_data_available.connect(self.updateUI)

        self.proc_pool = None

        # minimize, maximize and close buttons
        self.setWindowFlags(QtCore.Qt.Window | 
            QtCore.Qt.WindowMinimizeButtonHint | 
            QtCore.Qt.WindowMaximizeButtonHint | 
            QtCore.Qt.WindowCloseButtonHint)

        self.parent_ref = parent
        self.setWindowTitle(win_title)
        self.setMinimumSize(1100, 700)
        # self.setFixedSize(1100, 700)
        self.forms = []

        # create layout
        self.layout = QtWidgets.QVBoxLayout()

        # widget with two columns, one for the list and one for the image
        self.widget = QtWidgets.QWidget()
        self.widget_layout = QtWidgets.QHBoxLayout()
        self.widget.setLayout(self.widget_layout)

        # list widget
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.itemClicked.connect(self.navigation_item_clicked)
        self.widget_layout.addWidget(self.list_widget)

        self.frame = QtWidgets.QFrame()
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_layout = QtWidgets.QVBoxLayout()
        self.frame.setLayout(self.frame_layout)


        self.widget_layout.addWidget(self.frame)

        self.get_nav_content("Start")

        # add widget to layout
        self.layout.addWidget(self.widget)

        # close button
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.close_app)
        self.layout.addWidget(self.close_button)

        # set layout
        self.setLayout(self.layout)

    def add_form(self, form: Form):
        '''
        Add a form to the form navigation window

        @param form: The form to be added
        '''
        self.list_widget.addItem(form.nav)
        self.forms.append(form)
        form.form_widget.hide()
        self.frame_layout.addWidget(form.form_widget)

    def get_form(self, name):
        '''
        Get the form with the given name

        @param name: The name of the form
        @return: The form with the given name
        '''
        for form in self.forms:
            if form.name == name:
                return form
        return None

    def navigation_item_clicked(self, item):
        '''
        Handle the click event of the navigation item

        @param item: The clicked item
        '''
        if self.current_widget != item.text():
            self.get_nav_content(item.text())

    def get_nav_content(self, item):
        '''
        Get the content of the navigation item

        @param item: The clicked item
        '''
        # if self.widget_layout.count() > 1:
        #     wid = self.widget_layout.itemAt(1).widget()
        #     self.widget_layout.removeWidget(wid)
        #     wid.deleteLater()

        # hide the all widgets in the frame
        for i in range(self.frame_layout.count()):
            curr_widget = self.frame_layout.itemAt(i).widget()
            curr_widget.hide()

        self.current_widget = item

        if item == "Start":
            # label = QtWidgets.QLabel("Start")
            # label.setAlignment(QtCore.Qt.AlignCenter)
            # label.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))

            # add image to the frame
            label = QtWidgets.QLabel()
            if self.win_title == "Miscellaneous Tools":
                pixmap = QtGui.QPixmap(Config.ICONS_DIR + "/mt.jpeg")

            elif self.win_title == "Insights":
                pixmap = QtGui.QPixmap(Config.ICONS_DIR + "/insights.jpeg")
            
            elif self.win_title == "Surface Reconstruction":
                pixmap = QtGui.QPixmap(Config.ICONS_DIR + "/sr.jpeg")

            # resize the image automatically
            pixmap = pixmap.scaledToWidth(600)

            
            label.setPixmap(pixmap)
            label.setAlignment(QtCore.Qt.AlignCenter)



            self.frame_layout.addWidget(label)

            # self.frame_layout.addWidget()
        else:
            for form in self.forms:
                if form.name == item:
                    form.form_widget.show()
                    break

        self.widget_layout.setStretch(0, 1)
        self.widget_layout.setStretch(1, 2)

    def close_app(self):
        '''
        terminate the emitter thread and close the process pool
        '''

        if self.proc_pool is not None:
            # close the process pool
            self.proc_pool.close()

        # close the emitter thread
        self.emitter.stop()

        # # close the queue
        # self.queue.close()

        # destroy Qwidget QApplication
        self.destroy()

    def closeEvent(self, event):
        '''
        Handle the close event of the window

        @param event: The close event
        '''
        self.close_app()