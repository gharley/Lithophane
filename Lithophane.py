import math

import numpy as np
import pyvista as pv
from PIL import ImageOps


class Lithophane:
    def __init__(self):
        pass

    @staticmethod
    def create_mesh_from_point_cloud(pcd, base):
        mesh = pcd.delaunay_2d()
        if base is not None: mesh += base
        # mesh.plot(show_edges=True, show_grid=True)

        return mesh

    @staticmethod
    def create_point_cloud_from_vertices(vertices, props, display=False):
        pcd = pv.PolyData(vertices)

        if 0.0 < props.minHeight or 0.0 < props.baseHeight:
            bounds = pcd.bounds
            x_max = bounds[1]
            y_max = bounds[3]
            height = (props.minHeight + props.baseHeight) * props.numSamples
            base = pv.Cube(center=(x_max / 2, y_max / 2, -height / 2), x_length=x_max, y_length=y_max, z_length=height)
            base = base.triangulate()
        else:
            base = None

        if display:
            plotter = pv.Plotter()
            plotter.add_mesh(pcd, color='maroon', point_size=10.0, render_points_as_spheres=True)
            plotter.show_grid()
            plotter.show()

        return pcd, base

    @staticmethod
    def _get_vertices(heights, props):
        vertices = []
        for index, value in np.ndenumerate(heights):
            vertices.append((index[0], index[1], (value + props.minHeight) * props.numSamples))

        return np.array(vertices)

    def prepare_image(self, props):
        img = props.img

        scale = props.maxSize * props.numSamples / max(img.width, img.height)
        gray = ImageOps.scale(ImageOps.grayscale(img), scale, True)  # .rotate(-90)  # Not sure why rotate is necessary
        if props.chkInvert: gray = ImageOps.invert(gray)
        if props.chkMirror: gray = ImageOps.mirror(gray)
        data = gray.getdata()
        actual_max_height = np.max(data)
        heights = np.zeros([gray.height + 2, gray.width + 2])
        heights[1:-1, 1:-1] = gray / actual_max_height * props.maxHeight

        return self._get_vertices(heights, props)

    @staticmethod
    def scale_to_final_size(mesh, props):
        bound = mesh.bounds
        scale = props.maxSize / max(bound[1], bound[3])
        matrix = np.array([
            [scale, 0, 0, 0],
            [0, scale, 0, 0],
            [0, 0, scale, 0],
            [0, 0, 0, 1]])

        return mesh.transform(matrix)
