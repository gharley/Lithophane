import sys
import time

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

        ui_file = QFile('mainwindow.ui')
        ui_file.open(QFile.ReadOnly)
        self._main = uic.loadUi(ui_file, self)
        ui_file.close()

        # self._main = QtWidgets.QWidget()
        # self.setCentralWidget(self._main)
        # layout = QtWidgets.QVBoxLayout(self._main)
        #
        img = self._to_gray_scale(Image.open("C:/Cloud/Google/Fab/Artwork/nsfw.png"))
        dpi = img.info['dpi'][0]
        fig = Figure(figsize=(img.width / dpi, img.height / dpi))
        fig.figimage(img, cmap='gray')
        static_canvas = FigureCanvas(fig)
        # # Ideally one would use self.addToolBar here, but it is slightly
        # # incompatible between PyQt6 and other bindings, so we just add the
        # # toolbar as a plain widget instead.
        # # layout.addWidget(NavigationToolbar(static_canvas, self))
        # layout.addWidget(static_canvas)
        self._main.imgLayout.addWidget(static_canvas)
        #
        dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self._main.imgLayout.addWidget(dynamic_canvas)
        self._main.imgLayout.addWidget(NavigationToolbar(dynamic_canvas, self))

        # self._static_ax = static_canvas.figure.subplots()
        # t = np.linspace(0, 10, 501)
        # self._static_ax.plot(t, np.tan(t), ".")

        self._dynamic_ax = dynamic_canvas.figure.subplots()
        t = np.linspace(0, 10, 101)
        # Set up a Line2D.
        self._line, = self._dynamic_ax.plot(t, np.sin(t + time.time()))
        self._timer = dynamic_canvas.new_timer(50)
        self._timer.add_callback(self._update_canvas)
        self._timer.start()

    def _update_canvas(self):
        t = np.linspace(0, 10, 101)
        # Shift the sinusoid as a function of time.
        self._line.set_data(t, np.sin(t + time.time()))
        self._line.figure.canvas.draw()

    def _to_gray_scale(self, img: Image):
        # r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        # gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
        # return gray
        result = ImageOps.grayscale(img)
        return result


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
