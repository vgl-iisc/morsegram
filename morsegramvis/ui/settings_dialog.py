from PySide6 import QtCore, QtWidgets
from settings import Config
from ui import transferfunc
import logging
from core import utils


class SettingsDialog(QtWidgets.QDialog):
    '''
    Settings dialog to change background color, 
    light factor, ambient occlusion factor, iso value,
    iso opacity, so on ...
    '''

    def __init__(self, parent=None):
        '''
        Initialize Settings dialog

        @param parent: parent widget
        '''
        super(SettingsDialog, self).__init__(parent)
        # ref to parent
        self.parent_widget = parent
        self.setWindowTitle("Configure Settings")
        self.setMinimumSize(500, 400)
        # self.setStyleSheet("background-color: #f0f0f0")

        # create layout
        self.layout = QtWidgets.QVBoxLayout()

        if self.parent_widget.bg_color:
            rgb_label = []
            self.rgb_slider = []
            # horizontal layout
            rgb_layout = QtWidgets.QVBoxLayout()
            for c in ["r", "g", "b"]:
                # horizontal layout
                c_layout = QtWidgets.QHBoxLayout()
                rgb_label.append(QtWidgets.QLabel("<b>%s</b>" % c))
                # slider
                self.rgb_slider.append(QtWidgets.QSlider(QtCore.Qt.Horizontal))
                self.rgb_slider[-1].setMinimum(0)
                self.rgb_slider[-1].setMaximum(255)
                # self.rgb_edit[-1].setText("0")
                if c == "r":
                    # self.rgb_edit[-1].setText(str(config.BG_COLOR[0]))
                    self.rgb_slider[-1].setValue(Config.BG_COLOR[0] * 255)
                elif c == "g":
                    # self.rgb_edit[-1].setText(str(config.BG_COLOR[1]))
                    self.rgb_slider[-1].setValue(Config.BG_COLOR[1] * 255)
                elif c == "b":
                    # self.rgb_edit[-1].setText(str(config.BG_COLOR[2]))
                    self.rgb_slider[-1].setValue(Config.BG_COLOR[2] * 255)
                # self.rgb_edit[-1].setStyleSheet("background-color: #fff")
                # self.rgb_edit[-1].setAlignment(QtCore.Qt.AlignCenter)
                # signal/slot on finished editing
                # self.rgb_edit[-1].editingFinished.connect(self.update_color)
                # signal/slot on value changed
                self.rgb_slider[-1].valueChanged.connect(self.update_bg_color)
                c_layout.addWidget(rgb_label[-1])
                # c_layout.addWidget(self.rgb_edit[-1])
                c_layout.addWidget(self.rgb_slider[-1])
                rgb_layout.addLayout(c_layout)
            self.layout.addLayout(rgb_layout)

        if self.parent_widget.light_factor:
            # slider for [ambient, diffuse, specular] factor
            # vertical layout
            ads_layout = QtWidgets.QVBoxLayout()
            self.factor_slider = []
            for i, f in enumerate(["Ambient", "Diffuse", "Specular", "Specular Power"]):
                # horizontal layout
                factor_layout = QtWidgets.QHBoxLayout()
                # label
                self.factor_label = QtWidgets.QLabel("<b>" + f + " factor</b>")
                self.factor_label.setAlignment(QtCore.Qt.AlignCenter)
                # constant width label
                self.factor_label.setFixedWidth(200)
                # slider
                self.factor_slider.append(QtWidgets.QSlider(QtCore.Qt.Horizontal))
                self.factor_slider[i].setMinimum(0)
                self.factor_slider[i].setMaximum(100)
                # self.factor_slider[i].setValue(50)
                if i == 0:
                    self.factor_slider[i].setValue(Config.AMBIENT * 100)
                elif i == 1:
                    self.factor_slider[i].setValue(Config.DIFFUSE * 100)
                elif i == 2:
                    self.factor_slider[i].setValue(Config.SPECULAR * 100)
                elif i == 3:
                    self.factor_slider[i].setValue(Config.SPECULAR_POWER)
                self.factor_slider[i].setTickPosition(QtWidgets.QSlider.TicksBelow)
                self.factor_slider[i].setTickInterval(10)
                self.factor_slider[i].setFocusPolicy(QtCore.Qt.NoFocus)
                self.factor_slider[i].valueChanged.connect(self.update_light_factor)
                # add to layout
                factor_layout.addWidget(self.factor_label)
                factor_layout.addWidget(self.factor_slider[i])
                # add to vertical layout
                ads_layout.addLayout(factor_layout)
            self.layout.addLayout(ads_layout)

        if self.parent_widget.ao_factor:
            # line edit for Ambient occlustion factor and Ambient occlustion kernel size
            # vertical layout
            ao_layout = QtWidgets.QVBoxLayout()
            self.ao_edit = []
            for i, f in enumerate(["Ambient Occlusion Factor", "Ambient Occlusion Kernel Size"]):
                # horizontal layout
                ao_hlayout = QtWidgets.QHBoxLayout()
                # label
                ao_label = QtWidgets.QLabel("<b>" + f + "</b>")
                ao_label.setAlignment(QtCore.Qt.AlignCenter)
                # constant width label
                ao_label.setFixedWidth(200)
                # line edit
                self.ao_edit.append(QtWidgets.QLineEdit())
                # self.ao_edit[i].setText("0")
                if i == 0:
                    self.ao_edit[i].setText(str(Config.AMBIENT_OCCLUSION_CONSTANT))
                elif i == 1:
                    self.ao_edit[i].setText(str(Config.AMBIENT_OCCLUSION_KERNEL_SIZE))
                self.ao_edit[i].setAlignment(QtCore.Qt.AlignCenter)
                # signal/slot on finished editing
                self.ao_edit[i].editingFinished.connect(self.update_ao_factor)
                # add to layout
                ao_hlayout.addWidget(ao_label)
                ao_hlayout.addWidget(self.ao_edit[i])
                # add to vertical layout
                ao_layout.addLayout(ao_hlayout)
            self.layout.addLayout(ao_layout)
        
        try:
            if self.parent_widget.iso_show:
                # iso value handling
                # frame with label, input and button in a horizontal layout
                self.iso_frame = QtWidgets.QFrame()
                self.iso_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
                self.iso_frame.setFrameShadow(QtWidgets.QFrame.Raised)
                self.iso_frame.setLineWidth(1)
                self.iso_frame.setMidLineWidth(0)
                # self.iso_frame.setFixedWidth(300)
                self.iso_frame.setFixedHeight(100)
                self.iso_frame_layout = QtWidgets.QVBoxLayout()
                hl = QtWidgets.QHBoxLayout()
                self.iso_frame.setLayout(self.iso_frame_layout)
                # label
                self.iso_label = QtWidgets.QLabel("<b>ISO Value</b>")
                self.iso_label.setAlignment(QtCore.Qt.AlignCenter)
                self.iso_label.setFixedWidth(100)
                # line edit
                self.iso_edit = QtWidgets.QLineEdit()
                self.iso_edit.setText(str(self.parent_widget.iso_value))
                self.iso_edit.setAlignment(QtCore.Qt.AlignCenter)
                self.iso_edit.setFixedWidth(100)
                # button
                self.iso_button = QtWidgets.QPushButton("Set")
                self.iso_button.clicked.connect(self.set_iso_value)
                self.iso_button.setFixedWidth(100)
                hl.addWidget(self.iso_label)
                hl.addWidget(self.iso_edit)
                hl.addWidget(self.iso_button)
                # add to layout
                self.iso_frame_layout.addLayout(hl)

                hl = QtWidgets.QHBoxLayout()
                op_label = QtWidgets.QLabel("<b>Opacity</b>")
                op_label.setAlignment(QtCore.Qt.AlignCenter)
                op_label.setFixedWidth(100)
                hl.addWidget(op_label)
                # add a opacity slider
                self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
                # self.opacity_slider.setFixedWidth(300)
                self.opacity_slider.setFixedHeight(20)
                self.opacity_slider.setMinimum(0)
                self.opacity_slider.setMaximum(100)
                self.opacity_slider.setValue(self.parent_widget.iso_opacity * 100)
                self.opacity_slider.valueChanged.connect(self.update_iso_opacity)
                hl.addWidget(self.opacity_slider)
                self.iso_frame_layout.addLayout(hl)

                self.layout.addWidget(self.iso_frame)
        except AttributeError:
            logging.getLogger().warning("attribute error: iso_show")
        
        # volume cutoff handling
        try:
            if self.parent_widget.vol_cutoff_filter:
                self.widget_width = 300
                self.vol_cutoff_input1 = QtWidgets.QLineEdit()
                self.vol_cutoff_input1.setText(str(self.parent_widget.vol_range[0]))
                self.vol_cutoff_input2 = QtWidgets.QLineEdit()
                self.vol_cutoff_input2.setText(str(self.parent_widget.vol_range[1]))
                self.vol_bounds = self.parent_widget.get_vol_bounds()
                vol_range_label1 = QtWidgets.QLabel("<b>Volume Range from </b>")
                vol_range_label2 = QtWidgets.QLabel("<b> to </b>")
                # update button
                self.vol_cutoff_button = QtWidgets.QPushButton("Set")
                self.vol_cutoff_button.clicked.connect(self.update_vol_cutoff)
                self.layout.addWidget(transferfunc.get_frame([vol_range_label1,
                                                              self.vol_cutoff_input1,
                                                              vol_range_label2,
                                                              self.vol_cutoff_input2,
                                                              self.vol_cutoff_button], QtWidgets.QHBoxLayout))
        except AttributeError:
            logging.getLogger().warning("attribute error: vol_cutoff_filter")

        # text actor handling - saddle simplified graph
        try:
            if self.parent_widget.text_actor_visible:
                self.widget_width = 300
                self.rangeSelector = transferfunc.RangeSlider(self, self.alpha_cb)
                self.rangeSelector.label_minmax(0, 1)
                self.rangeSelector.styled_range_hslider.setValue((self.parent_widget.alpha_range[0] * 100,
                                                                  self.parent_widget.alpha_range[1] * 100))
                # add text actor visible checkbox
                self.text_actor_visible_checkbox = QtWidgets.QCheckBox("Text Actor Visible")
                if self.parent_widget.show_simplified_text_actor:
                    self.text_actor_visible_checkbox.setChecked(True)
                else:
                    self.text_actor_visible_checkbox.setChecked(False)
                self.text_actor_visible_checkbox.stateChanged.connect(self.update_text_actor_visible)
                self.layout.addWidget(transferfunc.get_frame([self.text_actor_visible_checkbox, self.rangeSelector], QtWidgets.QHBoxLayout))
        except AttributeError:
            logging.getLogger().warning("attribute error: text_actor_visible")

        if self.parent_widget.input_raw_data:
            self.setMinimumSize(500, 800)
            # add rangeSelector
            self.rangeSelector = transferfunc.TransferFunctionWithColorMap(self)
            self.layout.addWidget(self.rangeSelector)

        # close button
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.close_app)
        self.layout.addWidget(self.close_button)

        # set layout
        self.setLayout(self.layout)
    
    def set_iso_value(self):
        '''
        Set iso value
        '''
        # validate input value against iso value range (distance_scalar_range)
        # Qmessagebox if invalid
        if float(self.iso_edit.text()) < self.parent_widget.distance_scalar_range[0] or \
                float(self.iso_edit.text()) > self.parent_widget.distance_scalar_range[1]:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("Invalid value for ISO value")
            msg.setInformativeText("Please enter a value between " + str(self.parent_widget.distance_scalar_range[0]) + " and " + str(self.parent_widget.distance_scalar_range[1]))
            msg.setWindowTitle("Warning")
            msg.exec_()
            return
        self.parent_widget.iso_value = float(self.iso_edit.text())
        self.parent_widget.update_iso_surface()

    def update_iso_opacity(self):
        '''
        Update opacity of iso surface
        '''
        self.parent_widget.iso_opacity = self.opacity_slider.value() / 100
        self.parent_widget.update_iso_surface()

    def alpha_cb(self, range):
        '''
        Callback function for alpha range slider

        @param range: range of alpha values
        '''
        a1, a2 = float(range[0])/100, float(range[1])/100
        self.parent_widget.display_alpha_range(a1, a2)
        return a1, a2

    def update_vol_cutoff(self):
        '''
        Update volume cutoff
        '''
        try:
            if utils.check_file(Config.PARTICLE_STATS_FILE):
                self.parent_widget.vol_range = (int(self.vol_cutoff_input1.text()), int(self.vol_cutoff_input2.text()))
                QtWidgets.QMessageBox.information(self, "Information", "Volume cutoff range updated")
            else:
                QtWidgets.QMessageBox.warning(self, "Warning", "Please compute particle statistics first")
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a valid integer value")
            return

    def update_text_actor_visible(self):
        '''
        Update text actor visible
        '''
        self.parent_widget.update_text_actor_visible()
        curr_range = self.rangeSelector.styled_range_hslider.value()
        self.parent_widget.display_alpha_range(float(curr_range[0])/100, float(curr_range[1])/100)

    def update_bg_color(self):
        '''
        Update background color
        '''
        try:
            r = self.rgb_slider[0].value() / 255
            g = self.rgb_slider[1].value() / 255
            b = self.rgb_slider[2].value() / 255
            Config.BG_COLOR = (r, g, b)
            # update background color of self.parent.ren
            self.parent_widget.update_bg_color(Config.BG_COLOR)
        except ValueError:
            return

    def update_light_factor(self):
        '''
        Update light factor (ambient, diffuse, specular, specular power)
        '''
        Config.AMBIENT = self.factor_slider[0].value() / 100
        Config.DIFFUSE = self.factor_slider[1].value() / 100
        Config.SPECULAR = self.factor_slider[2].value() / 100
        Config.SPECULAR_POWER = self.factor_slider[3].value()
        # print(config.AMBIENT, config.DIFFUSE, config.SPECULAR, config.SPECULAR_POWER)
        # update light factor of self.parent.ren
        self.parent_widget.update_light_factor()

    def update_ao_factor(self):
        '''
        Update ambient occlusion factor and kernel size
        '''
        try:
            Config.AMBIENT_OCCLUSION_CONSTANT = int(self.ao_edit[0].text())
            Config.AMBIENT_OCCLUSION_KERNEL_SIZE = int(self.ao_edit[1].text())
            # update light factor of self.parent.ren
            self.parent_widget.update_ao_factor()
        except ValueError:
            return

    def close_app(self):
        '''
        Close Settings dialog
        '''
        self.close()
        # destroy Qwidget QApplication
        self.destroy()


def main(parent=None):
    '''
    Open Settings dialog

    @param parent: parent widget
    '''
    dialog = SettingsDialog(parent)
    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()



