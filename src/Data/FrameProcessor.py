import math
import time

import cv2
import numpy as np
import pyrealsense2 as rs

__state__ = 0
out = 0


class __State__:

    def __init__(self, *args, **kwargs):
        self.pitch, self.yaw = math.radians(-10), math.radians(-15)
        self.translation = np.array([0, 0, -1], dtype=np.float32)
        self.distance = 2
        self.prev_mouse = 0, 0
        self.mouse_btns = [False, False, False]
        self.paused = False
        self.decimate = 1
        self.scale = True
        self.color = True

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


def mouse_cb(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        __state__.mouse_btns[0] = True

    if event == cv2.EVENT_LBUTTONUP:
        __state__.mouse_btns[0] = False

    if event == cv2.EVENT_RBUTTONDOWN:
        __state__.mouse_btns[1] = True

    if event == cv2.EVENT_RBUTTONUP:
        __state__.mouse_btns[1] = False

    if event == cv2.EVENT_MBUTTONDOWN:
        __state__.mouse_btns[2] = True

    if event == cv2.EVENT_MBUTTONUP:
        __state__.mouse_btns[2] = False

    if event == cv2.EVENT_MOUSEMOVE:

        h, w = out.shape[:2]
        dx, dy = x - __state__.prev_mouse[0], y - __state__.prev_mouse[1]

        if __state__.mouse_btns[0]:
            __state__.yaw += float(dx) / w * 2
            __state__.pitch -= float(dy) / h * 2

        elif __state__.mouse_btns[1]:
            dp = np.array((dx / w, dy / h, 0), dtype=np.float32)
            __state__.translation -= np.dot(__state__.rotation, dp)

        elif __state__.mouse_btns[2]:
            dz = math.sqrt(dx ** 2 + dy ** 2) * math.copysign(0.01, -dy)
            __state__.translation[2] += dz
            __state__.distance -= dz

    if event == cv2.EVENT_MOUSEWHEEL:
        dz = math.copysign(0.1, flags)
        __state__.translation[2] += dz
        __state__.distance -= dz

    __state__.prev_mouse = (x, y)


def project(v):
    """project 3d vector array to 2d"""
    global out
    h, w = out.shape[:2]
    view_aspect = float(h) / w

    # ignore divide by zero for invalid depth
    with np.errstate(divide='ignore', invalid='ignore'):
        proj = v[:, :-1] / v[:, -1, np.newaxis] * \
               (w * view_aspect, h) + (w / 2.0, h / 2.0)

    # near clipping
    znear = 0.03
    proj[v[:, 2] < znear] = np.nan
    return proj


def view(v):
    """apply view transformation on vector array"""
    return np.dot(v - __state__.pivot, __state__.rotation) + __state__.pivot - __state__.translation


def line3d(_out, pt1, pt2, color=(0x80, 0x80, 0x80), thickness=1):
    """draw a 3d line from pt1 to pt2"""
    p0 = project(pt1.reshape(-1, 3))[0]
    p1 = project(pt2.reshape(-1, 3))[0]
    if np.isnan(p0).any() or np.isnan(p1).any():
        return
    p0 = tuple(p0.astype(int))
    p1 = tuple(p1.astype(int))
    rect = (0, 0, _out.shape[1], _out.shape[0])
    inside, p0, p1 = cv2.clipLine(rect, p0, p1)
    if inside:
        cv2.line(_out, p0, p1, color, thickness, cv2.LINE_AA)


def grid(_out, pos, rotation=np.eye(3), size=1, n=10, color=(0x80, 0x80, 0x80)):
    """draw a grid on xz plane"""
    pos = np.array(pos)
    s = size / float(n)
    s2 = 0.5 * size
    for i in range(0, n + 1):
        x = -s2 + i * s
        line3d(_out, view(pos + np.dot((x, 0, -s2), rotation)),
               view(pos + np.dot((x, 0, s2), rotation)), color)
    for i in range(0, n + 1):
        z = -s2 + i * s
        line3d(_out, view(pos + np.dot((-s2, 0, z), rotation)),
               view(pos + np.dot((s2, 0, z), rotation)), color)


def axes(_out, pos, rotation=np.eye(3), size=0.075, thickness=2):
    """draw 3d axes"""
    line3d(_out, pos, pos +
           np.dot((0, 0, size), rotation), (0xff, 0, 0), thickness)
    line3d(_out, pos, pos +
           np.dot((0, size, 0), rotation), (0, 0xff, 0), thickness)
    line3d(_out, pos, pos +
           np.dot((size, 0, 0), rotation), (0, 0, 0xff), thickness)


def frustum(_out, intrinsics, color=(0x40, 0x40, 0x40)):
    """draw camera's frustum"""
    orig = view([0, 0, 0])
    w, h = intrinsics.width, intrinsics.height

    for d in range(1, 6, 2):
        def get_point(x, y):
            p = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], d)
            line3d(_out, orig, view(p), color)
            return p

        top_left = get_point(0, 0)
        top_right = get_point(w, 0)
        bottom_right = get_point(w, h)
        bottom_left = get_point(0, h)

        line3d(_out, view(top_left), view(top_right), color)
        line3d(_out, view(top_right), view(bottom_right), color)
        line3d(_out, view(bottom_right), view(bottom_left), color)
        line3d(_out, view(bottom_left), view(top_left), color)


def pointcloud(_out, verts, texcoords, color, painter=True):
    """draw point cloud with optional painter's algorithm"""
    if painter:
        # Painter's algo, sort points from back to front

        # get reverse sorted indices by z (in view-space)
        # https://gist.github.com/stevenvo/e3dad127598842459b68
        v = view(verts)
        s = v[:, 2].argsort()[::-1]
        proj = project(v[s])
    else:
        proj = project(view(verts))

    if __state__.scale:
        proj *= 0.5 ** __state__.decimate

    h, w = _out.shape[:2]

    # proj now contains 2d image coordinates
    j, i = proj.astype(np.uint32).T

    # create a mask to ignore _out-of-bound indices
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
    _out[i[m], j[m]] = color[u[m], v[m]]


class FrameProcessor:
    def __init__(self, camera):
        self.camera = camera
        self.__image2D__ = True  # True: image2D, False: image3D
        global __state__
        __state__ = __State__()
        self.pc = self.camera.pointcloud()

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

    # TODO
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

            depth_image_viewer = np.asanyarray(depth_frame_viewer.get_data())

            # Grab new intrinsics (may be changed by decimation)
            depth_intrinsics = self.camera.get_profile_intrinsics(depth_frame.profile)
            w, h = depth_intrinsics.width, depth_intrinsics.height
            global out
            out = np.empty((h, w, 3), dtype=np.uint8)

            depth_image_viewer = np.asanyarray(depth_frame_viewer.get_data())

            depth_colormap = np.asanyarray(
                self.camera.__colorizer__.colorize(depth_frame_viewer).get_data())

            if __state__.color:
                mapped_frame, color_source = color_frame, color_image
            else:
                mapped_frame, color_source = depth_image_viewer, depth_colormap

            self.pc.map_to(mapped_frame)
            points = self.pc.calculate(depth_frame_viewer)

            # Pointcloud data to arrays
            v, t = points.get_vertices(), points.get_texture_coordinates()
            verts = np.asanyarray(v).view(np.float32).reshape(-1, 3)  # xyz
            texcoords = np.asanyarray(t).view(np.float32).reshape(-1, 2)  # uv

            # Render
            now = time.time()

            out.fill(0)

            if not __state__.scale or out.shape[:2] == (h, w):
                pointcloud(out, verts, texcoords, color_source)
            else:
                tmp = np.zeros((h, w, 3), dtype=np.uint8)
                pointcloud(tmp, verts, texcoords, color_source)
                tmp = cv2.resize(
                    tmp, out.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)
                np.putmask(out, tmp > 0, tmp)

            if any(__state__.mouse_btns):
                axes(out, view(__state__.pivot), __state__.rotation, thickness=4)

            dt = time.time() - now

            return out

    # TODO
    def updateRotation(self):
        pass
