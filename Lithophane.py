import math

import numpy as np
import pyvista as pv
from PIL import Image, ImageOps


class Lithophane:
    def __init__(self):
        pass

    def create_mesh_from_point_cloud(self, pcd, props):
        mesh = pcd.delaunay_2d()
        mesh.plot(show_edges=True, show_grid=True)

        return mesh

    @staticmethod
    def create_point_cloud_from_vertices(vertices, props, color=[0.0, 0.0, 0.0], display=False):
        pcd = pv.PolyData(vertices)

        if 0.0 < props.minHeight or 0.0 < props.baseHeight:
            bounds = pcd.bounds
            height = (props.minHeight + props.baseHeight) * props.numSamples
            base = pv.Cube(center=(bounds[0] / 2, bounds[1] / 2, height / 2), x_length=bounds[0], y_length=bounds[1], z_length=height)
            pcd = pcd.merge(base)

        if display:
            plotter = pv.Plotter()
            plotter.add_mesh(pcd, color='maroon', point_size=10.0, render_points_as_spheres=True)
            plotter.show_grid()
            plotter.show()

        return pcd

    @staticmethod
    def _get_vertices(heights, props):
        vertices = []
        for index, value in np.ndenumerate(heights):
            vertices.append((index[0], index[1], (value + props.minHeight) * props.numSamples))

        return np.array(vertices)

    def prepare_image(self, filename, props):
        img = Image.open(filename)

        scale = props.maxSize * props.numSamples / max(img.width, img.height)
        gray = ImageOps.scale(ImageOps.grayscale(img), scale, True)
        gray = ImageOps.invert(gray)
        data = gray.getdata()
        actual_max_height = np.max(data)
        heights = np.zeros([gray.height + 2, gray.width + 2])
        heights[1:-1, 1:-1] = gray / actual_max_height * props.maxHeight

        return self._get_vertices(heights, props)

    @staticmethod
    def scale_to_final_size(pcd, props):
        bound = pcd.bounds
        scale = props.maxSize / max(bound[1], bound[3])
        matrix = np.array([
            [scale, 0,  0,  0],
            [0,  scale, 0,  0],
            [0,  0,  scale, 0],
            [0,  0,  0,  1]])

        return pcd.transform(matrix)
