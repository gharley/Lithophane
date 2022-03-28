import sys
import time

import matplotlib.image
import numpy as np
from stl import mesh

from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas)
from matplotlib.figure import Figure
from matplotlib import pyplot
from mpl_toolkits import mplot3d
from PIL import Image, ImageOps
from PyQt5 import uic
from PyQt5.QtCore import QFile


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self._img = None
        self._heights = None
        self._vectors = None
        self._faces = None
        self._model = None

        self._max_height = 3
        self._max_size = 100

        ui_file = QFile('mainwindow.ui')
        ui_file.open(QFile.ReadOnly)
        self._main = uic.loadUi(ui_file, self)
        ui_file.close()

        # self._main = QtWidgets.QWidget()
        # self.setCentralWidget(self._main)
        # layout = QtWidgets.QVBoxLayout(self._main)
        #
        self.process_image("C:/Cloud/Google/Fab/Artwork/nsfw.png")

        # Create a new plot
        figure = pyplot.figure()
        axes = mplot3d.Axes3D(figure)

        # Load the STL files and add the vectors to the plot
        axes.add_collection3d(mplot3d.art3d.Poly3DCollection(self._model.vectors))

        # Auto scale to the mesh size
        scale = self._model.points.flatten(-1)
        axes.auto_scale_xyz(scale, scale, scale)

        # Show the plot to the screen
        pyplot.show()

        self.imgLayout = self._main.imgLayout
        fig = Figure(figsize=(self._img.width, self._img.height))
        fig.figimage(self._img, cmap='gray')
        static_canvas = FigureCanvas(fig)
        self._main.imgLayout.addWidget(static_canvas)

        dynamic_canvas = FigureCanvas(Figure(figsize=(self._img.width, self._img.height)))
        self.imgLayout.addWidget(dynamic_canvas)
        # self._main.imgLayout.addWidget(NavigationToolbar(dynamic_canvas, self))
        #
        # # self._static_ax = static_canvas.figure.subplots()
        # # t = np.linspace(0, 10, 501)
        # # self._static_ax.plot(t, np.tan(t), ".")
        #
        # self._dynamic_ax = dynamic_canvas.figure.subplots()
        # t = np.linspace(0, 10, 101)
        # # Set up a Line2D.
        # self._line, = self._dynamic_ax.plot(t, np.sin(t + time.time()))
        # self._timer = dynamic_canvas.new_timer(50)
        # self._timer.add_callback(self._update_canvas)
        # self._timer.start()

    def process_image(self, filename):
        self._img = Image.open(filename)
        gray = ImageOps.grayscale(self._img)
        scale = self._max_size / max(self._img.width, self._img.height)
        gray = ImageOps.scale(gray, scale, True)
        self._heights = np.zeros([gray.height + 2, gray.width + 2])
        self._heights[1:-1, 1:-1] = (matplotlib.image.pil_to_array(gray) / np.max(gray.getdata())) * self._max_height
        self._get_vectors()
        self._get_faces()

        # Create the mesh
        self._model = mesh.Mesh(np.zeros(len(self._faces), dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self._vectors):
            for j in range(3):
                self._model.vectors[i][j] = f[j]

    def _get_vectors(self):
        self._vectors = np.zeros([self._heights.shape[0], self._heights.shape[1]], dtype=np.dtype((np.float64, 3)))
        for x in range(self._heights.shape[0]):
            for y in range(self._heights.shape[1]):
                self._vectors[x, y] = (x, y, self._heights[x][y])

    def _get_faces(self):
        self._faces = []
        for x in range(self._vectors.shape[0] - 1):
            for y in range(self._vectors.shape[1] - 1):
                self._faces.append((x, y, y + 1))
                self._faces.append((x, y + 1, y))


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
