from PySide6 import QtCore, QtWidgets
from core import particlestats, particleseg


def convert_str_to_list(s):
    '''
    Convert string to list

    @param s: string
    @return: list
    '''
    s = s.replace(" ", "")
    # remove '[' and ']' from string
    s = s[1:-1]

    if s[0] == '[':
        # remove '[' and ']' from string
        s = s[1:-1]
        # split string by '],['
        s = s.split("],[")

        # convert to float
        s = [convert_str_to_list(i) for i in s]
    else:
        # split string by ','
        s = s.split(",")
        # convert to float
        s = [round(float(i), 2) for i in s]
    
    return s


def list_to_str(l):
    '''
    Convert list to string and round to 2 decimal places

    @param l: list
    @return: string
    '''
    # check if element is list of lists
    if isinstance(l[0], list):
        l = [list_to_str(i) for i in l]
        return str(l)
    else:
        # round to 2 decimal places
        l = [round(i, 2) for i in l]
        return str(l)


class ParticleInfoDialog(QtWidgets.QDialog):
    '''
    Particle info dialog containing information about 
    the particle and its neighbors and provides interface 
    to change the visibility of the neighbors
    '''
    def __init__(self, stats_file, parent=None):
        '''
        Particle info dialog

        @param stats_file: the stats file
        @param parent: parent widget
        '''
        super(ParticleInfoDialog, self).__init__(parent)

        # minimum size
        self.setMinimumSize(500, 700)

        # ref to parent
        self.parent = parent
        self.setWindowTitle("Particle Information")

        # create layout
        self.layout = QtWidgets.QVBoxLayout()

        # tab screen
        self.tabs = QtWidgets.QTabWidget()
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()

        # add tabs
        self.tabs.addTab(self.tab1, "Particle data")
        self.tabs.addTab(self.tab2, "Neighbors visibility")

        # create first tab
        self.tab1.layout = QtWidgets.QVBoxLayout()
        self.tab1.layout.addWidget(
            QtWidgets.QLabel("Information about the particle"))

        # table
        grain = particlestats.particle_record(
            int(self.parent.files[self.parent.curr_file].split(".")[0]),
            stats_file)
        
        particle = particlestats.Particle(  cp_id=grain['cp_id'].values[0],
                                            centroid=grain['centroid'].values[0],
                                            eig_vecs=grain['eig_vecs'].values[0],
                                            eig_vals=grain['eig_vals'].values[0],
                                            neighbours=grain['neighbours'].values[0],
                                            num_voxels=grain['num_voxels'].values[0],
                                            eq_rad=grain['eq_rad'].values[0],
                                            label=particleseg.Label.get_label(grain['label'].values[0]),
                                            FI=grain['FI'].values[0],
                                            EI=grain['EI'].values[0],
                                            S=grain['S'].values[0],
                                            C=grain['C'].values[0],
                                            cn=grain['cn'].values[0],
                                            volume=grain['volume'].values[0],
                                            surface_area=grain['surface_area'].values[0],
                                            min_cell_surface_area=grain['min_cell_surface_area'].values[0],
                                            max_cell_surface_area=grain['max_cell_surface_area'].values[0],
                                            normalized_shape_index=grain['normalized_shape_index'].values[0])

        self.table = QtWidgets.QTableWidget()
        
        # populate table with data
        self.table.setRowCount(len(particle.__dict__.keys()))
        self.table.setColumnCount(2)

        # set headers
        self.table.setHorizontalHeaderLabels(["Property", "Value"])

        # set data
        for i, key in enumerate(particle.__dict__.keys()):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(key))
            if key == "label":
                updated_label = self.parent.particle_labels.get_particle_label(particle.cp_id)
                if updated_label is not None:
                    particle.label = updated_label
                for l in particleseg.Label:
                    if l == particle.__dict__[key]:
                        self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(l.name))
                        break
            else:
                # if value is float, round it to 2 decimal places
                key_value = particle.__dict__[key]

                if isinstance(key_value, float):
                    key_value = round(key_value, 2)
                elif "[" in str(key_value):
                    key_value = convert_str_to_list(str(key_value))
                
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(key_value)))

        # resize table size
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        # add table to layout
        self.tab1.layout.addWidget(self.table)

        self.tab1.setLayout(self.tab1.layout)

        # create second tab
        self.tab2.layout = QtWidgets.QVBoxLayout()
        self.tab2.layout.addWidget(QtWidgets.QLabel(
            "Information about the particle's neighbors"))

        # Scroll area
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.cb = {k : QtWidgets.QCheckBox() 
                   for k, v in self.parent.neighbor.items()}

        vl = QtWidgets.QVBoxLayout()
        # print(self.parent.neighbor)
        for k, v in self.parent.neighbor.items():
            hl = QtWidgets.QHBoxLayout()

            # checkbox
            self.cb[k].setChecked(v[0])
            self.cb[k].stateChanged.connect(self.update_visibility)

            # label
            label = QtWidgets.QLabel()
            label.setText(str(k))
            # color label using v[1]
            label.setStyleSheet("QLabel { background-color : %s; }" % v[1])
            # center label
            label.setAlignment(QtCore.Qt.AlignCenter)

            hl.addWidget(label)
            hl.addWidget(self.cb[k])

            vl.addLayout(hl)

        wd = QtWidgets.QWidget()
        wd.setLayout(vl)
        self.scroll.setWidget(wd)

        self.tab2.layout.addWidget(self.scroll)
        self.tab2.setLayout(self.tab2.layout)

        # add tabs to layout
        self.layout.addWidget(self.tabs)

        # close button
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.close_app)
        self.layout.addWidget(self.close_button)

        # set layout
        self.setLayout(self.layout)

    def update_visibility(self):
        '''
        Update visibility of the neighbors
        '''
        for k, cb in self.cb.items():
            if self.sender() == cb:
                self.parent.neighbor[k][0] = cb.isChecked()
                self.parent.onToolbarViewAction(None)
                break

    def close_app(self):
        '''
        Close dialog and destroy it
        '''
        self.close()
        # destroy Qwidget QApplication
        self.destroy()


def main(stats_file, parent=None):
    '''
    Open particle info dialog
    '''
    dialog = ParticleInfoDialog(stats_file, parent)
    parent.paritcle_info_dialog = dialog
    # dialog.move(parent.x() + parent.frameGeometry().width(), parent.y())
    # make it non blocking dialog
    dialog.setWindowModality(QtCore.Qt.NonModal)
    dialog.show()