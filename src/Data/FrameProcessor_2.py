import math
import time
from datetime import datetime
import os
import PySimpleGUI as sg
import sys
import pyrealsense2 as rs
import numpy as np
import cv2


def mouse_cb(event, x, y, flags, param, processor):
    if event == cv2.EVENT_LBUTTONDOWN:
        processor.mouse_btns[0] = True

    if event == cv2.EVENT_LBUTTONUP:
        processor.mouse_btns[0] = False

    if event == cv2.EVENT_RBUTTONDOWN:
        processor.mouse_btns[1] = True

    if event == cv2.EVENT_RBUTTONUP:
        processor.mouse_btns[1] = False

    if event == cv2.EVENT_MBUTTONDOWN:
        processor.mouse_btns[2] = True

    if event == cv2.EVENT_MBUTTONUP:
        processor.mouse_btns[2] = False

    if event == cv2.EVENT_MOUSEMOVE:

        h, w = __out__.shape[:2]
        dx, dy = x - processor.prev_mouse[0], y - processor.prev_mouse[1]

        if processor.mouse_btns[0]:
            processor.yaw += float(dx) / w * 2
            processor.pitch -= float(dy) / h * 2

        elif processor.mouse_btns[1]:
            dp = np.array((dx / w, dy / h, 0), dtype=np.float32)
            processor.translation -= np.dot(processor.rotation, dp)

        elif processor.mouse_btns[2]:
            dz = math.sqrt(dx ** 2 + dy ** 2) * math.copysign(0.01, -dy)
            processor.translation[2] += dz
            processor.distance -= dz

    if event == cv2.EVENT_MOUSEWHEEL:
        dz = math.copysign(0.1, flags)
        processor.translation[2] += dz
        processor.distance -= dz

    processor.prev_mouse = (x, y)


def project(v):
    """project 3d vector array to 2d"""
    h, w = __out__.shape[:2]
    view_aspect = float(h) / w

    # ignore divide by zero for invalid depth
    with np.errstate(divide='ignore', invalid='ignore'):
        proj = v[:, :-1] / v[:, -1, np.newaxis] * \
               (w * view_aspect, h) + (w / 2.0, h / 2.0)

    # near clipping
    znear = 0.03
    proj[v[:, 2] < znear] = np.nan
    return proj


def view(v, processor):
    """apply view transformation on vector array"""
    return np.dot(v - processor.pivot, processor.rotation) + processor.pivot - processor.translation


def line3d(out, pt1, pt2, color=(0x80, 0x80, 0x80), thickness=1):
    """draw a 3d line from pt1 to pt2"""
    p0 = project(pt1.reshape(-1, 3))[0]
    p1 = project(pt2.reshape(-1, 3))[0]
    if np.isnan(p0).any() or np.isnan(p1).any():
        return
    p0 = tuple(p0.astype(int))
    p1 = tuple(p1.astype(int))
    rect = (0, 0, out.shape[1], out.shape[0])
    inside, p0, p1 = cv2.clipLine(rect, p0, p1)
    if inside:
        cv2.line(out, p0, p1, color, thickness, cv2.LINE_AA)


def grid(out, pos, processor, rotation=np.eye(3), size=1, n=10, color=(0x80, 0x80, 0x80)):
    """draw a grid on xz plane"""
    pos = np.array(pos)
    s = size / float(n)
    s2 = 0.5 * size
    for i in range(0, n + 1):
        x = -s2 + i * s
        line3d(out, view(pos + np.dot((x, 0, -s2), rotation), processor),
               view(pos + np.dot((x, 0, s2), rotation), processor), color)
    for i in range(0, n + 1):
        z = -s2 + i * s
        line3d(out, view(pos + np.dot((-s2, 0, z), rotation), processor),
               view(pos + np.dot((s2, 0, z), rotation), processor), color)


def axes(out, pos, rotation=np.eye(3), size=0.075, thickness=2):
    """draw 3d axes"""
    line3d(out, pos, pos +
           np.dot((0, 0, size), rotation), (0xff, 0, 0), thickness)
    line3d(out, pos, pos +
           np.dot((0, size, 0), rotation), (0, 0xff, 0), thickness)
    line3d(out, pos, pos +
           np.dot((size, 0, 0), rotation), (0, 0, 0xff), thickness)


def frustum(out, intrinsics, processor, color=(0x40, 0x40, 0x40)):
    """draw camera's frustum"""
    orig = view([0, 0, 0], processor)
    w, h = intrinsics.width, intrinsics.height

    for d in range(1, 6, 2):
        def get_point(x, y):
            p = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], d)
            line3d(out, orig, view(p, processor), color)
            return p

        top_left = get_point(0, 0)
        top_right = get_point(w, 0)
        bottom_right = get_point(w, h)
        bottom_left = get_point(0, h)

        line3d(out, view(top_left, processor), view(top_right, processor), color)
        line3d(out, view(top_right, processor), view(bottom_right, processor), color)
        line3d(out, view(bottom_right, processor), view(bottom_left, processor), color)
        line3d(out, view(bottom_left, processor), view(top_left, processor), color)


def pointcloud(out, verts, texcoords, color, processor, painter=True):
    """draw point cloud with optional painter's algorithm"""
    if painter:
        # Painter's algo, sort points from back to front

        # get reverse sorted indices by z (in view-space)
        # https://gist.github.com/stevenvo/e3dad127598842459b68
        v = view(verts, processor)
        s = v[:, 2].argsort()[::-1]
        proj = project(v[s])
    else:
        proj = project(view(verts, processor))

    if processor.scale:
        proj *= 0.5 ** processor.decimate

    h, w = out.shape[:2]

    # proj now contains 2d image coordinates
    j, i = proj.astype(np.uint32).T

    # create a mask to ignore out-of-bound indices
    im = (i >= 0) & (i < h)
    jm = (j >= 0) & (j < w)
    m = im & jm

    cw, ch = color.shape[:2][::-1]
    if painter:
        # sort texcoord with same indices as above
        # texcoords are [0..1] and relative to top-left pixel corner,
        # multiply by size and add 0.5 to center
        v, u = (texcoords[s] * (cw, ch) + 0.5).astype(np.uint32).T
    else:
        v, u = (texcoords * (cw, ch) + 0.5).astype(np.uint32).T
    # clip texcoords to image
    np.clip(u, 0, ch - 1, out=u)
    np.clip(v, 0, cw - 1, out=v)

    # perform uv-mapping
    out[i[m], j[m]] = color[u[m], v[m]]
    return out


class FrameProcessor:

    def __init__(self, camera, *args, **kwargs):
        self.camera = camera
        self.pitch, self.yaw = math.radians(-10), math.radians(-15)
        self.translation = np.array([0, 0, -1], dtype=np.float32)
        self.distance = 2
        self.prev_mouse = 0, 0
        self.mouse_btns = [False, False, False]
        self.decimate = 1
        self.scale = True
        self.color = True
        self.__image2D__ = True  # True: image2D, False: image3D

    def is2DMode(self):
        return self.__image2D__

    def is3DMode(self):
        return not self.__image2D__

    def changeMode(self, image2D=None, image3D=False):
        """
        Changes to process the image as two 2D images or combine them and process as one 3D image
        It processes by default the 2D image
        :param image2D: True process 2D image, False process 3D image
        :param image3D: param image2D has priority over this param, this is the opposite of it
        :return:
        """
        if image2D is not None:
            self.__image2D__ = image2D
        else:
            self.__image2D__ = not image3D

    def reset(self):
        self.pitch, self.yaw, self.distance = 0, 0, 2
        self.translation[:] = 0, 0, -1

    @property
    def rotation(self):
        Rx, _ = cv2.Rodrigues((self.pitch, 0, 0))
        Ry, _ = cv2.Rodrigues((0, self.yaw, 0))
        return np.dot(Ry, Rx).astype(np.float32)

    @property
    def pivot(self):
        return self.translation + np.array((0, 0, self.distance), dtype=np.float32)

    def process(self, color_frame, depth_frame):
        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        if self.__image2D__:
            return color_image, depth_image
        else:

            # We need to keep the original depth_frame to save
            # the data; however, the visualization works better with
            # the depth_frame processed; so we keep both
            depth_frame_viewer = self.camera.__decimate__.process(depth_frame)

            # Grab new intrinsics (may be changed by decimation)
            # depth_intrinsics = rs.video_stream_profile(
            #   depth_frame.profile).get_intrinsics()

            depth_intrinsics = self.camera.get_profile_intrinsics(depth_frame.profile)
            w, h = depth_intrinsics.width, depth_intrinsics.height

            global __out__
            __out__ = np.empty((h, w, 3), dtype=np.uint8)

            depth_image_viewer = np.asanyarray(depth_frame_viewer.get_data())

            depth_colormap = np.asanyarray(
                self.camera.__colorizer__.colorize(depth_frame_viewer).get_data())

            if self.color:
                mapped_frame, color_source = color_frame, color_image
            else:
                mapped_frame, color_source = depth_image_viewer, depth_colormap

            # pc = rs.pointcloud()
            pc = self.camera.pointcloud()
            pc.map_to(mapped_frame)
            points = pc.calculate(depth_frame_viewer)

            # Pointcloud data to arrays
            v, t = points.get_vertices(), points.get_texture_coordinates()
            verts = np.asanyarray(v).view(np.float32).reshape(-1, 3)  # xyz
            texcoords = np.asanyarray(t).view(np.float32).reshape(-1, 2)  # uv

            # Render
            now = time.time()

            __out__.fill(0)

            grid(__out__, (0, 0.5, 1), self, size=1, n=10)
            frustum(__out__, depth_intrinsics, self)
            axes(__out__, view([0, 0, 0], self), self.rotation, size=0.1, thickness=1)

            if not self.scale or __out__.shape[:2] == (h, w):
                __out__ = pointcloud(__out__, verts, texcoords, color_source, self)
            else:
                tmp = np.zeros((h, w, 3), dtype=np.uint8)
                __out__ = pointcloud(tmp, verts, texcoords, color_source, self)
                tmp = cv2.resize(
                    tmp, __out__.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)
                np.putmask(__out__, tmp > 0, tmp)

            if any(self.mouse_btns):
                axes(__out__, view(self.pivot, self), self.rotation, thickness=4)

            dt = time.time() - now

            return __out__

#
# if __name__ == "__main__":
#     state = AppState()
#
#     sg.ChangeLookAndFeel('DarkTanBlue')
#     # sg.LOOK_AND_FEEL_TABLE
#     # define the window layout
#     layout = [[sg.Text('OpenCV Demo', size=(40, 1), justification='center', font='Helvetica 20')],
#               [sg.Image(filename='', key='image')],
#               [sg.Button('Record', size=(10, 1), font='Helvetica 14'),
#                sg.Button('Stop', size=(10, 1), font='Any 14'),
#                sg.Button('Exit', size=(10, 1), font='Helvetica 14'), ]]
#
#     # create the window and show it without the plot
#     window = sg.Window('Demo Application - OpenCV Integration', layout,
#                        location=(800, 400))
#
#     # ---===--- Event LOOP Read and display frames, operate the GUI --- #
#     # cap = cv2.VideoCapture(0)
#     recording = False
#
#     # Configure depth and color streams
#     pipeline = rs.pipeline()
#     config = rs.config()
#     config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
#     config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
#
#     # Start streaming
#     pipeline.start(config)
#
#     # Get stream profile and camera intrinsics
#     profile = pipeline.get_active_profile()
#     depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
#
#     depth_intrinsics = depth_profile.get_intrinsics()
#     w, h = depth_intrinsics.width, depth_intrinsics.height
#
#     # Processing blocks
#     pc = rs.pointcloud()
#
#     decimate = rs.decimation_filter()
#     decimate.set_option(rs.option.filter_magnitude, 2 ** state.decimate)
#     colorizer = rs.colorizer()
#
#     # cv2.namedWindow(state.WIN_NAME, cv2.WINDOW_AUTOSIZE)
#     # cv2.resizeWindow(state.WIN_NAME, w, h)
#     # cv2.resizeWindow(state.WIN_NAME, 640, 480)
#     # cv2.setMouseCallback(state.WIN_NAME, mouse_cb)
#
#     out = np.empty((h, w, 3), dtype=np.uint8)
#
#     done = False
#
#     frames_saved = 0
#
#     id_crotal_aux = None
#     id_crotal = None
#     while id_crotal_aux is None:
#         id_crotal_aux = pyautogui.prompt('Please, insert the id crotal of the lamb:')
#
#     while True:
#         # Grab camera data
#         if not state.paused:
#             # Wait for a coherent pair of frames: depth and color
#             frames = pipeline.wait_for_frames()
#             # frames = pipeline.wait_for_frames(timeout_ms=0)
#
#             depth_frame = frames.get_depth_frame()
#             color_frame = frames.get_color_frame()
#
#             # We need to keep the original depth_frame to save
#             # the data; however, the visualization works better with
#             # the depth_frame processed; so we keep both
#             depth_frame_viewer = decimate.process(depth_frame)
#
#             # Grab new intrinsics (may be changed by decimation)
#             depth_intrinsics = rs.video_stream_profile(
#                 depth_frame.profile).get_intrinsics()
#             w, h = depth_intrinsics.width, depth_intrinsics.height
#
#             depth_image = np.asanyarray(depth_frame.get_data())
#             depth_image_viewer = np.asanyarray(depth_frame_viewer.get_data())
#             color_image = np.asanyarray(color_frame.get_data())
#
#             depth_colormap = np.asanyarray(
#                 colorizer.colorize(depth_frame_viewer).get_data())
#
#             if state.color:
#                 mapped_frame, color_source = color_frame, color_image
#             else:
#                 mapped_frame, color_source = depth_image_viewer, depth_colormap
#
#             pc.map_to(mapped_frame)
#             points = pc.calculate(depth_frame_viewer)
#
#             # Pointcloud data to arrays
#             v, t = points.get_vertices(), points.get_texture_coordinates()
#             verts = np.asanyarray(v).view(np.float32).reshape(-1, 3)  # xyz
#             texcoords = np.asanyarray(t).view(np.float32).reshape(-1, 2)  # uv
#
#             event, values = window.Read(timeout=20)
#
#             if event == 'Exit' or event is None:
#                 sys.exit(0)
#             elif event == 'Record':
#                 recording = True
#             elif event == 'Stop':
#                 recording = False
#                 img = np.full((480, 640), 255)
#                 imgbytes = cv2.imencode('.png', img)[1].tobytes()  # this is faster, shorter and needs less includes
#                 window.FindElement('image').Update(data=imgbytes)
#
#         # Render
#         now = time.time()
#
#         out.fill(0)
#
#         grid(out, (0, 0.5, 1), size=1, n=10)
#         frustum(out, depth_intrinsics)
#         axes(out, view([0, 0, 0]), state.rotation, size=0.1, thickness=1)
#
#         if not state.scale or out.shape[:2] == (h, w):
#             pointcloud(out, verts, texcoords, color_source)
#         else:
#             tmp = np.zeros((h, w, 3), dtype=np.uint8)
#             pointcloud(tmp, verts, texcoords, color_source)
#             tmp = cv2.resize(
#                 tmp, out.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)
#             np.putmask(out, tmp > 0, tmp)
#
#         if any(state.mouse_btns):
#             axes(out, view(state.pivot), state.rotation, thickness=4)
#
#         dt = time.time() - now
#
#         # cv2.setWindowTitle(
#         #     state.WIN_NAME, "RealSense (%dx%d) %dFPS (%.2fms) %s" %
#         #                     (w, h, 1.0 / dt, dt * 1000, "PAUSED" if state.paused else ""))
#
#         if recording:
#             imgbytes_color = cv2.imencode('.png', out)[1].tobytes()
#             window.FindElement('image').Update(data=imgbytes_color)
#
#         # cv2.imshow(state.WIN_NAME, out)
#
#         key = cv2.waitKey(1)
#
#         if key == ord("r"):
#             state.reset()
#
#         if key == ord("p"):
#             state.paused ^= True
#
#         if key == ord("d"):
#             state.decimate = (state.decimate + 1) % 3
#             decimate.set_option(rs.option.filter_magnitude, 2 ** state.decimate)
#
#         if key == ord("z"):
#             state.scale ^= True
#
#         if key == ord("c"):
#             state.color ^= True
#
#         # SAVE A SCREENSHOT IN PNG FILE
#         if key == ord("s"):
#             cv2.imwrite('./out.png', out)
#
#         # EXPORT IMG TO PLY FILE
#         if key == ord("e"):
#             frames_saved, id_crotal_aux = take_dataset_frame(color_image, depth_image, frames_saved, id_crotal_aux)
#
#         if key == ord("j"):
#             frames_saved += 1
#
#         if key == ord("n"):
#             id_crotal = None
#             while id_crotal_aux is None:
#                 id_crotal_aux = pyautogui.prompt('Please, insert the id crotal of the lamb:')
#
#         # if key in (27, ord("q")) or cv2.getWindowProperty(state.WIN_NAME, cv2.WND_PROP_VISIBLE) < 1:
#         #     done = True
#         #     break
#
#         frames_saved, id_crotal = save_frames(frames_saved, id_crotal)
#
#     stop_streaming(pipeline)