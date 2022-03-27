import sys
import time

import matplotlib.image
import numpy as np

from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
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
        self.imgLayout = self._main.imgLayout
        fig = Figure(figsize=(self._img.width, self._img.height))
        fig.figimage(self._img, cmap='gray')
        static_canvas = FigureCanvas(fig)
        self._main.imgLayout.addWidget(static_canvas)
        #
        # dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        # self._main.imgLayout.addWidget(dynamic_canvas)
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

    def _update_canvas(self):
        t = np.linspace(0, 10, 101)
        # Shift the sinusoid as a function of time.
        self._line.set_data(t, np.sin(t + time.time()))
        self._line.figure.canvas.draw()

    def process_image(self, filename):
        self._img = Image.open(filename)
        gray = ImageOps.grayscale(self._img)
        scale = self._max_size / max(self._img.width, self._img.height)
        gray = ImageOps.scale(gray, scale, True)
        self._heights = (matplotlib.image.pil_to_array(gray) / np.max(gray)) * self._max_height
        self.get_vectors()

    def get_vectors(self):
        height_index = 0
        self._vectors = np.zeros((self._heights.size, 3), np.dtype(np.float64, (3,)))
        for x in range(self._heights.shape[0]):
            for y in range(self._heights.shape[1]):
                self._vectors[height_index] = (x, y, self._heights[x][y])
                height_index += 1


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
