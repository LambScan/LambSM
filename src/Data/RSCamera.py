import pyrealsense2 as rs


class RSCamera:
    def __init__(self):
        # Configure depth and color streams
        self.__pipeline__ = rs.pipeline()
        self.__config__ = rs.config()
        self.__config__.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.__config__.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.__profile__ = None
        self.__depth_profile__ = None
        self.__depth_intrinsics__ = None
        self.__decimate__ = rs.decimation_filter()
        self.__colorizer__ = rs.colorizer()

    def start(self):
        try:
            # Start streaming
            self.__pipeline__.start(self.__config__)

            # Get stream profile and camera intrinsics
            self.__profile__ = self.__pipeline__.get_active_profile()
            self.__depth_profile__ = rs.video_stream_profile(self.__profile__.get_stream(rs.stream.depth))

            self.__depth_intrinsics__ = self.__depth_profile__.get_intrinsics()
            w, h = self.__depth_intrinsics__.width, self.__depth_intrinsics__.height

            self.__decimate__.set_option(rs.option.filter_magnitude, 2 ** self.__decimate__)
            return True
        except Exception as e:
            print(e)
            return False

    def get_frame(self):
        try:
            # Wait for a coherent pair of frames: depth and color
            frames = self.__pipeline__.wait_for_frames()

            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()

            if not depth_frame or not color_frame:
                return None
            else:
                return color_frame, depth_frame
        except Exception as e:
            print(e)
            return None

    # Stop streaming
    def stop(self):
        self.__pipeline__.stop()

    def get_profile_intrinsics(self, profile):
        return rs.video_stream_profile(profile).get_intrinsics()

    def pointcloud(self):
        return rs.pointcloud()

    def deproject_pixel_to_point(self, intrinsics, x, y, d):
        return rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], d)


def __get_pointcloud__(color_frame, depth_frame):
    pointcloud = rs.pointcloud()
    pointcloud.map_to(color_frame)
    points = pointcloud.calculate(depth_frame)
    return points


