import numpy as np
import open3d as o3d


class Lithophane:
    def __init__(self):
        pass

    def create_point_cloud_from_vertices(self, vertices, color=[0.0, 0.0, 0.0], normal_direction=[0.0, 0.0, 1.0], display=False, show_normals=False, show_back=False):
        pcd = o3d.geometry.PointCloud()
        point_cloud = np.asarray(vertices)
        pcd.points = o3d.utility.Vector3dVector(point_cloud)
        pcd.paint_uniform_color(color)
        pcd.estimate_normals()
        # pcd.orient_normals_consistent_tangent_plane(0)
        pcd.orient_normals_to_align_with_direction(normal_direction)
        # pcd.orient_normals_towards_camera_location(pcd.get_center())
        pcd = pcd.normalize_normals()

        if display:
            o3d.visualization.draw_geometries([pcd], point_show_normal=show_normals, mesh_show_back_face=show_back)

        return pcd
