from PySide6 import QtCore, QtGui, QtWidgets
import core.utils as utils
from settings import Config
import os


def get_toolbar(parent):
    '''
    this function returns the toolbar for single particle view

    @param parent: the parent widget
    '''
    toolbar = QtWidgets.QToolBar("My main toolbar")
    toolbar.setMovable(False)

    # change the view action
    view_action = QtGui.QAction(QtGui.QIcon(
        Config.ICONS_DIR + "nstone.png"), "Toggle single grain / Neighbour grain view", parent)
    view_action.triggered.connect(parent.onToolbarViewAction)
    toolbar.addAction(view_action)
    toolbar.addSeparator()

    # settings action
    setting_action = QtGui.QAction(QtGui.QIcon(
        Config.ICONS_DIR + "gear.png"), "Settings", parent)
    setting_action.triggered.connect(parent.onToolbarSettingsAction)
    toolbar.addAction(setting_action)
    toolbar.addSeparator()

    # contact area display action
    contact_area_action = QtGui.QAction(QtGui.QIcon(
        Config.ICONS_DIR + "select.png"), "Contact Area", parent)
    contact_area_action.triggered.connect(parent.onToolbarContactAreaAction)
    toolbar.addAction(contact_area_action)
    toolbar.addSeparator()

    # contact area bar display action
    contact_bar_action = QtGui.QAction(QtGui.QIcon(
        Config.ICONS_DIR + "chart.png"), "Contact Area Bar Graph", parent)
    contact_bar_action.triggered.connect(parent.onToolbarContactBarAction)
    toolbar.addAction(contact_bar_action)
    toolbar.addSeparator()

    # mark for under segmentation action
    mark_action = QtGui.QAction(QtGui.QIcon(
        Config.ICONS_DIR + "cutter.png"), "Mark for under segmentation", parent)
    mark_action.triggered.connect(parent.onToolbarMarkAction)
    toolbar.addAction(mark_action)
    toolbar.addSeparator()

    # extremum graph show action
    extremum_graph_action = QtGui.QAction(QtGui.QIcon(
        Config.ICONS_DIR + "graph.png"), "Extremum Graph", parent)
    extremum_graph_action.triggered.connect(
        parent.onToolbarExtremumGraphAction)
    toolbar.addAction(extremum_graph_action)
    # disable the action for now
    extremum_graph_action.setEnabled(False)
    toolbar.addSeparator()

    # particle simplified saddles action
    simplfied_saddle_action = QtGui.QAction(QtGui.QIcon(
        Config.ICONS_DIR + "venn.png"), "Simplified Saddle", parent)
    simplfied_saddle_action.triggered.connect(
        parent.onToolbarSimplifiedSaddleAction)
    toolbar.addAction(simplfied_saddle_action)
    toolbar.addSeparator()

    # particle info action
    particle_info_action = QtGui.QAction(QtGui.QIcon(
        Config.ICONS_DIR + "info.png"), "Particle Info", parent)
    particle_info_action.triggered.connect(
        parent.onToolbarParticleInfoAction)
    toolbar.addAction(particle_info_action)
    toolbar.addSeparator()

    # iso surface action
    iso_surface_action = QtGui.QAction(QtGui.QIcon(
        Config.ICONS_DIR + "iso.png"), "Iso Surface", parent)
    iso_surface_action.triggered.connect(parent.onToolbarIsoSurfaceAction)
    toolbar.addAction(iso_surface_action)
    toolbar.addSeparator()

    # slider for opacity
    opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
    opacity_slider.setMinimum(0)
    opacity_slider.setMaximum(100)
    opacity_slider.setValue(100)
    opacity_slider.setFixedWidth(150)
    opacity_slider.valueChanged.connect(parent.onOpacitySliderChange)
    toolbar.addWidget(opacity_slider)
    toolbar.addSeparator()

    # toggle button for showing binder
    show_binder_toggle_button = QtWidgets.QToolButton()
    show_binder_toggle_button.setText("Show Binder")
    # checked by default
    show_binder_toggle_button.setCheckable(True)
    show_binder_toggle_button.clicked.connect(parent.onShowBinderToggleButton)
    toolbar.addWidget(show_binder_toggle_button)
    toolbar.addSeparator()

    # display circle img label
    circle_img_label = QtWidgets.QLabel()
    circle_img_label.setPixmap(QtGui.QPixmap(Config.ICONS_DIR + "orange.png"))
    # on hover, display the info
    circle_img_label.setToolTip("Particle is not labelled.")
    toolbar.addWidget(circle_img_label)
    toolbar.addSeparator()

    # search bar
    search_bar = QtWidgets.QLineEdit()
    search_bar.setObjectName("search_bar")
    search_bar.setPlaceholderText("Enter CP ID")
    search_bar.returnPressed.connect(parent.onSearchBarEnter)
    # set Completion for the search bar
    search_bar.setCompleter(QtWidgets.QCompleter([x.split(".")[0] for x in parent.files]))
    search_bar.setFixedWidth(200)
    toolbar.addWidget(search_bar)
    toolbar.addSeparator()

    # checkbox for showing cluster
    show_cluster_checkbox = QtWidgets.QCheckBox("Show Cluster")
    show_cluster_checkbox.stateChanged.connect(parent.onShowClusterCheckboxChange)
    toolbar.addWidget(show_cluster_checkbox)

    return toolbar


def onShowClusterCheckboxChange(parent, state):
    '''
    this function is called when the show cluster checkbox is changed

    @param parent: the parent widget
    @param state: the state of the checkbox
    '''
    if state == QtCore.Qt.Checked:
        # add dropdown - parent.toolbar
        dropdown = QtWidgets.QComboBox()
        # check if config.COMM_FOLDER
        if not os.path.exists(Config.COMM_DIR):
            # unset the checkbox
            for widget in parent.tool_bar.children():
                if isinstance(widget, QtWidgets.QCheckBox):
                    widget.setChecked(False)
                    widget.setCheckState(QtCore.Qt.Unchecked)
                    break
            # warning message
            QtWidgets.QMessageBox.warning(parent, "Warning", "No cluster data found")
            return 0
        dropdown.addItem("Select Cluster")
        # add items
        for i in range(0, len(os.listdir(Config.COMM_DIR))):
            dropdown.addItem("Cluster " + str(i))
        dropdown.currentIndexChanged.connect(parent.onClusterDropdownChange)
        parent.tool_bar.addWidget(dropdown)
    else:
        for widget in parent.tool_bar.children():
            if isinstance(widget, QtWidgets.QComboBox):
                widget.deleteLater()
                return 1
    return 0


def update_slider(toolbar, value):
    '''
    this function updates the slider value

    @param toolbar: the toolbar widget
    @param value: the value to set
    '''
    for widget in toolbar.children():
        if isinstance(widget, QtWidgets.QSlider):
            widget.setValue(value)


def update_image_label(toolbar, color):
    '''
    this function updates the image label

    @param toolbar: the toolbar widget
    @param color: the color to set
    '''
    for widget in toolbar.children():
        if isinstance(widget, QtWidgets.QLabel):
            widget.setPixmap(QtGui.QPixmap(Config.ICONS_DIR + color + ".png"))

            if color == "orange":
                widget.setToolTip("Particle is not labelled.")
            elif color == "green":
                widget.setToolTip("Particle is labelled as correctly segmented.")
            elif color == "red":
                widget.setToolTip("Particle is labelled as incorrectly segmented.")


def update_ui(parent, viewtype: utils.ViewType):
    '''
    this function updates the ui based on the viewtype
    basically resets the widget state

    @param parent: the parent widget
    @param viewtype: the viewtype
    '''
    parent.view_type = viewtype
    if viewtype == utils.ViewType.NEIGHBOR:
        for widget in parent.children():
            if isinstance(widget, QtGui.QAction):
                if widget.text() == "Extremum Graph":
                    widget.setEnabled(True)
                elif widget.text() == "Mark for under segmentation":
                    widget.setEnabled(False)
                elif widget.text() == "Toggle single grain / Neighbour grain view":
                    widget.setIcon(QtGui.QIcon(Config.ICONS_DIR + "stone.png"))
    elif viewtype == utils.ViewType.SINGLE:
       for widget in parent.children():
            if isinstance(widget, QtGui.QAction):
                if widget.text() == "Extremum Graph":
                    widget.setEnabled(False)
                elif widget.text() == "Mark for under segmentation":
                    widget.setEnabled(True)
                elif widget.text() == "Toggle single grain / Neighbour grain view":
                    widget.setIcon(QtGui.QIcon(Config.ICONS_DIR + "nstone.png"))



