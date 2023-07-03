import core.utils as utils
import vtk
import time
from settings import Config
from PySide6 import QtCore, QtGui, QtWidgets
from start import Start
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import ui.settings_dialog as settings_dialog
from core import cleandata
from ui.window import Window
import os
import logging


class EnsembleView(Window):
    '''
    This window displays ensemble view of the data.
    '''

    def __init__(self, parent=None):
        super(EnsembleView, self).__init__(parent)

        self.parent_ref: Start = parent

        self.bg_color = True
        self.light_factor = True
        self.ao_factor = True

        self.caption_repr = self.get_caption_repr()
        self.last_picked_actor = None
        self.maxima_data = None
        self.last_picked_property = vtk.vtkProperty()
        self.input_raw_data = None

        start_time = time.time()

        self.iren.AddObserver("KeyPressEvent", self.key_press_event)
        # mouse button event
        self.iren.AddObserver("LeftButtonPressEvent", self.left_button_press_event)
        self.ren.AddObserver("EndEvent", self.compute_fps)

        # Add the actor to the scene
        self.ren.AddActor(self.get_ensemble_actor())
        self.ren.SetBackground(Config.BG_COLOR)

        self.ambient_occlusion()

        # print execution time
        print("Execution time: ", time.time() - start_time)

        print("==========================================================")
        print("Rendering the ... ")
        print("==========================================================")

        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

        self.window_title = Config.APP_NAME
        self.setWindowTitle(self.window_title)
        self.start_time = time.time()

        # --------------- Toolbar ----------------
        toolbar = QtWidgets.QToolBar("My main toolbar")

        setting_action = QtGui.QAction(QtGui.QIcon("ui/icons/gear.png"), "Settings", self)
        setting_action.setStatusTip("Settings")
        setting_action.triggered.connect(self.onToolbarSettingsAction)
        toolbar.addAction(setting_action)

        # separator
        toolbar.addSeparator()

        # info action
        info_action = QtGui.QAction(QtGui.QIcon("ui/icons/info.png"), "Info", self)
        info_action.setStatusTip("Info")
        info_action.triggered.connect(self.onToolbarInfoAction)
        toolbar.addAction(info_action)

        # interaction mode checkbox
        toolbar.addSeparator()
        self.interaction_mode_checkbox = QtWidgets.QCheckBox("Interaction Mode")
        self.interaction_mode_checkbox.setChecked(False)
        self.interaction_mode_checkbox.stateChanged.connect(self.onInteractionModeCheckbox)
        toolbar.addWidget(self.interaction_mode_checkbox)

        # separator
        toolbar.addSeparator()

        # checkbox for loading clean ensemble
        self.clean_ensemble_checkbox = QtWidgets.QCheckBox("Clean Ensemble")
        self.clean_ensemble_checkbox.setChecked(False)
        self.clean_ensemble_checkbox.stateChanged.connect(self.onCleanEnsembleCheckbox)
        toolbar.addWidget(self.clean_ensemble_checkbox)

        # camera info toolbar
        self.add_toolbar(toolbar, "ui/icons/cam.png", "Camera Information", self.onToolbarCamInfoAction)
        # export toolbar
        self.add_toolbar(toolbar, "ui/icons/export.png", "Export Scene as Image", self.onToolbarExportAction)

        # --------------- End Toolbar ----------------
        # reset camera
        self.ren.ResetCamera()
        # Start the event loop.
        self.show()
        self.iren.Initialize()

    def get_ensemble_actor(self):
        '''
        Get ensemble actor.
        '''
        file_data = self.parent_ref.ensemble

        print("Data is a Object of type: ", file_data.GetClassName())

        utils.print_all_arrays_point_data(file_data)
        utils.print_all_arrays_cell_data(file_data)

        # extract surface from unstructured grid
        surface_filter = vtk.vtkDataSetSurfaceFilter()
        surface_filter.SetInputData(file_data)
        surface_filter.Update()

        # Create a mapper
        # mapper = vtk.vtkPolyDataMapper()
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(utils.compute_normals(surface_filter.GetOutput()))

        # Create a actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        actor.GetProperty().SetSpecularPower(Config.SPECULAR_POWER)
        actor.GetProperty().SetSpecular(Config.SPECULAR)
        actor.GetProperty().SetDiffuse(Config.DIFFUSE)
        actor.GetProperty().SetAmbient(Config.AMBIENT)

        # set interpolation to phong
        utils.set_interpolation(actor)
        return actor

    def onToolbarInfoAction(self, s):
        """
        Info action.
        display list of error particle CP IDs

        @param s: status
        """
        error_grains = cleandata.CleanData()
        error_grains.load()

        # displaying cp ids in the list format in a Dialog
        listWidget = QtWidgets.QListWidget()
        for cp_id in error_grains.cp_ids:
            listWidget.addItem(str(cp_id))
        
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Error Grains")
        dialog.setWindowModality(QtCore.Qt.NonModal)
        dialog.resize(400, 300)
        dialog.setLayout(QtWidgets.QVBoxLayout())
        dialog.layout().addWidget(listWidget)
        dialog.show()

    def onToolbarSettingsAction(self, s):
        """
        Open the settings dialog.

        @param s: status
        """
        settings_dialog.main(self)

    def onInteractionModeCheckbox(self, state):
        """
        Interaction mode checkbox to find the particle ids on click.

        @param state: checkbox state
        """
        if state == QtCore.Qt.Checked:
            print("Interaction Mode: ON")

            actors = []
            self.maxima_data = utils.get_grains_point_cloud(utils.read_file(Config.MAXIMAS_FILE))
            # iterate over all file in config.PARTICLES_DIR
            for file in os.listdir(Config.PARTICLES_MESH_DIR):
                cp_id = int(os.fsdecode(file).split(".")[0])
                try:
                    actors += utils.get_actors_list(self.maxima_data, {}, cp_id, self.ren, False)
                except Exception as e:
                    logging.getLogger().error("(Ens view) Error while getting actors list for cp_id: " + str(cp_id))
            
            # remove all actors from the renderer
            self.ren.RemoveAllViewProps()
            # add actors to the renderer
            for actor in actors:
                self.ren.AddActor(actor)
        else:
            print("Interaction Mode: OFF")
            self.caption_repr.Off()

            # remove all actors from the renderer
            self.ren.RemoveAllViewProps()

            # add ensemble actor to the renderer
            self.ren.AddActor(self.get_ensemble_actor())

    def compute_fps(self, obj, event):
        """
        Compute the fps.
        @param obj: vtkRenderWindowInteractor
        @param event: event
        """
        timeInSeconds = time.time() - self.start_time
        if timeInSeconds != 0.0:
            fps = 1.0 / timeInSeconds
            # print("FPS: ", fps)
            # update window title with fps value integer
            self.setWindowTitle(self.window_title + " FPS: " + str(int(fps)))
        self.start_time = time.time()

    def key_press_event(self, obj, event):
        """
        Key press event.
        @param obj: vtkRenderWindowInteractor
        @param event: event
        """
        key = obj.GetKeySym()
        # quit the app on esc
        if key == 'Escape':
            self.closeEvent(None)

    def update_ao_factor(self):
        '''
        update the ambient occlusion
        '''
        self.ambient_occlusion()
        self.iren.Render()

    def clean(self):
        '''
        clean the scene and free memory
        '''
        self.parent.delaunaty_3d = None

    def closeEvent(self, event):
        '''
        close event

        :param event: event
        '''
        self.clean()
        self.destroy()

    def get_silhouette_actor(self):
        '''
        Get silhouette actor.

        :return: silhouette, silhouette actor
        '''
        silhouette = vtk.vtkPolyDataSilhouette()
        silhouette.SetCamera(self.ren.GetActiveCamera())

        # mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(silhouette.GetOutputPort())

        # actor
        silhouette_actor = vtk.vtkActor()
        silhouette_actor.SetMapper(mapper)
        silhouette_actor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d("Tomato"))
        silhouette_actor.GetProperty().SetLineWidth(5)

        return silhouette, silhouette_actor

    def left_button_press_event(self, obj, event):
        '''
        Find the particle id on click.

        :param obj: vtkRenderWindowInteractor
        :param event: event
        '''
        if self.interaction_mode_checkbox.isChecked():
            click_pos = self.iren.GetEventPosition()

            # pick the actor
            picker = vtk.vtkPropPicker()
            picker.Pick(click_pos[0], click_pos[1], 0, self.ren)

            # get the actor
            actor = picker.GetActor()

            if actor:
                
                if self.last_picked_actor:
                    self.last_picked_actor.GetProperty().DeepCopy(self.last_picked_property)

                self.last_picked_property.DeepCopy(actor.GetProperty())
                actor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d("Tomato"))
                actor.GetProperty().SetDiffuse(1.0)
                actor.GetProperty().SetSpecular(0.0)
                actor.GetProperty().EdgeVisibilityOn()

                self.last_picked_actor = actor

                cp_id = int(actor.GetProperty().GetMaterialName().split("_")[1])

                # update the caption
                self.update_caption(actor.GetProperty().GetMaterialName(), self.maxima_data[cp_id][0])

                self.caption_repr.On()

    def update_caption(self, caption, location):
        '''
        update the caption

        :param caption: caption text
        :param location: caption location
        '''
        # get the caption representation
        cr = self.caption_repr.GetRepresentation()
        cr.GetCaptionActor2D().SetCaption(caption)

        # position the text
        cr.SetAnchorPosition(location)

    def get_caption_repr(self):
        '''
        Get caption representation.

        :return: caption representation
        '''
        # create a caption
        cr = vtk.vtkCaptionRepresentation()
        cr.GetCaptionActor2D().GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d("Tomato"))

        widget = vtk.vtkCaptionWidget()
        widget.SetInteractor(self.iren)
        widget.SetRepresentation(cr)

        return widget

    def onCleanEnsembleCheckbox(self, state):
        '''
        View clean ensemble.

        :param state: checkbox state
        '''
        if state == QtCore.Qt.Checked:
            print("Clean Ensemble: ON")
            Config.ENSEMBLE_FILE = Config.ENSEMBLE_FILE.replace(".vtu", "_clean.vtu")
            self.parent.load_ensemble_file()
            self.ren.RemoveAllViewProps()
            self.ren.AddActor(self.get_ensemble_actor())
        else:
            print("Clean Ensemble: OFF")
            Config.ENSEMBLE_FILE = Config.ENSEMBLE_FILE.replace("_clean.vtu", ".vtu")
            self.parent.load_ensemble_file()
            self.ren.RemoveAllViewProps()
            self.ren.AddActor(self.get_ensemble_actor())


if __name__ == '__main__':
    print("You cannot run this file directly.")


def main(parent=None):
    '''
    Open the ensemble view window.

    :param parent: parent window
    '''
    dialog = EnsembleView(parent)
    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())

    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()


