import sys

if sys.version_info[0] < 3:
    from Data import frequency, num_frames
    from Model import AppState
else:
    from src.Model import AppState
    from src.Data import frequency, num_frames


def EXIT(self):
    self.state.close()
    self.apptothe_end.emit()

def BACK(self):
    self.state.close()
    self.apptoapp.emit()


def StartingW2Component(self):
    if self.state.window is not None:
        self.state.window.close()
    self.app_inittocomponent.emit()


def StartingW2Watch(self):
    if self.state.window is not None:
        self.state.window.close()
    self.app_inittowatch_live.emit()


def StartingW2Load(self):
    if self.state.window is not None:
        self.state.window.close()
    self.app_inittoload_image.emit()


def Frame2FrameLoop(self):
    if self.state.state == AppState.STATE_COMPONENT:
        self.getting_framestogetting_frames.emit()
    elif self.state.state == AppState.STATE_WATCHER:
        self.get_framestoget_frames.emit()


def GetFrame2SaveFrame(self):
    self.state.recording = 1
    Frame2FrameLoop(self)


def GetFrame2TakeFrames(self):
    self.state.recording = num_frames * frequency
    Frame2FrameLoop(self)
