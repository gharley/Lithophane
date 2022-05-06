import numpy as np
import pyvista as pv
from PIL import ImageOps

_THRESHOLD = 1000000


class Lithophane:
    def __init__(self):
        pass

    @staticmethod
    def create_mesh_from_point_cloud(pcd, base):
        mesh = pcd.delaunay_2d(progress_bar=True)
        if base is not None: mesh += base

        if mesh.n_faces > _THRESHOLD:
            mesh = mesh.decimate_pro(1.0 - (_THRESHOLD / mesh.n_faces))

        return mesh

    @staticmethod
    def create_point_cloud_from_vertices(vertices, props):
        pcd = pv.PolyData(vertices)

        bounds = pcd.bounds
        x_max = bounds[1]
        y_max = bounds[3]
        height = (props.minHeight + props.baseHeight) * props.numSamples
        base = pv.Cube(center=(x_max / 2, y_max / 2, -height / 2), x_length=x_max, y_length=y_max, z_length=height)
        base = base.triangulate()

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
        gray = ImageOps.scale(ImageOps.grayscale(img), scale, True)
        if props.chkInvert: gray = ImageOps.invert(gray)
        if props.chkMirror: gray = ImageOps.mirror(gray)
        data = gray.getdata()
        actual_max_height = np.max(data)
        heights = np.zeros([gray.height + 2, gray.width + 2])
        heights[1:-1, 1:-1] = gray / actual_max_height * props.maxHeight

        return self._get_vertices(np.rot90(heights, axes=(1, 0)), props)

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
