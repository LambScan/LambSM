import sys

if sys.version_info[0] < 3:
    from Model import LambFilter
    from Data import RSCamera, FrameProcessor, FileManager
    from View.GUI import WWatchLive, WStarting
else:
    from src.Model import LambFilter
    from src.Data import RSCamera, FrameProcessor, FileManager
    from src.View.GUI import WWatchLive, WStarting

STATE_COMPONENT = "COMPONENT"
STATE_LOADER = "LOAD"
STATE_WATCHER = "WATCH"
EXIT = "EXIT"


class AppState:
    def __init__(self):
        self.state = "none"
        self.stopped = False
        self.image2D = True
        self.recording = 0
        self.window = None
        self.processor = []
        self.cams = []
        self.refresh = None

    def starting(self):
        self.refresh = None
        self.recording = 0
        self.window = WStarting()
        transition = self.window.launch()
        if transition is not None:
            return transition
        else:
            return False

    def close(self):
        if self.window is not None:
            self.window.close()
            for cam in self.cams:
                cam.stop()
        self.cams = []
        self.processor = []

    def watcher(self):
        self.state = STATE_WATCHER
        self.refresh = None
        self.recording = 0
        self.cams = [RSCamera.RSCamera()]
        self.processor = FrameProcessor.FrameProcessor(self.cams[0])
        self.window = WWatchLive()
        self.cams[0].start()
        self.window.launch()

        def get_frame(self, id_crotal="random"):
            camera = self.cams[0]

            transition = self.window.refresh()
            if not self.stopped:
                color_frame, depth_frame = camera.get_frame()
                result = self.processor.process(color_frame, depth_frame)
                if self.image2D and type(result) is tuple and len(result) == 2 and self.processor.image2D:
                    color_image, depth_image = result
                    if self.recording > 0:
                        if self.recording % frequency == 1:
                            FileManager.save_frames(color_image, depth_image, id_crotal)
                        self.recording -= 1
                    self.window.update_image(image_color=color_image, depth_image=depth_image)
                elif not self.processor.image2D:
                    self.window.update_image(image_3D=result)
                    if self.recording > 0:
                        self.recording -= 1
                        # FileManager.save_frames(color_image, depth_image, "random")
            else:
                color_frame, depth_frame = camera.get_frame()
                result = self.processor.process(color_frame, depth_frame)
                if type(result) is tuple and len(result) == 2 and self.processor.image2D:
                    color_image, depth_image = result
                    self.window.update_image(image_color=color_image, depth_image=depth_image)
                elif not self.processor.image2D:
                    self.window.update_image(image_3D=result)
            return transition

        self.refresh = get_frame

    def loader(self):
        self.state = STATE_LOADER
        self.refresh = None
        self.recording = 0
        self.window = WImageLoaded()
        self.window.launch()

        self.refresh = self.window.refresh

    def component(self):
        self.state = STATE_COMPONENT
        self.refresh = None
        self.recording = 0
        self.cams = [RSCamera.RSCamera()]
        self.processor = FrameProcessor.FrameProcessor(self.cams[0])
        self.cams[0].start()

        def get_frame(self, id_crotal="random"):
            camera = self.cams[0]

            transition = Frame2FrameLoop
            if self.recording == 0:
                if np.random.random_integers(0, 100) == 3:
                    transition = GetFrame2TakeFrames

            if not self.stopped:
                # time.sleep(sleep * 900)  # random_number * 1/4 hour
                time.sleep(2)
                color_frame, depth_frame = camera.get_frame()
                result = self.processor.process(color_frame, depth_frame)
                if self.image2D and type(result) is tuple and len(result) == 2 and self.processor.image2D:
                    color_image, depth_image = result
                    if self.recording > 0:
                        if self.recording % frequency == 1:
                            id_crotal = LambFilter.isThereALamb(color_image, depth_image)
                            if id_crotal == "no_lamb":
                                if 2 == np.random.random_integers(0, 350):
                                    FileManager.save_frames(color_image, depth_image, id_crotal)
                            else:
                                time.sleep(0.4)
                                FileManager.save_frames(color_image, depth_image, id_crotal)
                        self.recording -= 1
                elif not self.processor.image2D:
                    if self.recording > 0:
                        self.recording -= 1
                        # FileManager.save_frames(color_image, depth_image, "random")
            else:
                color_frame, depth_frame = camera.get_frame()
                result = self.processor.process(color_frame, depth_frame)
                if type(result) is tuple and len(result) == 2 and self.processor.image2D:
                    color_image, depth_image = result
                elif not self.processor.image2D:
                    pass
            return transition

        self.refresh = get_frame
