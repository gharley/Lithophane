import numpy as np
import open3d as o3d


class Lithophane:
    def __init__(self):
        pass

    def create_point_cloud_from_vertices(self, vertices, color=[0.0, 0.0, 0.0], normal_direction=[0.0, 0.0, 1.0], display=False):
        pcd = o3d.geometry.PointCloud()
        point_cloud = np.asarray(vertices)
        pcd.points = o3d.utility.Vector3dVector(point_cloud)
        pcd.paint_uniform_color(color)
        pcd.estimate_normals()
        pcd = pcd.normalize_normals()
        pcd.orient_normals_to_align_with_direction(normal_direction)

        if display:
            o3d.visualization.draw_geometries([pcd], point_show_normal=True)

        return pcd
