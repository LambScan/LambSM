# TODO: Everything
import cv2
import open3d as o3


def show_3D_image_from_file(file):
    pc = o3.io.read_point_cloud(file)
    vis = o3.visualization.Visualizer()
    vis.create_window()
    vis.add_geometry(pc)
    vis.run()
    vis.destroy_window()


# TODO
__default_profile__ = None


def show_3D_image_from_pngs(file_color, file_depth, profile=__default_profile__):
    source_color = o3.io.read_image(file_color)
    source_depth = o3.io.read_image(file_depth)
    pc, _, _ = rgbd2pcd(profile, rs2o3RGBD(source_color, source_depth))
    vis = o3.visualization.Visualizer()
    vis.create_window()
    vis.add_geometry(pc)
    vis.run()
    vis.destroy_window()


def rs2o3RGBD(color_image, depth_image):
    color_img_2 = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
    img_depth = o3.geometry.Image(depth_image)
    img_color = o3.geometry.Image(color_img_2)
    rgbd = o3.geometry.RGBDImage.create_rgbd_image_from_color_and_depth(img_color, img_depth,
                                                                        convert_rgb_to_intensity=False)
    return rgbd


def rgbd2pcd(profile, rgbd):
    pointcloud = o3.geometry.PointCloud()

    intrinsics = profile.as_video_stream_profile().get_intrinsics()
    pinhole_camera_intrinsic = o3.camera.PinholeCameraIntrinsic(intrinsics.width, intrinsics.height, intrinsics.fx,
                                                                intrinsics.fy,
                                                                intrinsics.ppx, intrinsics.ppy)

    pc = o3.geometry.PointCloud.create_point_cloud_from_rgbd_image(rgbd, pinhole_camera_intrinsic)
    pc.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
    pointcloud.points = pc.points
    pointcloud.colors = pc.colors

    return pointcloud, pointcloud.points, pointcloud.colors
