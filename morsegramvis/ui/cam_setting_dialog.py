from PySide6 import QtCore, QtWidgets


class CameraSetting(QtWidgets.QDialog):
    '''
    Camera setting dialog
    Display camera parameters like position, focal point, view up, view angle
    and allow user to change/update these parameters.
    '''
    
    def __init__(self, parent=None):
        super(CameraSetting, self).__init__(parent)
        # ref to parent
        self.parent_widget = parent

        self.parent_widget.cam_info_signal.value_changed.connect(self.update_cam_info)

        self.setWindowTitle("Configure Settings")
        self.setMinimumSize(500, 400)
        # self.setStyleSheet("background-color: #f0f0f0")

        # create layout
        self.layout = QtWidgets.QVBoxLayout()
    
        self.position = [QtWidgets.QLineEdit() for i in range(3)]
        self.focal_point = [QtWidgets.QLineEdit() for i in range(3)]
        self.view_up = [QtWidgets.QLineEdit() for i in range(3)]
        
        # init input field
        for v, ui_w in zip(self.parent_widget.cam_pos, self.position):
            ui_w.setText(str(round(v, 2)))
        for v, ui_w in zip(self.parent_widget.cam_focal_point, self.focal_point):
            ui_w.setText(str(round(v, 2)))
        for v, ui_w in zip(self.parent_widget.cam_view_up, self.view_up):
            ui_w.setText(str(round(v, 2)))
        
        input_field = [ ["Position\t", self.position],
                        ["Focal\nPoint\t", self.focal_point],
                        ["View Up\t", self.view_up]]

        for field, input_wid in input_field:
            hl = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(field)
            hl.addWidget(label)
            for i in range(3):
                hl.addWidget(input_wid[i])
            self.layout.addLayout(hl)

        # view angle
        hl = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("View Angle\t")
        hl.addWidget(label)
        self.view_angle = QtWidgets.QLineEdit()
        hl.addWidget(self.view_angle)
        self.layout.addLayout(hl)

        # init view angle
        self.view_angle.setText(str(self.parent_widget.cam_view_angle))
        
        self.apply_button = QtWidgets.QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply)
        self.layout.addWidget(self.apply_button)

        # close button
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.close_app)
        self.layout.addWidget(self.close_button)

        # set layout
        self.setLayout(self.layout)

    @QtCore.Slot(str)
    def update_cam_info(self, cam_info):
        '''
        Update camera info

        @param cam_info: camera info contains position, focal point, view up, view angle
        '''
        # parse string to dict
        cam_info = eval(cam_info)
        
        for i in ["position", "focal_point", "view_up"]:
            for j in range(3):
                self.__dict__[i][j].setText(str(round(cam_info[i][j], 2)))


        self.view_angle.setText(str(cam_info["view_angle"]))

    def apply(self):
        '''
        Apply camera settings
        Update camera parameters like position, focal point, view up, view angle
        '''
        self.parent_widget.set_camera_info(
            (float(self.position[0].text()), float(self.position[1].text()), float(self.position[2].text())),
            (float(self.focal_point[0].text()), float(self.focal_point[1].text()), float(self.focal_point[2].text())),
            (float(self.view_up[0].text()), float(self.view_up[1].text()), float(self.view_up[2].text())),
            float(self.view_angle.text()))

    def close_app(self):
        '''
        Close dialog window
        '''
        self.parent_widget.reset()
        self.close()
        # destroy Qwidget QApplication
        self.destroy()

    def closeEvent(self, event):
        '''
        Close dialog window

        @param event: close event
        '''
        self.close_app()


def main(parent=None):
    '''
    Open camera setting dialog
    '''
    dialog = CameraSetting(parent)
    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()