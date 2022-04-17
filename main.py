import math
import sys
import time

import matplotlib.image
import numpy as np
from stl import mesh
import open3d as o3d

from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas)
from matplotlib.figure import Figure
from matplotlib import pyplot
from mpl_toolkits import mplot3d
from PIL import Image, ImageOps
from PyQt5 import uic
from PyQt5.QtCore import QFile

import Lithophane as lp


class ApplicationWindow(QtWidgets.QMainWindow):
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
        self._samples = 5

        ui_file = QFile('mainwindow.ui')
        ui_file.open(QFile.ReadOnly)
        self._main = uic.loadUi(ui_file, self)
        ui_file.close()

        self.process_image("C:/Cloud/Google/Fab/CNC/3D/bee3D.jpg")

        # self.imgLayout = self._main.imgLayout
        # fig = Figure(figsize=(self._img.width, self._img.height))
        # fig.figimage(self._img, cmap='gray')
        # static_canvas = FigureCanvas(fig)
        # self._main.imgLayout.addWidget(static_canvas)

        # dynamic_canvas = FigureCanvas(Figure(figsize=(self._img.width, self._img.height)))
        # self.imgLayout.addWidget(dynamic_canvas)

    def process_image(self, filename):
        litho = lp.Lithophane()

        self._vertices = litho.prepare_image(filename, self._base_height, self._max_height, self._max_size, self._samples)
        pcd = litho.create_point_cloud_from_vertices(self._vertices, color=[0.5, 0.5, 1.0], display=False, show_normals=False)
        pcd = litho.scale_to_final_size(pcd, self._max_size)
        bpa_mesh = litho.create_mesh_from_point_cloud(pcd, self._base_height, self._max_height)
        o3d.io.write_triangle_mesh("C:/Cloud/Google/Fab/Artwork/nsfw.stl", bpa_mesh)


if __name__ == "__main__":
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow()
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec()
