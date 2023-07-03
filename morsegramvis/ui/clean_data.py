from PySide6 import QtCore, QtWidgets


def get_ui(vol_hist, perform_clean_data):
    """
    clean data interface.
    Use this interface to filter out the particles that are too small.
    @param vol_hist: The volume histogram data.
    @param perform_clean_data: The perform clean data button function.
    @return: The UI object(layout), vol_cutoff_input: The volume cutoff input widget.
    """
    # vertical layout
    vl = QtWidgets.QVBoxLayout()
    # heading label - Cleaning Data
    heading_label = QtWidgets.QLabel("Cleaning Data")
    heading_label.setStyleSheet("font-size: 20px; font-weight: bold;")
    # align the heading label to the center
    heading_label.setAlignment(QtCore.Qt.AlignCenter)
    vl.addWidget(heading_label)

    # clean data button
    vol_hist_data_button = QtWidgets.QPushButton("Show Histogram of Particle Sizes(volume)")
    # fix the size of the button
    vol_hist_data_button.setFixedWidth(300)
    vol_hist_data_button.clicked.connect(vol_hist)
    vl.addWidget(vol_hist_data_button, alignment=QtCore.Qt.AlignCenter)

    # volume cutoff input box
    vol_cutoff_input = QtWidgets.QLineEdit()
    vol_cutoff_input.setFixedWidth(300)
    vol_cutoff_input.setPlaceholderText("Volume cutoff")
    vl.addWidget(vol_cutoff_input, alignment=QtCore.Qt.AlignCenter)

    # perform cleaning data button
    perform_clean_data_button = QtWidgets.QPushButton("Perform Cleaning Data")
    # fix the size of the button
    perform_clean_data_button.setFixedWidth(300)
    perform_clean_data_button.clicked.connect(perform_clean_data)
    vl.addWidget(perform_clean_data_button, alignment=QtCore.Qt.AlignCenter)

    # horizontal line
    hline = QtWidgets.QFrame()
    hline.setFrameShape(QtWidgets.QFrame.HLine)
    hline.setFrameShadow(QtWidgets.QFrame.Sunken)
    vl.addWidget(hline)

    return vl, vol_cutoff_input