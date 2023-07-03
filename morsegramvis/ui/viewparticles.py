import math
import core.utils as utils
import vtk
from settings import Config
from PySide6 import QtCore, QtWidgets, QtGui
from ui.transferfunc import ControlPoint
import ui.settings_dialog as settings_dialog
from ui import particleinfo_dialog
import os
import core.contactstats as contactstats
import ui.plotgraph as plotgraph
from ui import toolbar
from core import fileutil, particleseg
import logging
from ui.window import Window
from core import actors
import pandas as pd
import error_msgs


class Viewparticles(Window):
    '''
    Single/Multiple particle view.
    Neighbors are displayed in the multiple particle view.
    Extremum graph, contact area bar graph, particle info, contact area, simplified saddle,
    and isosurface are displayed.
    '''

    def __init__(self, parent=None):
        super(Viewparticles, self).__init__(parent)

        self.bg_color = True
        self.light_factor = True
        self.ao_factor = False
        self.text_actor_visible = True
        self.view_type = utils.ViewType.SINGLE
        self.showExtremumGraph = False
        self.paritcle_info_dialog = None
        self.contact_area_bar_graph_dialog = None
        self.particle_labels = particleseg.LabelList()
        self.input_raw_data = None
        self.input_distance_data = None
        self.binder_show = False
        self.iso_show = False   # show isosurface
        self.iso_opacity = 1  # isosurface opacity
        self.control_points: list(ControlPoint) = None
        self.show_simplified_saddle_actor = False
        self.show_simplified_text_actor = False
        self.alpha_range = (0,1)
        # list of files in the directory Grains
        self.files = os.listdir(Config.PARTICLES_MESH_DIR)
        self.tool_bar = toolbar.get_toolbar(self)
        
        # ================ Volume Cutoff Filter  ================
        self.vol_cutoff_filter = True
        self.vol_range = (0, 1000000000)    # this range captures all the particles
        if utils.check_file(Config.PARTICLE_STATS_FILE):
            df = pd.read_csv(Config.PARTICLE_STATS_FILE, index_col='cp_id')
            self.vol = df['num_voxels'].copy()
            self.vol_range = (self.vol.min(), self.vol.max())
        # =======================================================

        self.curr_file = 0
        self.showContactRegion = False        # show contacts region

        maxima_data_file = utils.read_file(Config.MAXIMAS_FILE)
        self.maxima_data = utils.get_grains_point_cloud(maxima_data_file)

        contact_net_data = utils.read_file(Config.CONTACT_NET_FILE)
        self.contact_points = utils.get_contact_network(contact_net_data)

        self.iren.AddObserver("KeyPressEvent", self.key_press_event)

        try:
            while True:
                grain_file = Config.PARTICLES_MESH_DIR + self.files[self.curr_file]
                reader = vtk.vtkXMLPolyDataReader()
                reader.SetFileName(grain_file)
                reader.Update()

                grain_id = int(self.files[self.curr_file].split(".")[0])

                # skip empty files (no points)
                # and files with volume less than the threshold
                if reader.GetOutput().GetNumberOfPoints() > 0 and self.is_particle_vol(grain_id):
                    break
                else:
                    logging.getLogger().warning("Skipping empty file: " + grain_file)
                    self.curr_file += 1
        except IndexError:
            # no particles in the directory
            logging.getLogger().error("No valid files in the directory: " + Config.PARTICLES_MESH_DIR)
            QtWidgets.QMessageBox.critical(self, "Error", "No valid files in the directory: " 
                                           + Config.PARTICLES_MESH_DIR + "\n" + error_msgs.SR_MSG)
            self.close()
        
        grain_id = int(self.files[self.curr_file].split(".")[0])

        self.update_neighbors()

        self.setWindowTitle("Particle with CP ID: " + str(grain_id))

        # spatial map renderer - display particle in the ensemble space
        if os.path.exists(Config.ENSEMBLE_FILE):
            file_data = utils.read_file(Config.ENSEMBLE_FILE)
            assembly = utils.get_bounding_cylinder(file_data.GetBounds())

            rgb = [0.0, 0.0, 0.0]
            colors = vtk.vtkNamedColors()
            colors.GetColorRGB('Wheat', rgb)
            # Set up the widget
            self.widget = vtk.vtkOrientationMarkerWidget()
            self.widget.SetOrientationMarker(assembly)
            self.widget.SetInteractor(self.iren)
            self.widget.SetViewport(0.0, 0.0, 0.2, 0.2)
            self.widget.SetOutlineColor(*rgb)
            self.widget.SetEnabled(1)
            self.widget.SetZoom(1.0)
            self.widget.InteractiveOn()
            self.widget.KeyPressActivationOff()
        else:
            print("No orientation marker due to missing file: " + Config.ENSEMBLE_FILE)

        self.update_actors(self.iren, utils.get_actors_list(self.maxima_data, self.contact_points,
                                                            grain_id, self.ren, Config.PARTICLES_MESH_DIR + str(grain_id) + ".vtp"))

        self.ren.ResetCamera()
        self.ren.GetActiveCamera().Zoom(0.5)

        self.ren.SetBackground(Config.BG_COLOR)

        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

        self.statusBar().showMessage(
            "index " + str(self.curr_file + 1) + " of " + str(len(self.files)))

        
        self.add_toolbar(self.tool_bar, "ui/icons/cam.png", "Camera Information", self.onToolbarCamInfoAction)
        # export toolbar
        self.add_toolbar(self.tool_bar, "ui/icons/export.png", "Export Scene as Image", self.onToolbarExportAction)
        self.addToolBar(self.tool_bar)

        # Start the event loop.
        self.show()
        self.iren.Initialize()

    def update_iso_surface(self):
        '''
        Update isosurface
        '''
        # remove old isosurface
        self.remove_iso_surface()
        self.onToolbarIsoSurfaceAction(None)

    def onToolbarIsoSurfaceAction(self, s):
        '''
        Display isosurface

        @param s: bool - True or False
        '''
        if self.input_distance_data is None:
            try:
                self.input_distance_data = utils.read_file(Config.RAW_IMAGE_FILE)
            except AttributeError:
                QtWidgets.QMessageBox.critical(self, "Error", "No input file found in " 
                                            + Config.CHAMFER_DIR)
                return
            # scalar range
            self.distance_scalar_range = self.input_distance_data.GetScalarRange()
            self.iso_value = 0
            print("distance field scalar range: ", self.distance_scalar_range)

        if self.input_distance_data is None:
            QtWidgets.QMessageBox.critical(self, "Error", "No input file found in " 
                                        + Config.CHAMFER_DIR)
            return

        if s is not None:
            self.iso_show = not self.iso_show

        if not self.iso_show:
            # remove the actor
            self.remove_iso_surface()
            # update the view
            self.iren.Render()
            return
        
        self.actors_extent = []
        # update extent to compare 
        for actor in self.ren.GetActors():
            # actor material name
            if actor.GetProperty().GetMaterialName().startswith("Particle_"):
                self.actors_extent.append(actor.GetBounds())
        
        # print("extent: ", self.actors_extent)        

        for i, extent in enumerate(self.actors_extent):

            extract = vtk.vtkExtractVOI()
            extract.SetInputData(self.input_distance_data)
            extract.SetVOI(math.floor(extent[0]), math.ceil(extent[1]),
                            math.floor(extent[2]), math.ceil(extent[3]),
                            math.floor(extent[4]), math.ceil(extent[5]))
            extract.Update()

            # iso surface
            iso = vtk.vtkMarchingCubes()
            iso.SetInputConnection(extract.GetOutputPort())
            iso.ComputeNormalsOn()
            iso.SetValue(0, self.iso_value)
            iso.Update()

            # iso surface mapper
            iso_mapper = vtk.vtkPolyDataMapper()
            iso_mapper.SetInputConnection(iso.GetOutputPort())
            iso_mapper.ScalarVisibilityOff()

            # iso surface actor
            iso_actor = vtk.vtkActor()
            iso_actor.SetMapper(iso_mapper)
            # material name
            iso_actor.GetProperty().SetMaterialName("iso_surface_" + str(i))
            # opacity
            iso_actor.GetProperty().SetOpacity(self.iso_opacity)

            self.ren.AddActor(iso_actor)

        # update the view
        self.iren.Render()

    def remove_iso_surface(self):
        '''
        Remove isosurface
        '''
        for actor in self.ren.GetActors():
            if actor.GetProperty().GetMaterialName().startswith("iso_surface"):
                self.ren.RemoveActor(actor)

    def onToolbarSimplifiedSaddleAction(self, s):
        '''
        Display graph involving simplified 2-saddle and maximas.

        @param s: bool - True or False
        '''
        if self.show_simplified_saddle_actor:
            # loop over all actors and remove the simplified saddle actor
            for actor in self.ren.GetActors():
                # actor material name contains simplified
                if "simplified" in actor.GetProperty().GetMaterialName():
                    self.ren.RemoveActor(actor)
            self.show_simplified_saddle_actor = False
        else:
            try:
                actors.get_simplified_triples(int(self.files[self.curr_file].split(".")[0]), self)
            except FileNotFoundError:
                logging.getLogger().error("No simplified saddle file found.")
                QtWidgets.QMessageBox.critical(self, "Error", "No simplified saddle file found.")
                return

        # update the view
        self.iren.Render()

    def update_text_actor_visible(self):
        """
        Update text actor visibility.
        """
        self.show_simplified_text_actor = not self.show_simplified_text_actor
        if not self.show_simplified_text_actor:
            for actor in self.ren.GetActors():
                # actor material name contains simplified
                if actors.SIM_TEXT_ACTOR_NAME in actor.GetProperty().GetMaterialName():
                    actor.SetVisibility(self.show_simplified_text_actor)
            self.iren.Render()

    def display_alpha_range(self, a1, a2):
        '''
        Display the text actors in the alpha range.

        @param a1: float - alpha left value
        @param a2: float - alpha right value
        '''
        self.alpha_range = (a1, a2)
        if not self.show_simplified_text_actor:
            return
        for actor in self.ren.GetActors():
            # actor material name contains simplified
            if actors.SIM_TEXT_ACTOR_NAME in actor.GetProperty().GetMaterialName():
                # material name contains the alpha value - SIM_TEXT_ACTOR_NAME_0.1
                alpha = float(actor.GetProperty().GetMaterialName().split("_")[-1])
                if alpha >= a1 and alpha <= a2:
                    actor.SetVisibility(True)
                else:
                    actor.SetVisibility(False)
        
        self.iren.Render()

    def onToolbarParticleInfoAction(self, s):
        """
        Open particle info dialog.

        @param s: bool - True or False
        """
        try:
            particleinfo_dialog.main(Config.PARTICLE_STATS_FILE, self)
        except FileNotFoundError:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("No csv file found")
            msg.setInformativeText("Run the particle stats computation(including noisy grains).")
            msg.setWindowTitle("Error")
            msg.exec()

    def onToolbarSettingsAction(self, s):
        """
        Open settings dialog.

        @param s: bool - True or False
        """
        settings_dialog.main(self)

    def onToolbarContactAreaAction(self, s):
        """
        Display the contact area of the current particle.

        @param s: bool - True or False
        """

        if self.showContactRegion:
            self.showContactRegion = False
            for actor in self.ren.GetActors():
                if actor.GetProperty().GetMaterialName() == "Contact Region":
                    self.ren.RemoveActor(actor)
        else:
            self.showContactRegion = True
            grain_id = int(self.files[self.curr_file].split(".")[0])
            try:
                cp_saddle_list = [
                    int(contact_pt.saddle_2_cp_id) for contact_pt in self.contact_points[grain_id]]
            except KeyError:
                logging.getLogger().warning("No contact points found for grain id: " + str(grain_id))
                cp_saddle_list = []
            try:
                for actor in contactstats.contact_region_actors(cp_saddle_list, Config.CONTACT_REGION_DIR):
                    self.ren.AddActor(actor)
            except FileNotFoundError:
                QtWidgets.QMessageBox.critical(self, "Error", "No contact region file found."+
                " Run the contact stats computation.")
        self.iren.Render()

    def onOpacitySliderChange(self, value):
        """
        Change the Opacity of existing actors.

        @param value: int - opacity value
        """
        actors = self.ren.GetActors()
        for actor in range(actors.GetNumberOfItems()):
            actor_prop = actors.GetItemAsObject(actor).GetProperty()
            if actor_prop.GetMaterialName().startswith("Particle"):
                    actor_prop.SetOpacity(value / 100.0)
        actors.GetItemAsObject(actor).Modified()
        self.iren.Render()

    def onToolbarContactBarAction(self, s):
        """
        Display Contact area bar graph

        @param s: bool - True or False
        """
        grain_id = int(self.files[self.curr_file].split(".")[0])
        try:
            cp_saddle_list = [(int(contact_pt.sibling_cp_id), int(contact_pt.saddle_2_cp_id))
                        for contact_pt in self.contact_points[grain_id]]
        except KeyError:
            logging.getLogger().error("No contact points for grain " + 
                                str(grain_id) + " found.")
            cp_saddle_list = []
        barGraphData = {}
        for (neighbor_id, saddle_id) in cp_saddle_list:
            try:
                barGraphData[neighbor_id] = (contactstats.num_cells_contact_region(saddle_id, Config.CONTACT_REGION_DIR), 
                                             utils.get_color_particle(Config.PARTICLES_MESH_DIR + str(int(neighbor_id)) + ".vtp"))
            except FileNotFoundError:
                logging.getLogger().error("No contact region with " + 
                    str(saddle_id) + " for grain " + str(grain_id) + " found.")
                # barGraphData[neighbor_id] = (0, utils.get_color_particle(neighbor_id))
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("No corresponding contact region file found")
                msg.setInformativeText("Run the contact stats computation.")
                msg.setWindowTitle("Error")
                msg.exec()
                return

        plotgraph.main(plotgraph.Task({"data": barGraphData, "grain_id": grain_id}, 
                                            plotgraph.TaskType.CONTACT_AREA), self)

    def onToolbarMarkAction(self, s):
        """
        Mark particle for under segmentation.

        @param s: bool - True or False
        """

        # create folder
        if not os.path.exists(Config.UNDER_SEGMENTATION_DIR):
            os.makedirs(Config.UNDER_SEGMENTATION_DIR)

        try:
            fileutil.crop_undersegmented_particle(Config.RAW_IMAGE_FILE, \
                utils.read_file(Config.PC_DIR + "grain_" + str(self.files[self.curr_file].split(".")[0]) + '.vtp'), \
                Config.UNDER_SEGMENTATION_DIR + str(self.files[self.curr_file].split(".")[0]) + '.mhd')
        except AttributeError:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("No raw image file found.")
            msg.setInformativeText("Select the raw image file.")
            msg.setWindowTitle("No raw image file found.")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()
            return
        
        # success message box
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Marked for under segmentation.")
        msg.setInformativeText("The image has been saved to " + Config.UNDER_SEGMENTATION_DIR + ".")
        msg.setWindowTitle("Marked for under segmentation.")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def onSearchBarEnter(self):
        """
        Search for a particle.
        """
        for widget in self.tool_bar.children():
            if widget.objectName() == "search_bar":
                grain_id = widget.text()
                widget.setText("")
                break
        self.curr_file = self.files.index(grain_id + ".vtp")
        self.update_ui()

    def onToolbarExtremumGraphAction(self, s):
        """
        Display Extremum graph.

        @param s: bool - True or False
        """
        if self.showExtremumGraph:
            self.showExtremumGraph = False
            # code to remove tube actor
            for actor in self.ren.GetActors():
                if actor.GetProperty().GetMaterialName() == "graph":
                    self.ren.RemoveActor(actor)
        else:
            self.showExtremumGraph = True
            grain_id = int(self.files[self.curr_file].split(".")[0])
            self.ren.AddActor(actors.get_extremum_graph_actor(self.maxima_data[grain_id][0], \
                         self.contact_points[grain_id], self.maxima_data))
        self.iren.Render()

    def onToolbarViewAction(self, s):
        """
        Change the view type.
        Single particle view or multiple particle view.
        Or Multiple particle view to single particle view.
        """
        toolbar.update_slider(self.tool_bar, 100)
        if self.view_type == utils.ViewType.NEIGHBOR:
            if s == False:
                toolbar.update_ui(self, utils.ViewType.SINGLE)
                self.onToolbarViewAction(None)
                return
            grain_id = int(self.files[self.curr_file].split(".")[0])
            actors_list = []
            try:
                for contact_pt in self.contact_points[grain_id]:
                    if self.neighbor[contact_pt.sibling_cp_id][0]:
                        actors_list += utils.get_actors_list(self.maxima_data, self.contact_points, contact_pt.sibling_cp_id, self.ren, 
                                                             Config.PARTICLES_MESH_DIR + str(contact_pt.sibling_cp_id) + ".vtp", False)
            except KeyError:
                print("No contact points available")
            actors_list += utils.get_actors_list(self.maxima_data, self.contact_points, grain_id, self.ren,
                                                  Config.PARTICLES_MESH_DIR + str(grain_id) + ".vtp")
            self.update_actors(self.iren, actors_list)
        else:
            if s == False:
                toolbar.update_ui(self, utils.ViewType.NEIGHBOR)
                self.reset_iso_param()
                self.onToolbarViewAction(None)
                return
            grain_id = int(self.files[self.curr_file].split(".")[0])
            self.update_actors(self.iren, utils.get_actors_list(self.maxima_data, self.contact_points, 
                                                                grain_id, self.ren, Config.PARTICLES_MESH_DIR + str(grain_id) + ".vtp"))

        self.iren.Render()

    def update_neighbors(self):
        '''
        Update the neighbor dictionary.
        This dictionary contains the particle ids of the neighbors 
        and their visibility.
        '''
        # update the neighbor dictionary
        grain_id = int(self.files[self.curr_file].split(".")[0])
        self.neighbor = {}
        try:
            for neighbor in self.contact_points[grain_id]:
                if neighbor.sibling_cp_id not in self.neighbor.keys():
                    self.neighbor[neighbor.sibling_cp_id] = [True, utils.get_color_particle(Config.PARTICLES_MESH_DIR + str(int(neighbor.sibling_cp_id)) + ".vtp")]
        except KeyError:
            logging.getLogger().warning("KeyError: No contact points available for grain id " + str(grain_id))

    def key_press_event(self, obj, event):
        """
        Key press event - right arrow, left arrow, ...
        @param obj: vtkRenderWindowInteractor
        @param event: vtkEvent
        """
        key = obj.GetKeySym()

        # if key is c and view is single particle, mark as correct seg
        if key == 'c' and self.view_type == utils.ViewType.SINGLE:
            self.lable_particle(particleseg.Label.CORRECT_SEGMENTATION)
        if key == 'i' and self.view_type == utils.ViewType.SINGLE:
            self.lable_particle(particleseg.Label.INCORRECT_SEGMENTATION)

        if key == 'Escape':
            self.close()
        # right arrow
        elif key == 'Right':
            prev_curr_file = self.curr_file
            self.curr_file += 1
            grain_id = int(self.files[self.curr_file].split(".")[0])

            while self.is_particle_vol(grain_id) == False:
                self.curr_file += 1
                if self.curr_file >= len(self.files):
                    self.curr_file = len(self.files) - 1
                    break
                grain_id = int(self.files[self.curr_file].split(".")[0])

            if self.curr_file >= len(self.files):
                self.curr_file = prev_curr_file
            self.update_ui()

        elif key == 'Left':
            prev_curr_file = self.curr_file
            self.curr_file -= 1
            grain_id = int(self.files[self.curr_file].split(".")[0])

            while self.is_particle_vol(grain_id) == False:
                self.curr_file -= 1
                if self.curr_file < 0:
                    self.curr_file = 0
                    break
                grain_id = int(self.files[self.curr_file].split(".")[0])
            
            if self.curr_file < 0:
                self.curr_file = 0
            self.update_ui()
        
        # obj.Render()

        # update status bar
        self.statusBar().showMessage("index " + str(self.curr_file + 1) + " of " + str(len(self.files)))

    def update_ui(self):
        '''
        Update the UI and reset the widgets to default.
        '''
        if self.paritcle_info_dialog is not None:
            self.paritcle_info_dialog.close()
        if self.contact_area_bar_graph_dialog is not None:
            self.contact_area_bar_graph_dialog.close()
        self.show_simplified_saddle_actor = False

        # reset the iso surface actor
        self.reset_iso_param()
        self.update_neighbors()
        self.onToolbarViewAction(None)

    def reset_iso_param(self):
        '''
        Reset the iso surface parameters.
        '''
        self.iso_opacity = 1
        self.iso_show = False
        self.iso_value = 0.0

    def update_actors(self, input_interactor_renderer, actors_list):
        '''
        Update the actors (removes all the actors and adds the new ones).
        @param input_interactor_renderer: vtkRenderWindowInteractor
        @param actors_list: list(vtkActor)
        '''
        self.showContactRegion = False
        # remove all actors
        renderers = input_interactor_renderer.GetRenderWindow().GetRenderers()
        # for i in range(renderer.GetNumberOfItems()):
        #     print(renderer.GetItemAsObject(i))
        renderer_0 = renderers.GetItemAsObject(0)
        actors = renderer_0.GetActors()
        # print("removing actors length: ", actors.GetNumberOfItems())
        while actors.GetNumberOfItems() > 0:
            for actor in range(actors.GetNumberOfItems()):
                renderer_0.RemoveActor(actors.GetItemAsObject(actor))
            actors = renderer_0.GetActors()
        
        # remove PropAssembly
        prop_assembly = renderer_0.GetViewProps()
        while prop_assembly.GetNumberOfItems() > 0:
            for prop in range(prop_assembly.GetNumberOfItems()):
                renderer_0.RemoveViewProp(prop_assembly.GetItemAsObject(prop))
            prop_assembly = renderer_0.GetViewProps()
        
        # add new actors
        for actor in actors_list:
            renderer_0.AddActor(actor)
        
        # spatial map renderer - from all renderers, get the desired one
        spatial_map_renderer = renderers.GetItemAsObject(2)
        actors = spatial_map_renderer.GetActors()
        while True:
            check = False
            for actor in range(actors.GetNumberOfItems()):
                if actors.GetItemAsObject(actor) != None:
                    if actors.GetItemAsObject(actor).GetProperty().GetMaterialName() != None:
                        check = True
                        # remove actor
                        spatial_map_renderer.RemoveActor(actors.GetItemAsObject(actor))
            if not check:
                break
        for actor in actors_list:
            spatial_map_renderer.AddActor(actor)

        # reset camera
        renderer_0.ResetCamera()
        if self.view_type == utils.ViewType.SINGLE:
            renderer_0.GetActiveCamera().Zoom(0.5)

        grain_id = int(self.files[self.curr_file].split(".")[0])
        self.setWindowTitle("Particle with CP ID: " + str(grain_id))
        # status bar
        self.statusBar().showMessage("index " + str(self.curr_file + 1) + " of " + str(len(self.files)))

        self.update_particle_label_image(grain_id)

        # update lightings
        self.update_light_factor()

    def update_particle_label_image(self, grain_id):
        '''
        Update the particle label image.
        @param grain_id: int
        '''
        # update particle label image
        pl = self.particle_labels.get_particle_label(grain_id)
        if pl == particleseg.Label.INCORRECT_SEGMENTATION:
            toolbar.update_image_label(self.tool_bar, "red")
        elif pl == particleseg.Label.CORRECT_SEGMENTATION:
            toolbar.update_image_label(self.tool_bar, "green")
        elif pl == None:
            toolbar.update_image_label(self.tool_bar, "orange")

    def onShowClusterCheckboxChange(self, state):
        '''
        Show the cluster checkbox change
        @param state: int - 0 or 2
        '''
        res = toolbar.onShowClusterCheckboxChange(self, state)

        if res == 1:
            # restore the original view
            self.update_ui()

            # auto update the window size
            self.resize(self.sizeHint())

    def onClusterDropdownChange(self, index):
        '''
        Choosing the cluster(louvain clustering) to view
        @param index: int - cluster index
        '''
        if index == 0:
            return
        # get nodes from config.COMM_FOLDER + "cluster_" + str(index) + ".txt"
        cluster_file = Config.COMM_DIR + str(index-1) + ".txt"
        if not os.path.exists(cluster_file):
            return
        # parse [int, int, ...]
        nodes = []
        with open(cluster_file, 'r') as f:
            content = f.read()
            content = content.replace("[", "")
            content = content.replace("]", "")
            content = content.replace(" ", "")
            nodes = content.split(",")
            nodes = [int(node) for node in nodes]
        
        # print("nodes: ", nodes)

        actors = []
        for node in nodes:
            try:
                actors += utils.get_actors_list(self.maxima_data, self.contact_points, node, self.ren, 
                                                Config.PARTICLES_MESH_DIR + str(node) + ".vtp", isContacts=False)
            except Exception as e:
                pass

        # update scene
        self.update_actors(self.iren, actors)

        # update render window
        self.iren.Render()

    def lable_particle(self, l : particleseg.Label):
        '''
        Label the particle
        @param l: particleseg.Label - Correct or Incorrect
        '''
        grain_id = int(self.files[self.curr_file].split(".")[0])
        self.particle_labels.add_particle(l, grain_id)
        self.update_particle_label_image(grain_id)

    def closeEvent(self, event: QtGui.QCloseEvent):
        '''
        Close event

        @param event: QtGui.QCloseEvent
        '''
        self.particle_labels.save()
        
    def onShowBinderToggleButton(self):
        '''
        Display volume of input scalar file
        to show the binder
        '''
        
        if self.input_raw_data is None:
            for f in os.listdir(Config.INPUT_DIR):
                if f.endswith(".mhd"):
                    self.input_raw_data = utils.read_file(Config.INPUT_DIR + f)
                    # scalar range
                    self.scalar_range = self.input_raw_data.GetScalarRange()
                    self.selected_scalar_range = (None, None)
                    print("scalar range: ", self.scalar_range)
                    break
        if self.input_raw_data is None:
            QtWidgets.QMessageBox.critical(self, "Error", "No input file found in " 
                                        + Config.INPUT_DIR)
            return    

        self.binder_show = not self.binder_show

        if not self.binder_show:
            # remove the volume
            self.ren.RemoveVolume(self.volume)
            self.volume = None
            self.iren.Render()
            return
        extent = [float('inf'), float('-inf'), float('inf'), 
                float('-inf'), float('inf'), float('-inf')]
        # update extent to compare 
        for actor in self.ren.GetActors():
            actor_extent = actor.GetBounds()
            # x min max
            if actor_extent[0] < extent[0]:
                extent[0] = actor_extent[0]
            if actor_extent[1] > extent[1]:
                extent[1] = actor_extent[1]
            # y min max
            if actor_extent[2] < extent[2]:
                extent[2] = actor_extent[2]
            if actor_extent[3] > extent[3]:
                extent[3] = actor_extent[3]
            # z min max
            if actor_extent[4] < extent[4]:
                extent[4] = actor_extent[4]
            if actor_extent[5] > extent[5]:
                extent[5] = actor_extent[5]
        
        # print("extent: ", extent)
        self.actors_extent = extent

        if self.control_points:
            self.update_range(self.control_points)

    def update_range(self, control_points):
        '''
        Update the range of the scalar bar
        @param control_points: control points list
        '''
        if self.binder_show:

            self.control_points = control_points

            # if self.volume is not None:
            #     self.ren.RemoveVolume(self.volume)
            #     self.volume = None

            # print(self.input_raw_data.GetBounds())

            extract = vtk.vtkExtractVOI()
            extract.SetInputData(self.input_raw_data)
            extract.SetVOI(math.floor(self.actors_extent[0]), math.ceil(self.actors_extent[1]),
                            math.floor(self.actors_extent[2]), math.ceil(self.actors_extent[3]),
                            math.floor(self.actors_extent[4]), math.ceil(self.actors_extent[5]))
            extract.Update()

            # Create transfer mapping scalar value to opacity.
            opacityTransferFunction = vtk.vtkPiecewiseFunction()
            colorTransferFunction = vtk.vtkColorTransferFunction()
            
            # Create transfer mapping scalar value to color.
            # colorTransferFunction = vtk.vtkColorTransferFunction()
            # colorTransferFunction.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
            # colorTransferFunction.AddRGBPoint(64.0, 1.0, 0.0, 0.0)
            for pt in control_points:
                opacityTransferFunction.AddPoint(pt.x * self.scalar_range[1], pt.opacity)
                colorTransferFunction.AddRGBPoint(pt.x * self.scalar_range[1], 
                                                  pt.color[0], pt.color[1], pt.color[2])

            # The property describes how the data will look.
            volumeProperty = vtk.vtkVolumeProperty()
            volumeProperty.SetColor(colorTransferFunction)
            volumeProperty.SetScalarOpacity(opacityTransferFunction)
            volumeProperty.ShadeOn()
            volumeProperty.SetInterpolationTypeToLinear()

            # volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
            volumeMapper = vtk.vtkSmartVolumeMapper()
            # volumeMapper = vtk.vtkGPUVolumeRayCastMapper()
            volumeMapper.SetInputConnection(extract.GetOutputPort())

            # The volume holds the mapper and the property and
            # can be used to position/orient the volume.
            self.volume = vtk.vtkVolume()
            self.volume.SetMapper(volumeMapper)
            self.volume.SetProperty(volumeProperty)

            # add to renderer
            self.ren.AddVolume(self.volume)

            # update render window
            self.iren.Render()

    def update_vol_range(self, range):
        '''
        Update the volume range
        @param range: volume range
        '''
        self.vol_range = range

    def get_vol_bounds(self):
        '''
        Get the volume bounds
        @return: volume bounds
        '''
        if utils.check_file(Config.PARTICLE_STATS_FILE):
            return (self.vol.min(), self.vol.max())
        return self.vol_range
    
    def is_particle_vol(self, cp_id):
        '''
        Check if the volume is in the range
        @param cp_id: control point id
        @return: True if in range, False otherwise
        '''
        if utils.check_file(Config.PARTICLE_STATS_FILE):
            if self.vol_range[0] <= self.vol[cp_id] <= self.vol_range[1]:
                return True
            return False
        
        # if no particle stats file, render all particles
        return True


if __name__ == '__main__':
    print("You cannot run this file directly")


def main(parent=None):
    '''
    Create the single/multiple particle view window.

    @param parent: parent window
    '''
    dialog = Viewparticles(parent)
    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()