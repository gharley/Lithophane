import os
import sys
import json

import open3d as o3d

from matplotlib.backends.qt_compat import QtWidgets

from PyQt5 import uic
from PyQt5.QtCore import QFile
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QComboBox, QLineEdit, QCheckBox, QFileDialog

from common import DotDict
import Lithophane as lp


class Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self._img = None
        self._img_colors = None
        self._heights = None
        self._vertices = None
        self._faces = None
        self._model = None

        self._base_height = 0.01
        self._max_height = 5.0
        self._max_size = 127
        self._samples = 2

        self._load_config()
        self._load_ui()

        # self.imgLayout = self._main.imgLayout
        # fig = Figure(figsize=(self._img.width, self._img.height))
        # fig.figimage(self._img, cmap='gray')
        # static_canvas = FigureCanvas(fig)
        # self._main.imgLayout.addWidget(static_canvas)

        # dynamic_canvas = FigureCanvas(Figure(figsize=(self._img.width, self._img.height)))
        # self.imgLayout.addWidget(dynamic_canvas)

    def _init_connections(self):
        self.actionOpen.triggered.connect(self.process_image)

    def _load_config(self):
        if os.path.exists('config.json'):
            with open('config.json', 'r') as in_file:
                self.config = DotDict(json.load(in_file))

    def _load_ui(self):
        ui_file = QFile('mainwindow.ui')
        # ui_file = QFile(':resources/mainwindow.ui')
        ui_file.open(QFile.ReadOnly)
        self._main = uic.loadUi(ui_file, self)
        ui_file.close()

        self._init_connections()

        self.show()

        # style_sheet = QFile(':resources/form.qss')
        # if style_sheet.exists():
        #     style_sheet.open(QFile.ReadOnly)
        #     style = str(style_sheet.readAll(), 'utf-8')
        #     self.setStyleSheet(style)
        #     style_sheet.close()
        #
        # self.setWindowIcon(QIcon(':images/end_all.svg'))

    def process_image(self):
        filename = "C:/Cloud/Google/Fab/CNC/3D/bee3D.jpg"
        litho = lp.Lithophane()

        self._vertices = litho.prepare_image(filename, self._base_height, self._max_height, self._max_size, self._samples)
        pcd = litho.create_point_cloud_from_vertices(self._vertices, color=[0.0, 1.0, 1.0], display=True, show_normals=False)
        pcd = litho.scale_to_final_size(pcd, self._max_size)
        bpa_mesh = litho.create_mesh_from_point_cloud(pcd, self._base_height, self._max_height)
        o3d.io.write_triangle_mesh("C:/Cloud/Google/Fab/Artwork/nsfw.stl", bpa_mesh)


if __name__ == "__main__":
    app = QApplication([])
    main_window = Main()
    sys.exit(app.exec_())
