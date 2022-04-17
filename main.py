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

        self._base_height = 0
        self._max_height = 5.0
        self._max_size = 127
        self._samples = 5

        ui_file = QFile('mainwindow.ui')
        ui_file.open(QFile.ReadOnly)
        self._main = uic.loadUi(ui_file, self)
        ui_file.close()

        self.process_image("C:/Cloud/Google/Fab/CNC/3D/bee3D.jpg")

        self.imgLayout = self._main.imgLayout
        fig = Figure(figsize=(self._img.width, self._img.height))
        fig.figimage(self._img, cmap='gray')
        static_canvas = FigureCanvas(fig)
        self._main.imgLayout.addWidget(static_canvas)

        # dynamic_canvas = FigureCanvas(Figure(figsize=(self._img.width, self._img.height)))
        # self.imgLayout.addWidget(dynamic_canvas)

    def process_image(self, filename):
        self._img = Image.open(filename)

        scale = self._max_size / max(self._img.width, self._img.height) * self._samples
        self._img = ImageOps.scale(self._img, scale, True)

        gray = ImageOps.grayscale(self._img)
        gray = gray.rotate(-90)
        # gray = ImageOps.flip(gray)
        img = o3d.geometry.Image(matplotlib.image.pil_to_array(gray).astype(np.uint8))
        actual_max_height = np.max(gray.getdata())
        self._heights = np.zeros([gray.height + 2, gray.width + 2])
        self._heights[1:-1, 1:-1] = img / actual_max_height * self._max_height

        self._get_vertices()
        litho = lp.Lithophane()
        pcd = litho.create_point_cloud_from_vertices(self._vertices, color=[0.5, 0.5, 1.0], display=False, show_normals=False)
        bound = pcd.get_max_bound()
        scale = self._max_size / max(bound[0], bound[1])
        pcd = pcd.scale(scale, pcd.get_center())

        poisson = True

        bound = pcd.get_max_bound()
        base_mesh = o3d.geometry.TriangleMesh.create_box(bound[0], bound[1], self._base_height + actual_max_height)

        if poisson:  # Mesh from poisson
            bpa_mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=10, linear_fit=False, n_threads=-1)
        else:  # Mesh from ball pivot
            distances = pcd.compute_nearest_neighbor_distance()
            avg_dist = np.mean(distances)
            radius = avg_dist * 3
            bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, o3d.utility.DoubleVector([radius, radius * 2]))

        bpa_mesh += base_mesh
        bpa_mesh = bpa_mesh.compute_vertex_normals()
        bpa_mesh = bpa_mesh.compute_triangle_normals()
        bpa_mesh.merge_close_vertices(0.1)
        # bpa_mesh = bpa_mesh.crop(o3d.geometry.AxisAlignedBoundingBox([0.0, 0.0, 0.0], [gray.height, gray.width, self._max_height + self._base_height]))
        bpa_mesh.remove_degenerate_triangles()
        bpa_mesh = bpa_mesh.remove_non_manifold_edges()
        # bpa_mesh.filter_smooth_taubin()
        o3d.visualization.draw_geometries([bpa_mesh], mesh_show_back_face=True)
        print(f'mesh.is_edge_manifold = {bpa_mesh.is_edge_manifold()}')
        print(f'mesh.is_vertex_manifold = {bpa_mesh.is_vertex_manifold()}')
        # print(f'mesh.is_watertight = {bpa_mesh.is_watertight()}')
        # bpa_mesh = self._simplify_mesh(bpa_mesh)
        o3d.io.write_triangle_mesh("C:/Cloud/Google/Fab/Artwork/nsfw.stl", bpa_mesh)

    def _get_vertices(self):
        vertices = []
        base_height = self._base_height

        x_limit = self._heights.shape[0]
        y_limit = self._heights.shape[1]

        for x in range(x_limit - 1):
            for y in range(y_limit - 1):
                if 0 < x < x_limit - 1 and 0 < y < y_limit - 1:
                    ht = self._heights[x][y]
                    vertices.append((float(x), float(y), float(base_height + ht)))
                    vertices.append((float(x), float(y+1), float(base_height + ht)))
                    # vertices.append((float(x), float(y), float(base_height)))
                    # vertices.append((float(x), float(y+1), float(base_height)))
                else:
                    vertices.append((float(x), float(y), 0.0))

        self._vertices = np.array(vertices)

    @staticmethod
    def _simplify_mesh(mesh_to_simplify):
        voxel_size = 0.5  # max(bpa_mesh.get_max_bound() - bpa_mesh.get_min_bound()) / 64
        print(f'voxel_size = {voxel_size:e}')
        print(
            f'Base mesh has {len(mesh_to_simplify.vertices)} vertices and {len(mesh_to_simplify.triangles)} triangles'
        )
        simple_mesh = mesh_to_simplify.simplify_vertex_clustering(
            voxel_size=voxel_size,
            contraction=o3d.geometry.SimplificationContraction.Average)
        simple_mesh = simple_mesh.compute_vertex_normals()
        simple_mesh = simple_mesh.compute_triangle_normals()
        print(
            f'Simplified mesh has {len(simple_mesh.vertices)} vertices and {len(simple_mesh.triangles)} triangles'
        )
        print(f'mesh.is_edge_manifold = {simple_mesh.is_edge_manifold()}')
        print(f'mesh.is_vertex_manifold = {simple_mesh.is_vertex_manifold()}')
        o3d.visualization.draw_geometries([simple_mesh], mesh_show_back_face=True)

        return simple_mesh


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
