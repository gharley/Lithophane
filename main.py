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


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self._img = None
        self._heights = None
        self._vectors = None
        self._faces = None
        self._model = None

        self._max_height = 5
        self._max_size = 254

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
        # figure = pyplot.figure()
        # axes = mplot3d.Axes3D(figure)

        # Load the STL files and add the vectors to the plot
        # axes.add_collection3d(mplot3d.art3d.Poly3DCollection(self._model.vectors))

        # Auto scale to the mesh size
        # scale = self._model.points.flatten(-1)
        # axes.auto_scale_xyz(scale, scale, scale)

        # Show the plot to the screen
        # pyplot.show()

        self.imgLayout = self._main.imgLayout
        fig = Figure(figsize=(self._img.width, self._img.height))
        fig.figimage(self._img, cmap='gray')
        static_canvas = FigureCanvas(fig)
        self._main.imgLayout.addWidget(static_canvas)

        # dynamic_canvas = FigureCanvas(Figure(figsize=(self._img.width, self._img.height)))
        # self.imgLayout.addWidget(dynamic_canvas)
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
        self._heights[1:-1, 1:-1] = matplotlib.image.pil_to_array(gray) / np.max(gray.getdata()) * self._max_height

        self._get_vectors()

        pcl = o3d.geometry.PointCloud()
        point_cloud = np.asarray(self._vectors)
        pcl.points = o3d.utility.Vector3dVector(point_cloud)
        img = o3d.geometry.Image((self._heights * 255).astype(np.uint8))
        pcl.colors = o3d.utility.Vector3dVector(point_cloud / 255)
        pcl.normals = o3d.utility.Vector3dVector(point_cloud)
        distances = pcl.compute_nearest_neighbor_distance()
        avg_dist = np.mean(distances)
        radius = 3 * avg_dist
        bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcl, depth=self._max_height)
        # bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcl, o3d.utility.DoubleVector([radius, radius * 2]))
        # o3d.visualization.draw_geometries([pcl])
        # o3d.visualization.draw_geometries([bpa_mesh[0]])

        x1 = np.linspace(1, self._heights.shape[1], self._heights.shape[1])
        y1 = np.linspace(1, self._heights.shape[0], self._heights.shape[0])

        x, y = np.meshgrid(x1, y1)

        count = 0
        points = []
        triangles = []
        for i in range(self._heights.shape[0] - 1):
            for j in range(self._heights.shape[1] - 1):
                # Triangle 1
                points.append([x[i][j], y[i][j], self._heights[i][j]])
                points.append([x[i][j + 1], y[i][j + 1], self._heights[i][j + 1]])
                points.append([x[i + 1][j], y[i + 1][j], self._heights[i + 1][j]])

                triangles.append([count, count + 1, count + 2])

                # Triangle 2
                points.append([x[i][j + 1], y[i][j + 1], self._heights[i][j + 1]])
                points.append([x[i + 1][j + 1], y[i + 1][j + 1], self._heights[i + 1][j + 1]])
                points.append([x[i + 1][j], y[i + 1][j], self._heights[i + 1][j]])

                triangles.append([count + 3, count + 4, count + 5])

                count += 6

        self._model = mesh.Mesh(np.zeros(len(triangles), dtype=mesh.Mesh.dtype))
        for i, f in enumerate(triangles):
            for j in range(3):
                self._model.vectors[i][j] = points[f[j]]

        # fig = pyplot.figure()
        fig = Figure(figsize=(self._img.width, self._img.height))
        ax = fig.gca(projection='3d')
        ax.add_collection3d(mplot3d.art3d.Poly3DCollection(np.asarray(bpa_mesh[0].triangles)))
        # ax.add_collection3d(mplot3d.art3d.Poly3DCollection(self._model.vectors))
        dynamic_canvas = FigureCanvas(fig)
        self.imgLayout.addWidget(dynamic_canvas)
        pyplot.show()
        self._model.save("C:/Cloud/Google/Fab/Artwork/nsfw.stl")
        # self._get_vectors()
        # self._get_faces()

    def _get_vectors(self):
        self._vectors = np.zeros([self._heights.size, 3], np.dtype(np.float64, (3, )))
        for x in range(self._heights.shape[0]):
            for y in range(self._heights.shape[1]):
                self._vectors[x * self._heights.shape[1] + y] = (float(x), float(y), self._heights[x][y])

    def _get_faces(self):
        self._faces = []
        for x in range(self._heights.shape[0] - 1):
            for y in range(self._heights.shape[1] - 1):
                offset = x * self._heights.shape[1]

                self._faces.append((offset, y, y + 1))
                self._faces.append((offset, y + 1, y))


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
