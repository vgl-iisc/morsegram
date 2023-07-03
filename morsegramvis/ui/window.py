from PySide6 import QtWidgets, QtGui, QtCore
from settings import Config
from ui import cam_setting_dialog
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk


def encode_cam_info(pos, fp, vu, va):
    """
    Encode the camera info into a string.

    :param pos: camera position
    :param fp: camera focal point
    :param vu: camera view up
    :param va: camera view angle
    :return: encoded string
    """
    return str({
                "position": pos,
                "focal_point": fp,
                "view_up": vu,
                "view_angle": va
            })


class CamInfoObj(QtCore.QObject):
    """
    Camera info object.
    When the camera info is changed, the signal will be emitted.
    """

    value_changed = QtCore.Signal(str)
    
    def __init__(self):
        super().__init__()
        self._value = 0
        
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, new_value):
        if self._value != new_value:
            self._value = new_value
            self.value_changed.emit(new_value)


class MyInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """
    Custom interactor style.
    """

    def __init__(self, parent=None):
        self.AddObserver('LeftButtonPressEvent', self.left_button_press_event)
        self.AddObserver('LeftButtonReleaseEvent', self.left_button_release_event)
        self.AddObserver('MouseMoveEvent', self.mouse_move_event)
        self.parent_ref = parent

    def left_button_press_event(self, obj, event):
        self.OnLeftButtonDown()
        return

    def left_button_release_event(self, obj, event):
        self.OnLeftButtonUp()
        return
    
    def mouse_move_event(self, obj, event):
        self.OnMouseMove()
        # update the camera info
        if self.parent_ref.cam_info_disp:
            self.parent_ref.cam_pos = self.parent_ref.ren.GetActiveCamera().GetPosition()
            self.parent_ref.cam_focal_point = self.parent_ref.ren.GetActiveCamera().GetFocalPoint()
            self.parent_ref.cam_view_up = self.parent_ref.ren.GetActiveCamera().GetViewUp()
            self.parent_ref.cam_view_angle = self.parent_ref.ren.GetActiveCamera().GetViewAngle()
            self.parent_ref.cam_info_signal.value = encode_cam_info(self.parent_ref.cam_pos,
                                                                    self.parent_ref.cam_focal_point, 
                                                                    self.parent_ref.cam_view_up, 
                                                                    self.parent_ref.cam_view_angle)
        return


class Window(QtWidgets.QMainWindow):
    '''
        Base class for visualization windows
    '''
    
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.parent = parent
        self.cam_info_disp = False
        self.cam_pos = None
        self.cam_focal_point = None
        self.cam_view_up = None
        self.cam_view_angle = None

        self.cam_info_signal = CamInfoObj()

        self.frame = QtWidgets.QFrame()

        self.vl = QtWidgets.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)

        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        self.iren.SetInteractorStyle(MyInteractorStyle(self))

        self.cam_orient_manipulator = vtk.vtkCameraOrientationWidget()
        self.cam_orient_manipulator.SetParentRenderer(self.ren)
        # cam_orient_manipulator.SetAnimatorTotalFrames(100)
        # Enable the widget.
        self.cam_orient_manipulator.On()
        self.cam_orient_manipulator.KeyPressActivationOff()
    
    def update_bg_color(self, color):
        '''
        Update the background color.

        :param color: color in RGB like (0.1, 0.2, 0.3)
        '''
        self.ren.SetBackground(color)
        self.iren.Render()

    def update_light_factor(self):
        '''
        update the actor's properties
        '''
        # iterate over all actors
        for actor in self.ren.GetActors():
            actor.GetProperty().SetSpecularPower(Config.SPECULAR_POWER)
            actor.GetProperty().SetSpecular(Config.SPECULAR)
            actor.GetProperty().SetDiffuse(Config.DIFFUSE)
            actor.GetProperty().SetAmbient(Config.AMBIENT)
        self.iren.Render()

    def add_toolbar(self, toolbar, icon, status_tip, action):
        '''
        Add a toolbar to the window.

        :param toolbar: toolbar object
        :param icon: icon path
        :param status_tip: status tip
        :param action: action function
        '''
        # separator
        toolbar.addSeparator()

        # cam info action
        cam_info_action = QtGui.QAction(QtGui.QIcon(icon), status_tip, self)
        cam_info_action.triggered.connect(action)
        toolbar.addAction(cam_info_action)

        self.addToolBar(toolbar)

    def onToolbarCamInfoAction(self, state):
        '''
        Toolbar camera info action event.

        :param state: action state
        '''
        self.cam_info_disp = ~self.cam_info_disp
        if self.cam_info_disp:
            self.update_cam_info()
            cam_setting_dialog.main(self)
        # update the render
        self.iren.Render()

    def update_cam_info(self):
        '''
        Update the camera info
        '''
        self.cam_pos = self.ren.GetActiveCamera().GetPosition()
        self.cam_focal_point = self.ren.GetActiveCamera().GetFocalPoint()
        self.cam_view_up = self.ren.GetActiveCamera().GetViewUp()
        self.cam_view_angle = self.ren.GetActiveCamera().GetViewAngle()

    def set_camera_info(self, pos, focal_point, view_up, view_angle):
        '''
        Set the camera info

        :param pos: camera position
        :param focal_point: camera focal point
        :param view_up: camera view up
        :param view_angle: camera view angle
        '''
        self.ren.GetActiveCamera().SetPosition(pos)
        self.ren.GetActiveCamera().SetFocalPoint(focal_point)
        self.ren.GetActiveCamera().SetViewUp(view_up)
        self.ren.GetActiveCamera().SetViewAngle(view_angle)

        self.iren.Render()

    def onToolbarExportAction(self, state):
        '''
        Export current view to image file.

        :param state: action state
        '''
        # window to image filter
        w2if = vtk.vtkWindowToImageFilter()
        w2if.SetInput(self.iren.GetRenderWindow())
        w2if.Update()


        # get the file name
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', '',
                        'PNG (*.png);;JPEG (*.jpg);;TIFF (*.tif);;BMP (*.bmp)')
        if file_name[0]:
            # get the file type
            img_type = file_name[0].split('.')[-1]

            if img_type == 'png':
                writer = vtk.vtkPNGWriter()
            elif img_type == 'jpg':
                writer = vtk.vtkJPEGWriter()
            elif img_type == 'tif':
                writer = vtk.vtkTIFFWriter()
            elif img_type == 'bmp':
                writer = vtk.vtkBMPWriter()
            else:
                return
            
            writer.SetInputConnection(w2if.GetOutputPort())
            writer.SetFileName(file_name[0])
            w2if.Modified()
            writer.Write()

    def reset(self):
        '''
        Reset the window.
        '''
        self.cam_info_disp = False

    def ambient_occlusion(self):
        '''
        Enable ambient occlusion
        @param renderer: vtk renderer
        '''
        self.ren.UseSSAOOn()
        self.ren.SetSSAORadius(0.1 * Config.AMBIENT_OCCLUSION_CONSTANT)
        self.ren.SetSSAOBias(0.001 * Config.AMBIENT_OCCLUSION_CONSTANT)
        # print default kernel size
        print("Default kernel size: " + str(self.ren.GetSSAOKernelSize()))
        self.ren.SetSSAOKernelSize(Config.AMBIENT_OCCLUSION_KERNEL_SIZE)
        self.ren.SSAOBlurOff()

