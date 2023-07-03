import core.utils as utils
import vtk
import time
import distinctipy
import os
import logging
from settings import Config
import datetime
from PySide6 import QtWidgets, QtCore, QtGui
from core import particlestats, contactstats
from core import multiproc
from ui import clean_data, form_nav
from core import cleandata
from core import simplified_cps
from core.multiproc import ChildTask
import pyqtgraph as pg
import numpy as np
import error_msgs
from core import surface_reconstruction_bk
from core import ensembleinfo


def vol_hist_task(pipe):
    """
    Show the histogram of particle sizes(volume)

    @param pipe: pipe to communicate with the parent process
    """
    # Read a vtp file and return a vtkPolyData object.
    file_data = utils.read_file(Config.SEGMENTATION_FILE)
    print("Data is a Object of type: ", file_data.GetClassName())
    utils.print_all_arrays_point_data(file_data)
    utils.print_all_arrays_cell_data(file_data)
    
    # grains point cloud
    grains_pc = utils.get_grains_point_cloud(file_data)
    vol_data = [len(pc) for pc in grains_pc.values()]

    min_val , max_val = min(vol_data), max(vol_data)
    bins = np.linspace(min_val, max_val, len(vol_data) // 100)

    # save data to file
    np.savetxt(Config.VOL_DATA, vol_data, fmt="%d")
    np.savetxt(Config.VOL_BINS, bins, fmt="%d")

    pipe.send(("display_hist").encode("utf-8"))


def perform_clean_data_task(vol_cutoff, pipe):
    """
    Perform data cleaning - filtering particles based on volume

    @param vol_cutoff: volume cutoff
    @param pipe: pipe to communicate with the parent process
    """
    grains_pc = utils.get_grains_point_cloud(utils.read_file(Config.SEGMENTATION_FILE))
    cd_obj = cleandata.CleanData(vol_cutoff, [k for k, v in grains_pc.items() if len(v) <= vol_cutoff])
    cd_obj.save()
    pipe.send(("clean_data").encode("utf-8"))


def surface_reconstruction_form(parent_ref) -> form_nav.Form:
    '''
    Create the Surface Reconstruction form

    @param parent_ref: reference to parent
    @return: form
    '''
    form = form_nav.Form("Surface Reconstruction")

    form.form_widget = QtWidgets.QScrollArea()
    form.form_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
    form.form_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    form.form_widget.setWidgetResizable(True)

    vl = QtWidgets.QVBoxLayout()
    # heading label - Surface Reconstruction
    heading_label = QtWidgets.QLabel("Surface Reconstruction")
    heading_label.setStyleSheet("font-size: 20px; font-weight: bold;")
    # align the heading label to the center
    heading_label.setAlignment(QtCore.Qt.AlignCenter)
    vl.addWidget(heading_label)


    hl = QtWidgets.QHBoxLayout()
    button = QtWidgets.QPushButton("Start")

    # button size
    # self.button.setFixedSize(QtCore.QSize(100, 40))
    button.clicked.connect(parent_ref.start_process)
    hl.addWidget(button, alignment=QtCore.Qt.AlignCenter)
    
    parent_ref.toggled = QtWidgets.QCheckBox("Display progress of each process")
    parent_ref.toggled.setChecked(True)
    vl.addWidget(parent_ref.toggled, alignment=QtCore.Qt.AlignCenter)
    vl.addLayout(hl)

    hl = QtWidgets.QHBoxLayout()
    # add dropdown menu to choose surface reconstruction method
    label = QtWidgets.QLabel("Use Surface Reconstruction method from :")
    hl.addWidget(label, alignment=QtCore.Qt.AlignRight)
    
    parent_ref.sr_method = QtWidgets.QComboBox()
    sr_methods = []
    # iterate over enum surface reconstruction_bk.SurfaceReconstructionMethod
    for method in surface_reconstruction_bk.SurfaceReconstructionMethod:
        sr_methods.append(method.name)
    parent_ref.sr_method.addItems(sr_methods)
    parent_ref.sr_method.setCurrentIndex(0)
    # parent_ref.sr_method.currentIndexChanged.connect(parent_ref.sr_method_changed)
    hl.addWidget(parent_ref.sr_method, alignment=QtCore.Qt.AlignLeft)
    vl.addLayout(hl)

    # advanced options
    parent_ref.advanced_options = QtWidgets.QPushButton("Advanced Options")
    parent_ref.advanced_options.setFixedSize(QtCore.QSize(200, 40))
    parent_ref.advanced_options.clicked.connect(parent_ref.show_advanced_options)
    vl.addWidget(parent_ref.advanced_options, alignment=QtCore.Qt.AlignCenter)


    hl = QtWidgets.QHBoxLayout()
    # label for time execution
    time_label = QtWidgets.QLabel("Time:")
    hl.addWidget(time_label, alignment=QtCore.Qt.AlignRight)
    parent_ref.time_exec = QtWidgets.QLabel("0")
    hl.addWidget(parent_ref.time_exec, alignment=QtCore.Qt.AlignLeft)
    vl.addLayout(hl)

    # vertical layout (Label and Progress Bar)
    hl = QtWidgets.QHBoxLayout()
    label = QtWidgets.QLabel("Overall Progress")
    hl.addWidget(label, alignment=QtCore.Qt.AlignRight)
    # progress bar for overall progress
    parent_ref.overall_progress = QtWidgets.QProgressBar()
    parent_ref.overall_progress.setMinimum(0)
    parent_ref.overall_progress.setMaximum(100)
    hl.addWidget(parent_ref.overall_progress, alignment=QtCore.Qt.AlignLeft)
    vl.addLayout(hl)

    # button to merge all the grains
    parent_ref.merge_button = QtWidgets.QPushButton("Merge All Grains")
    # size of the button
    parent_ref.merge_button.setFixedSize(QtCore.QSize(200, 40))
    parent_ref.merge_button.clicked.connect(parent_ref.merge_particles)
    # disable the button until all the grains are triangulated
    parent_ref.merge_button.setEnabled(False)
    vl.addWidget(parent_ref.merge_button, alignment=QtCore.Qt.AlignCenter)

    # horizontal line
    hline = QtWidgets.QFrame()
    hline.setFrameShape(QtWidgets.QFrame.HLine)
    hline.setFrameShadow(QtWidgets.QFrame.Sunken)
    vl.addWidget(hline)

    parent_ref.sr_ui_vl = vl

    wd = QtWidgets.QWidget()
    wd.setLayout(vl)

    form.form_widget.setWidget(wd)

    return form


def contact_stats_form(parent_ref) -> form_nav.Form:
    '''
    Create the contact statistics form

    @param parent_ref: reference to parent
    @return: form
    '''
    f = form_nav.Form("Contact Statistics")
    f.form_widget = QtWidgets.QWidget()
    
    vl = QtWidgets.QVBoxLayout()

    # Compute the contact statistics
    add_button = QtWidgets.QPushButton("Compute Contact Statistics")
    add_button.clicked.connect(parent_ref.contact_stat)

    vl.addWidget(add_button)

    # progress bar for contact statistics
    parent_ref.contact_progress = QtWidgets.QProgressBar()
    parent_ref.contact_progress.setMinimum(0)
    parent_ref.contact_progress.setMaximum(100)
    vl.addWidget(parent_ref.contact_progress)

    f.form_widget.setLayout(vl)

    return f


def particle_stats_form(parent_ref) -> form_nav.Form:
    '''
    Create the particle statistics form

    @param parent_ref: reference to parent
    @return: form
    '''
    f = form_nav.Form("Particle Statistics")
    f.form_widget = QtWidgets.QWidget()

    vl = QtWidgets.QVBoxLayout()

    # check box to select noise particles
    parent_ref.noise_particles = QtWidgets.QCheckBox("Noise Particles")
    parent_ref.noise_particles.setChecked(True)
    vl.addWidget(parent_ref.noise_particles)

    # Compute the particle statistics
    add_button = QtWidgets.QPushButton("Compute Particle Statistics")
    add_button.clicked.connect(parent_ref.particle_stat)
    vl.addWidget(add_button)

    # progress bar for particle statistics
    parent_ref.particle_progress = QtWidgets.QProgressBar()
    parent_ref.particle_progress.setMinimum(0)
    parent_ref.particle_progress.setMaximum(100)
    vl.addWidget(parent_ref.particle_progress)

    f.form_widget.setLayout(vl)

    return f


def simplified_cps_form(parent_ref) -> form_nav.Form:
    '''
    Create the simplified contact points form

    @param parent_ref: reference to parent
    @return: form
    '''
    f = form_nav.Form("Simplified Contact Points")
    f.form_widget = QtWidgets.QWidget()
    
    vl = QtWidgets.QVBoxLayout()
    # Compute the simplified contact points
    add_button = QtWidgets.QPushButton("Compute Simplified Contact Points")
    add_button.clicked.connect(parent_ref.simplified_cps)
    vl.addWidget(add_button)

    # progress bar for particle statistics
    parent_ref.sim_sad_progress = QtWidgets.QProgressBar()
    parent_ref.sim_sad_progress.setMinimum(0)
    parent_ref.sim_sad_progress.setMaximum(100)
    vl.addWidget(parent_ref.sim_sad_progress)

    f.form_widget.setLayout(vl)

    return f


def perform_cleaning_form(parent_ref) -> form_nav.Form:
    '''
    Create the perform cleaning form

    @param parent_ref: reference to parent
    @return: form
    '''
    f = form_nav.Form("Perform Cleaning")
    f.form_widget = QtWidgets.QWidget()
    clean_data_ui = clean_data.get_ui(parent_ref.init_clean_data, 
                                                parent_ref.perform_clean_data)
    f.form_widget.setLayout(clean_data_ui[0])
    parent_ref.vol_cutoff_input = clean_data_ui[1]
    return f


def get_progressbars(parent_ref):
    '''
    Get the progress bars

    @param parent_ref: reference to parent
    '''
    widget = QtWidgets.QWidget()
    vl = QtWidgets.QVBoxLayout()
    parent_ref.progressbar = []
    for i in range(parent_ref.proc_pool.get_num_procs()):
        hl = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Process " + str(i + 1) + "\t")
        parent_ref.progressbar.append(QtWidgets.QProgressBar())
        parent_ref.progressbar[i].setMinimum(0)
        parent_ref.progressbar[i].setMaximum(100)
        parent_ref.progressbar[i].setValue(0)
        hl.addWidget(label)
        hl.addWidget(parent_ref.progressbar[i])
        vl.addLayout(hl)

    widget.setLayout(vl)
    return widget


class SurfaceReconstructionForm(form_nav.Form_Nav):
    '''
    this window is used to perform surface reconstruction,
    compute contact statistics and particle statistics and 
    cleaning the dataset, so on
    '''

    def __init__(self, parent=None):
        '''
        Initialize the Surface Reconstruction window

        @param parent: parent widget
        '''
        super().__init__("Surface Reconstruction", parent)

        # ref to parent
        self.parent_ref = parent
        self.sr_method : QtWidgets.QComboBox = None
        self.progressbars_widget = None

        # Meshlab parameters
        self.ML_ALPHA = 0.5
        self.ML_MU = -0.43
        self.ML_ITERATIONS = 100

        # VTK parameters
        self.VTK_ALPHA = 3.0
        self.VTK_ITERATIONS = 20

        self.add_form(surface_reconstruction_form(self))
        self.add_form(contact_stats_form(self))
        self.add_form(particle_stats_form(self))
        self.add_form(simplified_cps_form(self))
        self.add_form(perform_cleaning_form(self))

    def simplified_cps(self):
        '''
        this function generates the simplified saddle points
        '''
        if self.proc_pool is not None:
            self.proc_pool.close()
        if hasattr(Config, "ALL_CONTACTS_FILE"):
            self.proc_pool = multiproc.MultiProc(self.child_conn, self.queue, 1)
            self.proc_pool.add_task(simplified_cps.generate_simplified_maximas,
                                    self.child_conn,
                                    Config.ALL_CONTACTS_FILE,
                                    Config.PARTICLES_MESH_DIR,
                                    Config.SIMPLIFIED_DIR)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Error computing particle statistics\n" +
                                            "There is no all contacts file.")

    def particle_stat_all(self):
        '''
        this function computes the particle statistics for all the grains
        '''
        pcs = utils.get_grains_point_cloud(utils.read_file(Config.SEGMENTATION_FILE))
        contact_points = utils.get_contact_network(utils.read_file(Config.CONTACT_NET_FILE))
        try:
            particlestats.compute_particle_stats(pcs, contact_points, noisy=True)
            QtWidgets.QMessageBox.information(self, "Particle Statistics", "Particle statistics computed")
        except Exception as e:
            print(e, type(e))
            QtWidgets.QMessageBox.warning(self, "Error", "Error computing particle statistics")

    def particle_stat(self):
        '''
        Compute particle statistics
        '''

        # warning box
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText("Make sure all particle meshs are water tight.\n" +
                    "If not, the particle statistics will not be computed correctly.\n" +
                    "you can use the miscellanous tools to check if the mesh is water tight and repair it.")
        msg.setInformativeText("Do you want to continue?")
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        retval = msg.exec_()

        if retval == QtWidgets.QMessageBox.No:
            return

        check_sr = True # flag to check if surface reconstruction is done
        try:
            files = os.listdir(Config.PARTICLES_MESH_DIR)
            if len(files) == 0:
               check_sr = False
        except FileNotFoundError:
            check_sr = False
        
        if not check_sr:
            QtWidgets.QMessageBox.warning(self, "Error", error_msgs.SR_MSG)
            return

        contact_points = utils.get_contact_network(utils.read_file(Config.CONTACT_NET_FILE))
        try:
            multiproc.set_spawn_method()
            if self.proc_pool is not None:
                self.proc_pool.close()
            non_daemon_proc = multiproc.NonDaemonProc()
            non_daemon_proc.add_task(particlestats.compute_particle_stats, 
                                     contact_points,
                                     self.child_conn,
                                     Config.SEGMENTATION_FILE,
                                     Config.PC_DIR,
                                     Config.PARTICLE_STATS_FILE,
                                     Config.DATA_DIR,
                                     Config.PARTICLES_MESH_DIR,
                                     self.noise_particles.isChecked())
            non_daemon_proc.start()
        except Exception as e:
            print(e, type(e))
            QtWidgets.QMessageBox.warning(self, "Error", "Error computing particle statistics")

    def contact_stat(self):
        '''
        Compute contact statistics
        '''
        try:
            if self.proc_pool is not None:
                self.proc_pool.close()
                
            self.proc_pool = multiproc.MultiProc(self.child_conn, self.queue, 1)
            self.proc_pool.add_task(contactstats.generate_contact_region, self.child_conn, 
                                    Config.CONTACT_REGION_FILE,
                                    Config.CONTACT_NET_FILE, 
                                    Config.CONTACT_REGION_DIR, 
                                    Config.DATA_DIR)
        except Exception as e:
            print(e)
            QtWidgets.QMessageBox.warning(self, "Error", "Error computing contact statistics")

    def init_clean_data(self):
        '''
        Initialize the clean data
        '''
        if (os.path.exists(Config.VOL_BINS) and os.path.exists(Config.VOL_DATA)):

            # display dialog to ask whether to use the existing data or not
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Question)
            msg.setText("Do you want to use the existing histogram data?")
            # msg.setInformativeText("")
            msg.setWindowTitle("Data Cleaning")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
            ret = msg.exec_()

            if ret == QtWidgets.QMessageBox.Yes:
                self.display_hist()
                return
            
        try:
            if self.proc_pool is not None:
                self.proc_pool.close()
            self.proc_pool = multiproc.MultiProc(self.child_conn, self.queue, 1)
            self.proc_pool.add_task(vol_hist_task, self.child_conn)
        except Exception as e:
            logging.getLogger("SurfaceReconstructionForm").error("Error perform data cleaning")
            QtWidgets.QMessageBox.warning(self, "Error", "Error perform data cleaning")

    def merge_particles(self, isClean=False):
        '''
        Merge all the particles

        @param isClean: flag to check if the data is cleaned
        '''
        # disable the button until all the grains are triangulated
        self.merge_button.setEnabled(False)
        triangulated_particles = []
        try:
            for file in os.listdir(Config.PARTICLES_MESH_DIR):
                triangulated_particles.append(int(file.split(".")[0]))
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, "Error", error_msgs.SR_MSG)
            return

        if not isClean and len(triangulated_particles) != len(self.list_cp):
            # warning box
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("Not all grains have been triangulated.\n" +
                        "Only " + str(len(triangulated_particles)) + " out of " + str(len(self.list_cp)) + " grains have been triangulated.")
            msg.setInformativeText("Do you want to merge all the grains?")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            retval = msg.exec_()
            if retval == QtWidgets.QMessageBox.No:
                self.merge_button.setEnabled(True)
                return
        
        if isClean:
            error_grains = cleandata.CleanData()
            error_grains.load()

            for cp_id in error_grains.cp_ids:
                triangulated_particles.remove(cp_id)

        # merge all the grains
        appendFilter = vtk.vtkAppendFilter()
        for i in triangulated_particles:
            appendFilter.AddInputData(utils.read_file(Config.PARTICLES_MESH_DIR + str(i).split(".")[0] + ".vtp"))
        appendFilter.Update()
        # write the unstructured grid to a file
        writer = vtk.vtkXMLUnstructuredGridWriter()
        if isClean:
            writer.SetFileName(Config.ENSEMBLE_CLEAN_FILE)
        else:
            writer.SetFileName(Config.ENSEMBLE_FILE)
        writer.SetInputConnection(appendFilter.GetOutputPort())
        writer.Write()
        logging.getLogger().info("Merged all the grains")

        # update the ensemble info file
        ens_bounds = appendFilter.GetOutput().GetBounds()
        ens_info = ensembleinfo.EnsembleInfo().load()
        # update length, width, height
        ens_info.length = ens_bounds[1] - ens_bounds[0]
        ens_info.width = ens_bounds[3] - ens_bounds[2]
        ens_info.height = ens_bounds[5] - ens_bounds[4]
        seg_file = (Config.SEGMENTATION_FILE).split("/")[-1]
        # remove chamf_distance_
        if seg_file.find("chamf_distance_") != -1:
            seg_file = seg_file.replace("chamf_distance_", "")
        # remove _segmentation.vtp
        if seg_file.find("_segmentation.vtp") != -1:
            seg_file = seg_file.replace("_segmentation.vtp", "")
        ens_info.dataset_name = seg_file
        # read txt file
        pers_val = 0
        with open(Config.PERS_VAL_FILE, "r") as f:
            pers_val = float(f.readline())
        ens_info.pers_val = pers_val
        ens_info.save()

        # display message box
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Merge completed")
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

        # enable the button again
        self.merge_button.setEnabled(True)

    def start_process(self):
        '''
        Start the processes
        '''
        
        enseminfo = ensembleinfo.EnsembleInfo.load()

        # voxel and meshlab
        for folder in [Config.DEM_DIR, Config.SURFACE_PC_DIR]:
            if not os.path.exists(folder):
                os.makedirs(folder)

        multiproc.set_fork_method()
        is_seg_data = False # flag to check if segmentation data is available

        if not os.path.exists(Config.PC_DIR):
            # no point cloud data, reading segmentation data
            # check if self contains grains_pc attribute
            if not hasattr(self, 'grains_pc'):
                self.grains_pc = utils.get_grains_point_cloud(utils.read_file(Config.SEGMENTATION_FILE))
            is_seg_data = True
            grain_ids = self.grains_pc.keys()
        else:
            # read the point cloud data
            grain_ids = []
            for file in os.listdir(Config.PC_DIR):
                # file - grain_123.vtp
                grain_ids.append(int(file.split("_")[1].split(".")[0]))

        N = len(grain_ids)
        enseminfo.num_particles = N
        enseminfo.save()

        # read the already triangulated grains file in config.GRAINS_DIR
        triangulated_grains = []
        # check if folder exists
        if not os.path.exists(Config.PARTICLES_MESH_DIR):
            os.makedirs(Config.PARTICLES_MESH_DIR)
        for file in os.listdir(Config.PARTICLES_MESH_DIR):
            triangulated_grains.append(int(file.split(".")[0]))

        print("Total number of grains: ", N)
        print("Number of already triangulated grains: ", len(triangulated_grains))

        self.num_of_grains = N

        max_cp = max(grain_ids)
        self.list_cp = list(grain_ids)
        for i in range(N):
            
            curr_cp = self.list_cp[i]
            if curr_cp not in triangulated_grains:

                # log the current critical point being processed
                logging.getLogger().info("Current critical point / Particle's CP ID : " + str(curr_cp))
                color = distinctipy.get_rgb256(distinctipy.get_random_color(float(curr_cp)/max_cp))

                pc_filename = Config.PC_DIR + "grain_" + str(curr_cp) + ".vtp"
                
                # create task and add to the queue
                grain_pc = None
                if is_seg_data:
                    grain_pc = self.grains_pc[curr_cp]
                
                curr_sr_method = self.sr_method.currentText()

                options = {}
                if curr_sr_method == surface_reconstruction_bk.SurfaceReconstructionMethod.VTK.name:
                    options["alpha"] = self.VTK_ALPHA
                    options["iters"] = self.VTK_ITERATIONS
                else:
                    options["lambda"] = self.ML_ALPHA
                    options["mu"] = self.ML_MU
                    options["iters"] = self.ML_ITERATIONS

                self.queue.put(ChildTask(grain_pc, color,
                                         pc_filename,
                                         self.toggled.isChecked(), 
                                         curr_sr_method, 
                                         Config.SURFACE_PC_DIR,
                                         Config.DEM_DIR,
                                         Config.PARTICLES_MESH_DIR,
                                         options))

            # remove the grain from the grains_pc
            if is_seg_data:
                del self.grains_pc[curr_cp]
        
        self.merge_button.setEnabled(True)
        prog = int(100 * (len(triangulated_grains) / N))
        self.overall_progress.setValue(prog)
        if prog == 100:
                self.overall_progress.setStyleSheet(self.success_styleSheet)
        else:
            if self.proc_pool is not None:
                self.proc_pool.close()
            self.proc_pool = multiproc.MultiProc(self.child_conn, self.queue)
            
            if  self.toggled.isChecked():
                if self.progressbars_widget is not None:
                    self.progressbars_widget.deleteLater()
                    self.progressbars_widget = None
                self.progressbars_widget = get_progressbars(self)    
                self.sr_ui_vl.addWidget(self.progressbars_widget)
            self.start_time = time.time()

            # start the processes
            for p in range(self.proc_pool.get_num_procs()):
                self.proc_pool.add_task(multiproc.sr_task)

    def updateUI(self, text:str):
        '''
        Update the progress bar

        @param text: text to be parsed
        '''
        if "Error" in text:
            QtWidgets.QMessageBox.critical(self, "Error", text)
        elif text == "display_hist":
            self.display_hist()
        elif text == "clean_data":
            msg_box = QtWidgets.QMessageBox()
            msg_box.setText("Data cleaned successfully")
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.exec()

            # update the clean data ui to include generate new ensemble button
            self.get_clean_data_ui()
        elif text.startswith("cs"):
            text = text[2:]
            prog = int(text)
            self.contact_progress.setValue(prog)
            if prog == 100:
                self.contact_progress.setStyleSheet(self.success_styleSheet)
                QtWidgets.QMessageBox.information(self, "Information", "Contact stats computation completed")
        elif text.startswith("ps"):
            text = text[2:]
            prog = int(text)
            self.particle_progress.setValue(prog)
            if prog == 100:
                self.particle_progress.setStyleSheet(self.success_styleSheet)
                QtWidgets.QMessageBox.information(self, "Information", "Particle stats computation completed")
        elif text.startswith("sd"):
            text = text[2:]
            prog = int(text)
            self.sim_sad_progress.setValue(prog)
            if prog == 100:
                self.sim_sad_progress.setStyleSheet(self.success_styleSheet)
                QtWidgets.QMessageBox.information(self, "Information", "Simplified Saddle computation completed")
        else:

            curr_time = time.time() - self.start_time
            self.time_exec.setText(str(datetime.timedelta(seconds=curr_time)))
            c_id, value = text.split(',')
            if self.toggled.isChecked():
                self.progressbar[self.proc_pool.proc_id_dict[int(c_id)]-1].setValue(int(value))
            try:
                prog = int((self.num_of_grains - self.queue.qsize()) * 100 / self.num_of_grains)
                self.overall_progress.setValue(prog)
                if prog == 100:
                    self.overall_progress.setStyleSheet(self.success_styleSheet)
            except NotImplementedError:
                pass

    def perform_clean_data(self):
        '''
        Clean the data
        '''
        try:
            if self.vol_cutoff_input.text() == "":
                raise ValueError
            
            if self.proc_pool is not None:
                self.proc_pool.close()

            self.proc_pool = multiproc.MultiProc(self.child_conn, self.queue, 1)
            self.proc_pool.add_task(perform_clean_data_task, int(self.vol_cutoff_input.text()), self.child_conn)
        except ValueError:
            msg_box = QtWidgets.QMessageBox()
            # warning message
            msg_box.setText("See the histogram and then enter the volume cutoff")
            # icon
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.exec()
            return

    def get_clean_data_ui(self):
        '''
        Get the clean data ui
        '''
        
        f = self.get_form("Perform Cleaning")
        if os.path.exists(Config.CLEAN_DATA_FILE):
            # Generate new ensemble button
            generate_new_ensemble_button = QtWidgets.QPushButton("Generate Ensemble from Cleaned Data")
            # fix the size of the button
            generate_new_ensemble_button.setFixedWidth(300)
            generate_new_ensemble_button.clicked.connect(self.merge_grains_cleaned)
            f.form_widget.layout().addWidget(generate_new_ensemble_button, alignment=QtCore.Qt.AlignCenter)

    def merge_grains_cleaned(self):
        '''
        Merge the grains after cleaning the data
        '''
        self.merge_particles(isClean=True)

    def display_hist(self):
        win = pg.plot()
        win.setWindowTitle("Clean Data")
        # plt1 = win.addPlot()
        # adding legend
        win.addLegend()
        # set properties of the label for y axis
        win.setLabel('left', 'Number of grains', 'Grains')
        # set properties of the label for x axis
        win.setLabel('bottom', 'Volume', 'Voxels')

        vol_data = np.loadtxt(Config.VOL_DATA)
        bins = np.loadtxt(Config.VOL_BINS)

        # update the x and y axis
        hist_data = np.histogram(vol_data, bins=bins)

        y = hist_data[0]
        x = hist_data[1]

        win.plot(x, y, stepMode=True, fillLevel=0, brush=(0,0,255,150))

    def show_advanced_options(self):
        '''
        Show the advanced options
        '''
        if self.sr_method.currentText() == surface_reconstruction_bk.SurfaceReconstructionMethod.VOXEL.name:
            # dialog with alpha, beta, iterations values
            dialog = QtWidgets.QDialog()
            dialog.setWindowTitle("Advanced Options")
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.resize(200, 180)
            dialog.setLayout(QtWidgets.QVBoxLayout())

            # alpha
            alpha_label = QtWidgets.QLabel("Lambda")
            alpha_input = QtWidgets.QLineEdit()
            alpha_input.setText(str(self.ML_ALPHA))
            alpha_input.setValidator(QtGui.QDoubleValidator())
            alpha_input.setFixedWidth(50)
            alpha_input.setFixedHeight(30)
            alpha_input.textChanged.connect(lambda: self.update_alpha(alpha_input.text()))

            # beta
            beta_label = QtWidgets.QLabel("Mu")
            beta_input = QtWidgets.QLineEdit()
            beta_input.setText(str(self.ML_MU))
            beta_input.setValidator(QtGui.QDoubleValidator())
            beta_input.setFixedWidth(50)
            beta_input.setFixedHeight(30)
            beta_input.textChanged.connect(lambda: self.update_mu(beta_input.text()))

            # iterations
            iterations_label = QtWidgets.QLabel("Iterations")
            iterations_input = QtWidgets.QLineEdit()
            iterations_input.setText(str(self.ML_ITERATIONS))
            iterations_input.setValidator(QtGui.QIntValidator())
            iterations_input.setFixedWidth(50)
            iterations_input.setFixedHeight(30)
            iterations_input.textChanged.connect(lambda: self.update_iterations(iterations_input.text()))

            # add the widgets to the layout
            hl = QtWidgets.QHBoxLayout()
            hl.addWidget(alpha_label, alignment=QtCore.Qt.AlignCenter)
            hl.addWidget(alpha_input, alignment=QtCore.Qt.AlignLeft)
            dialog.layout().addLayout(hl)

            hl = QtWidgets.QHBoxLayout()
            hl.addWidget(beta_label, alignment=QtCore.Qt.AlignCenter)
            hl.addWidget(beta_input, alignment=QtCore.Qt.AlignLeft)
            dialog.layout().addLayout(hl)

            hl = QtWidgets.QHBoxLayout()
            hl.addWidget(iterations_label, alignment=QtCore.Qt.AlignCenter)
            hl.addWidget(iterations_input, alignment=QtCore.Qt.AlignLeft)
            dialog.layout().addLayout(hl)

            # ok button
            ok_button = QtWidgets.QPushButton("OK")
            ok_button.clicked.connect(dialog.close)
            dialog.layout().addWidget(ok_button, alignment=QtCore.Qt.AlignCenter)

            dialog.exec()
        
        elif self.sr_method.currentText() == surface_reconstruction_bk.SurfaceReconstructionMethod.VTK.name:
            # dialog with alpha
            dialog = QtWidgets.QDialog()
            dialog.setWindowTitle("Advanced Options")
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.resize(200, 180)
            dialog.setLayout(QtWidgets.QVBoxLayout())

            # alpha
            alpha_label = QtWidgets.QLabel("Alpha")
            alpha_input = QtWidgets.QLineEdit()
            alpha_input.setText(str(self.VTK_ALPHA))
            alpha_input.setValidator(QtGui.QDoubleValidator())
            alpha_input.setFixedWidth(50)
            alpha_input.setFixedHeight(30)
            alpha_input.textChanged.connect(lambda: self.update_vtk_alpha(alpha_input.text()))

            # iterations
            iterations_label = QtWidgets.QLabel("Iterations")
            iterations_input = QtWidgets.QLineEdit()
            iterations_input.setText(str(self.VTK_ITERATIONS))
            iterations_input.setValidator(QtGui.QIntValidator())
            iterations_input.setFixedWidth(50)
            iterations_input.setFixedHeight(30)
            iterations_input.textChanged.connect(lambda: self.update_vtk_iterations(iterations_input.text()))

            # add the widgets to the layout
            hl = QtWidgets.QHBoxLayout()
            hl.addWidget(alpha_label, alignment=QtCore.Qt.AlignCenter)
            hl.addWidget(alpha_input, alignment=QtCore.Qt.AlignLeft)
            dialog.layout().addLayout(hl)

            hl = QtWidgets.QHBoxLayout()
            hl.addWidget(iterations_label, alignment=QtCore.Qt.AlignCenter)
            hl.addWidget(iterations_input, alignment=QtCore.Qt.AlignLeft)
            dialog.layout().addLayout(hl)

            # ok button
            ok_button = QtWidgets.QPushButton("OK")
            ok_button.clicked.connect(dialog.close)
            dialog.layout().addWidget(ok_button, alignment=QtCore.Qt.AlignCenter)

            dialog.exec()

    def update_vtk_iterations(self, iterations):
        '''
        Update the iterations value
        '''
        self.VTK_ITERATIONS = int(iterations)

    def update_vtk_alpha(self, alpha):
        '''
        Update the alpha value
        '''
        self.VTK_ALPHA = float(alpha)

    def update_alpha(self, alpha):
        '''
        Update the alpha value
        '''
        self.ML_ALPHA = float(alpha)

    def update_mu(self, mu):
        '''
        Update the mu value
        '''
        self.ML_MU = float(mu)

    def update_iterations(self, iterations):
        '''
        Update the iterations value
        '''
        self.ML_ITERATIONS = int(iterations)



if __name__ == '__main__':
    print("You cannot run this file directly")


def main(parent=None):
    '''
    Open the Surface Reconstruction dialog

    @param parent: parent widget
    '''

    dialog = SurfaceReconstructionForm(parent)

    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()