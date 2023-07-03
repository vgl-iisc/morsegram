import multiprocessing as mp
from PySide6.QtCore import QThread, Signal
from core import surface_reconstruction_bk, utils
import sys
import logging
from ui import misc_ui
import subprocess
import os


def set_spawn_method():
    """ Set spawn method for multiprocessing. """
    # mac
    if sys.platform == "darwin":
        mp.set_start_method('spawn', force=True)


def set_fork_method():
    """ Set spawn method for multiprocessing. """
    # mac
    if sys.platform == "darwin":
        mp.set_start_method('fork', force=True)


class NonDaemonProc(mp.Process):
    """ Non-daemon process. """

    def __init__(self, daemon=False):
        """
        :param to_emitter: pipe to communicate with parent process
        :param daemon: Boolean indicating whether process is daemon or not
        """
        super().__init__()
        self.daemon = daemon

    def add_task(self, task, *args):
        """
        Add task to process
        :param task: task to be executed
        :param args: arguments of task
        :return:
        """
        self.task = task
        self.args = args

    def run(self):
        """
        Run process
        :return:
        """
        self.task(*self.args)
        set_fork_method()


class ChildTask():
    """
    Task to be executed by child process
    with required parameters
    """

    def __init__(self, point_cloud, color, filename, display_progress, sr_method, surf_pc_dir, dem_dir, dest_dir, opts):
        """
        :param point_cloud: point cloud
        :param color: color
        :param filename: filename containing particle id
        :param display_progress: display progress
        :param sr_method: surface reconstruction method
        :param dest_dir: destination directory
        :param opts: options for surface reconstruction like alpha, mu, iterations
        """
        self.point_cloud = point_cloud
        self.color = color
        self.filename = filename
        self.display_progress = display_progress
        self.sr_method = sr_method
        self.dest_dir = dest_dir
        self.surf_pc_dir = surf_pc_dir
        self.dem_dir = dem_dir
        self.opts = opts


class Emitter(QThread):
    """ Emitter waits for data from child process and emits a signal to UI(parent) """
    ui_data_available = Signal(str)  # Signal indicating new UI data is available.

    def __init__(self, from_process: mp.Pipe):
        super().__init__()
        self.data_from_process = from_process

    def run(self):
        while True:
            try:
                text = self.data_from_process.recv()
            except EOFError:
                break
            else:
                self.ui_data_available.emit(text.decode('utf-8'))

    def stop(self):
        self.exit()
        self.terminate()


def sr_task():
    '''
        Surface reconstruction task
    '''
    global G_queue, C_pipe
    def proc_cb(obj, event):
        msg = '{},{}'.format(mp.current_process().pid, int(obj.GetProgress()*100))
        C_pipe.send(msg.encode('utf-8'))

    while True:
        task: ChildTask = G_queue.get()
        callback = None
        try:
            if surface_reconstruction_bk.SurfaceReconstructionMethod.VTK.name == task.sr_method:
                callback = proc_cb
            else:
                callback = C_pipe
            
            surface_reconstruction_bk.surface_reconstruction(task, callback)
        except Exception as e:
            logging.getLogger().error(e)


def water_tight_task():
    """
    Water tight task
    :return:
    """
    global G_queue, C_pipe

    while True:
        task_input = G_queue.get()

        if task_input.task_type == misc_ui.WaterTightTaskType.CHECK:
            polydata = utils.read_file(task_input.input_file)
            if utils.get_trimesh_from_polydata(polydata).is_watertight:
                msg = "wt|{}".format(task_input.input_file)
            else:
                msg = "nwt|{}".format(task_input.input_file)
        
        elif task_input.task_type == misc_ui.WaterTightTaskType.REPAIR:
            # cmd should change directory to core and run python3 make_water_tight.py --input <input_file>
            curr_file = os.path.abspath(__file__)
            curr_dir = os.path.dirname(curr_file)
            # os is windows
            if sys.platform == "win32":
                curr_dir = curr_dir.replace("\\", "/")
            # print(curr_dir)
            
            # Retrieve the path to the current virtual environment
            venv_path = sys.prefix

            # Generate the activation command based on the operating system
            if os.name == 'nt':
                # Windows
                activate_venv_cmd = os.path.join(venv_path, 'Scripts', 'activate.bat')
                activate_venv_cmd = activate_venv_cmd.replace("\\", "/")
                cmd = '"{}" && cd "{}" && python make_water_tight.py --input "{}"'\
                    .format(activate_venv_cmd, curr_dir, task_input.input_file)
            else:
                # Unix/Linux
                activate_venv_cmd = os.path.join(venv_path, 'bin', 'activate')

                cmd = '. "{}" && cd "{}" && python make_water_tight.py --input "{}"'\
                            .format(activate_venv_cmd, curr_dir, task_input.input_file)

            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(proc.stdout, proc.stderr)

            # utils.make_watertight(task_input.input_file)
            msg = "repair"

        C_pipe.send(msg.encode('utf-8'))


def proc_init(child_pipe, queue):
    """
    Initialize child process
    :param child_pipe: pipe to communicate with parent process
    :param queue: queue to store tasks
    :return:
    """
    global C_pipe
    global G_queue
    C_pipe = child_pipe
    G_queue = queue


class MultiProc():
    """
    Multi process class
    creates a pool of processes and provides methods to add tasks
    """
    def __init__(self, pipe=None, queue=None, num_procs=None):
        """
        :param pipe: pipe to communicate with parent process
        :param queue: queue to store tasks
        :param num_procs: number of processes
        """
        self.pipe = pipe
        self.queue = queue
        self.num_procs = mp.cpu_count() if num_procs is None else num_procs
        try:
            if hasattr(self, 'pool') and self.pool is not None:
                self.close()
            self.pool = mp.Pool(self.num_procs, initializer=proc_init, initargs=(self.pipe, self.queue))
        except Exception as e:
            print(e)

        self.proc_id_dict = {}
        for i, proc in enumerate(self.pool._pool):
            self.proc_id_dict[proc.pid] = i

    def add_task(self, func, *args):
        """
        Add task to pool
        :param func: function to be executed
        :param args: arguments of function
        :return:
        """
        return self.pool.apply_async(func, args)

    def close(self):
        """
        Close pool
        :return:
        """
        self.pool.close()
        self.pool.terminate()
        self.pool.join()

    def get_num_procs(self):
        """
        Get number of processes
        :return:
        """
        return self.num_procs


