import numpy as np
import math
import cv2
import time


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

            out = np.empty((h, w, 3), dtype=np.uint8)

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

            out.fill(0)

            self.grid(out, (0, 0.5, 1), size=1, n=10)
            self.frustum(out, depth_intrinsics)
            self.axes(out, self.view([0, 0, 0]), self.rotation, size=0.1, thickness=1)

            if not self.scale or out.shape[:2] == (h, w):
                self.pointcloud(out, verts, texcoords, color_source)
            else:
                tmp = np.zeros((h, w, 3), dtype=np.uint8)
                self.pointcloud(tmp, verts, texcoords, color_source)
                tmp = cv2.resize(
                    tmp, out.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)
                np.putmask(out, tmp > 0, tmp)

            if any(self.mouse_btns):
                self.axes(out, self.view(self.pivot), self.rotation, thickness=4)

            dt = time.time() - now

            return out

    @classmethod
    def project(cls, v, out):
        """project 3d vector array to 2d"""
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

    def view(self, v):
        """apply view transformation on vector array"""
        return np.dot(v - self.pivot, self.rotation) + self.pivot - self.translation

    @classmethod
    def line3d(cls, out, pt1, pt2, color=(0x80, 0x80, 0x80), thickness=1):
        """draw a 3d line from pt1 to pt2"""
        p0 = cls.project(pt1.reshape(-1, 3), out)[0]
        p1 = cls.project(pt2.reshape(-1, 3), out)[0]
        if np.isnan(p0).any() or np.isnan(p1).any():
            return
        p0 = tuple(p0.astype(int))
        p1 = tuple(p1.astype(int))
        rect = (0, 0, out.shape[1], out.shape[0])
        inside, p0, p1 = cv2.clipLine(rect, p0, p1)
        if inside:
            cv2.line(out, p0, p1, color, thickness, cv2.LINE_AA)

    def grid(self, out, pos, rotation=np.eye(3), size=1, n=10, color=(0x80, 0x80, 0x80)):
        """draw a grid on xz plane"""
        pos = np.array(pos)
        s = size / float(n)
        s2 = 0.5 * size
        for i in range(0, n + 1):
            x = -s2 + i * s
            self.line3d(out, self.view(pos + np.dot((x, 0, -s2), rotation)),
                        self.view(pos + np.dot((x, 0, s2), rotation)), color)
        for i in range(0, n + 1):
            z = -s2 + i * s
            self.line3d(out, self.view(pos + np.dot((-s2, 0, z), rotation)),
                        self.view(pos + np.dot((s2, 0, z), rotation)), color)

    def axes(self, out, pos, rotation=np.eye(3), size=0.075, thickness=2):
        """draw 3d axes"""
        self.line3d(out, pos, pos +
                    np.dot((0, 0, size), rotation), (0xff, 0, 0), thickness)
        self.line3d(out, pos, pos +
                    np.dot((0, size, 0), rotation), (0, 0xff, 0), thickness)
        self.line3d(out, pos, pos +
                    np.dot((size, 0, 0), rotation), (0, 0, 0xff), thickness)

    def frustum(self, out, intrinsics, color=(0x40, 0x40, 0x40)):
        """draw camera's frustum"""
        orig = self.view([0, 0, 0])
        w, h = intrinsics.width, intrinsics.height

        for d in range(1, 6, 2):
            def get_point(x, y):
                # p = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], d)
                p = self.camera.deproject_pixel_to_point(intrinsics, x, y, d)
                self.line3d(out, orig, self.view(p), color)
                return p

            top_left = get_point(0, 0)
            top_right = get_point(w, 0)
            bottom_right = get_point(w, h)
            bottom_left = get_point(0, h)

            self.line3d(out, self.view(top_left), self.view(top_right), color)
            self.line3d(out, self.view(top_right), self.view(bottom_right), color)
            self.line3d(out, self.view(bottom_right), self.view(bottom_left), color)
            self.line3d(out, self.view(bottom_left), self.view(top_left), color)

    def pointcloud(self, out, verts, texcoords, color, painter=True):
        """draw point cloud with optional painter's algorithm"""
        if painter:
            v = self.view(verts)
            s = v[:, 2].argsort()[::-1]
            proj = self.project(v[s], out)
        else:
            proj = self.project(self.view(verts), out)

        if self.scale:
            proj *= 0.5 ** self.decimate

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
