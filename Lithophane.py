import math

import numpy as np
import open3d as o3d
from PIL import Image, ImageOps


class Lithophane:
    def __init__(self):
        pass

    def create_mesh_from_point_cloud(self, pcd, base_height, max_height):
        voxel_size = 1000000 / np.asarray(pcd.points).size
        # pcd = pcd.random_down_sample(voxel_size)
        # pcd = pcd.uniform_down_sample(math.ceil(1/voxel_size))
        pcd = pcd.voxel_down_sample(voxel_size)
        pcd.estimate_normals()
        mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=10, linear_fit=False, n_threads=-1)

        distance =0.1
        bound = pcd.get_max_bound()
        if 0 < base_height:
            base_mesh = o3d.geometry.TriangleMesh.create_box(bound[0], bound[1], base_height)
            base_mesh = base_mesh.compute_vertex_normals()
            base_mesh = base_mesh.compute_triangle_normals()
            mesh += base_mesh

        mesh = mesh.remove_duplicated_vertices()
        mesh.remove_degenerate_triangles()
        mesh = mesh.remove_duplicated_triangles()
        mesh = mesh.compute_vertex_normals()
        mesh = mesh.compute_triangle_normals()
        # mesh.merge_close_vertices(distance)
        mesh = mesh.crop(o3d.geometry.AxisAlignedBoundingBox([0.0, 0.0, 0.0], [bound[0], bound[1], max_height + base_height]))
        # mesh = bpa_mesh.remove_non_manifold_edges()
        mesh.filter_smooth_taubin()
        # print(f'mesh.is_edge_manifold = {mesh.is_edge_manifold()}')
        # print(f'mesh.is_vertex_manifold = {mesh.is_vertex_manifold()}')
        # print(f'mesh.is_watertight = {mesh.is_watertight()}')
        o3d.visualization.draw_geometries([mesh], mesh_show_back_face=True)
        mesh = self._simplify_mesh(mesh, voxel_size)

        return mesh

    @staticmethod
    def create_point_cloud_from_vertices(vertices, color=[0.0, 0.0, 0.0], normal_direction=[0.0, 0.0, 1.0], display=False, show_normals=False, show_back=False):
        pcd = o3d.geometry.PointCloud()
        point_cloud = np.asarray(vertices)
        pcd.points = o3d.utility.Vector3dVector(point_cloud)
        pcd.paint_uniform_color(color)
        pcd.estimate_normals()
        pcd.orient_normals_to_align_with_direction(normal_direction)
        pcd = pcd.normalize_normals()

        if display:
            o3d.visualization.draw_geometries([pcd], point_show_normal=show_normals, mesh_show_back_face=show_back)

        return pcd

    @staticmethod
    def _get_vertices(heights, base_height):
        vertices = []

        x_limit = heights.shape[0]
        y_limit = heights.shape[1]

        for x in range(x_limit - 1):
            for y in range(y_limit - 1):
                if 0 < x < x_limit - 1 and 0 < y < y_limit - 1:
                    ht = heights[x][y]
                    vertices.append((float(x), float(y), float(base_height + ht)))
                    vertices.append((float(x), float(y), float(base_height)))
                else:
                    vertices.append((float(x), float(y), 0.0))

        return np.array(vertices)

    def prepare_image(self, filename, base_height, max_height, max_size, samples):
        img = Image.open(filename)

        scale = max_size / min(img.width, img.height) * samples
        gray = ImageOps.scale(ImageOps.grayscale(img), scale, True).rotate(-90)
        gray = ImageOps.invert(gray)
        actual_max_height = np.max(gray.getdata())
        heights = np.zeros([gray.height + 2, gray.width + 2])
        heights[1:-1, 1:-1] = gray / actual_max_height * max_height

        return self._get_vertices(heights, base_height)

    @staticmethod
    def scale_to_final_size(pcd, max_size):
        bound = pcd.get_max_bound()
        scale = max_size / max(bound[0], bound[1])
        matrix = np.array([
            [scale, 0,  0,  0],
            [0,  scale, 0,  0],
            [0,  0,  1.0, 0],
            [0,  0,  0,  1]])

        return pcd.transform(matrix)

    @staticmethod
    def _simplify_mesh(mesh, voxel_size=0.5):
        print(f'voxel_size = {voxel_size:e}')
        print(
            f'Base mesh has {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles'
        )
        simple_mesh = mesh.simplify_vertex_clustering(
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
