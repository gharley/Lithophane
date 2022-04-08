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

        ui_file = QFile('mainwindow.ui')
        ui_file.open(QFile.ReadOnly)
        self._main = uic.loadUi(ui_file, self)
        ui_file.close()

        self.process_image("C:/Cloud/Google/Fab/Artwork/nsfw.png")

        self.imgLayout = self._main.imgLayout
        fig = Figure(figsize=(self._img.width, self._img.height))
        fig.figimage(self._img, cmap='gray')
        static_canvas = FigureCanvas(fig)
        self._main.imgLayout.addWidget(static_canvas)

        # dynamic_canvas = FigureCanvas(Figure(figsize=(self._img.width, self._img.height)))
        # self.imgLayout.addWidget(dynamic_canvas)

    def process_image(self, filename):
        self._img = Image.open(filename)

        scale = self._max_size / max(self._img.width, self._img.height)
        self._img = ImageOps.scale(self._img, scale, True)

        gray = ImageOps.grayscale(self._img)
        img = o3d.geometry.Image(matplotlib.image.pil_to_array(gray))
        self._heights = np.zeros([gray.height + 2, gray.width + 2])
        self._heights[1:-1, 1:-1] = img / np.max(gray.getdata()) * self._max_height

        self._get_vertices()

        pcd = o3d.geometry.PointCloud()
        point_cloud = np.asarray(self._vertices)
        pcd.points = o3d.utility.Vector3dVector(point_cloud)
        pcd.paint_uniform_color([0.5, 0.5, 1.0])
        pcd.estimate_normals()
        pcd = pcd.normalize_normals()
        # o3d.visualization.draw_geometries([pcd], point_show_normal=True)
        pcd.orient_normals_to_align_with_direction([0.0, 0.0, 1.0])
        aabb = pcd.get_axis_aligned_bounding_box()
        aabb.color = (1, 0, 0)
        obb = pcd.get_oriented_bounding_box()
        obb.color = (0, 1, 0)
        o3d.visualization.draw_geometries([pcd], point_show_normal=True)
        # voxel_grid = o3d.geometry.VoxelGrid.create_dense([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.4, float(self._img.width), float(self._img.height), self._max_height)
        # voxel_grid = voxel_grid.carve_depth_map(img, o3d.camera.PinholeCameraParameters().extrinsic)
        # o3d.visualization.draw_geometries([voxel_grid, pcd], mesh_show_back_face=True)
        poisson = True

        if poisson:  # Mesh from poisson
            bpa_mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=10, scale=1.0, linear_fit=True, n_threads=-1)

        else:  # Mesh from ball pivot
            distances = pcd.compute_nearest_neighbor_distance()
            avg_dist = np.mean(distances)
            radius = avg_dist * 3
            bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, o3d.utility.DoubleVector([radius, radius * 2]))

        bpa_mesh = bpa_mesh.compute_vertex_normals()
        bpa_mesh = bpa_mesh.compute_triangle_normals()
        bpa_mesh.remove_degenerate_triangles()
        # bpa_mesh = bpa_mesh.remove_non_manifold_edges()
        # bpa_mesh.filter_smooth_taubin()
        o3d.visualization.draw_geometries([bpa_mesh], mesh_show_back_face=False)
        print(f'mesh.is_edge_manifold = {bpa_mesh.is_edge_manifold()}')
        print(f'mesh.is_vertex_manifold = {bpa_mesh.is_vertex_manifold()}')
        # print(f'mesh.is_watertight = {bpa_mesh.is_watertight()}')
        # bpa_mesh = self._simplify_mesh(bpa_mesh)
        o3d.io.write_triangle_mesh("C:/Cloud/Google/Fab/Artwork/nsfw.stl", bpa_mesh)

    def _get_vertices(self):
        self._vertices = np.zeros([self._heights.size, 3], np.dtype(np.float64, (3,)))
        vertices = []
        base = []
        for x in range(self._heights.shape[0]):
            for y in range(self._heights.shape[1]):
                base_height = self._base_height
                height = self._heights[x][y] + base_height
                # vertices.append((float(x), float(y), 0.0))
                vertices.append((float(x), float(y), height))
                # base.append((float(x), float(y), 0.0))

        self._vertices = np.array(vertices)
        # self._vertices = np.append(np.array(vertices), np.array(base), axis=0)

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
