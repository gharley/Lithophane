import numpy as np
import pyvista as pv
from PIL import ImageOps

FACE_THRESHOLD = 1000000


class Lithophane:
    def __init__(self):
        pass

    @staticmethod
    def create_mesh_from_point_cloud(pcd, props):
        props.statusBar.showMessage('Generating Mesh')
        mesh = pcd.delaunay_2d(progress_bar=True)

        if mesh.n_faces_strict > FACE_THRESHOLD:
            props.statusBar.showMessage('Decimating Mesh')
            try:
                mesh = mesh.decimate_pro(1.0 - (FACE_THRESHOLD / mesh.n_faces_strict), progress_bar=True)
            except ():
                props.statusBar.showMessage('Error decimating mesh')

        return mesh

    @staticmethod
    def create_point_cloud_from_vertices(vertices, props):
        props.statusBar.showMessage('Generating Point Cloud')
        pcd = pv.PolyData(vertices)

        return pcd

    @staticmethod
    def _get_vertices(heights, props):
        vertices = []
        for index, value in np.ndenumerate(heights):
            vertices.append((index[0], index[1], (value + props.minHeight) * props.numSamples))

        return np.array(vertices)

    def generate_mesh(self, props):
        vertices = self.prepare_image(props)
        pcd = self.create_point_cloud_from_vertices(vertices, props)

        mesh = self.create_mesh_from_point_cloud(pcd, props)
        mesh = self.scale_to_final_size(mesh, props)

        try:
            if props.chkSmooth:
                props.statusBar.showMessage('Smoothing Mesh')
                n_iter = props.sldSmooth * 20
                mesh = mesh.smooth(n_iter, progress_bar=True)
        except ():
            props.statusBar.showMessage('Error smoothing mesh')

        try:
            props.statusBar.showMessage('Filling Holes')
            temp = mesh.fill_holes(1000, progress_bar=True)
            mesh = temp
        except ():
            props.statusBar.showMessage('Error filling holes')

        bounds = mesh.bounds
        x_max = bounds[1]
        y_max = bounds[3]
        height = props.baseHeight
        base = pv.Cube(center=(x_max / 2, y_max / 2, -height / 2), x_length=x_max, y_length=y_max, z_length=height)
        base = base.triangulate()

        props.statusBar.showMessage('')
        return mesh + base

    def prepare_image(self, props):
        img = props.img

        divisor = img.width if props.btnWidth else img.height
        scale = props.maxSize * props.numSamples / divisor
        gray = ImageOps.scale(ImageOps.grayscale(img), scale, True)
        if props.chkInvert: gray = ImageOps.invert(gray)
        if props.chkMirror: gray = ImageOps.mirror(gray)

        data = gray.getdata()
        data -= np.min(data)  # Adjust to lowest value in case not zero
        gray.putdata(data)
        actual_max_height = np.max(data)

        heights = np.zeros([gray.height + 2, gray.width + 2])
        heights[1:-1, 1:-1] = gray / actual_max_height * props.maxHeight

        return self._get_vertices(np.rot90(heights, axes=(1, 0)), props)

    @staticmethod
    def scale_to_final_size(mesh, props):
        bound = mesh.bounds
        divisor = bound[1] if props.btnWidth else bound[3]
        scale = props.maxSize / divisor
        matrix = np.array([
            [scale, 0, 0, 0],
            [0, scale, 0, 0],
            [0, 0, scale, 0],
            [0, 0, 0, 1]])

        props.statusBar.showMessage('Scaling To Final Size')
        return mesh.transform(matrix, progress_bar=True)
