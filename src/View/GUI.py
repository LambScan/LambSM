import sys
import cv2
import numpy as np
import time
# import abc
# from src.Model.AppState import AppState, STATE_WATCHER, STATE_LOADER, STATE_COMPONENT

if sys.version_info[0] < 3:
    import PySimpleGUI27 as sg
    # ABC = abc.ABCMeta
else:
    import PySimpleGUI as sg
    # ABC = abc.ABC

__title__ = "LambScan"


# def Prompt(text_messages, title=__title__):
#     layout = []
#
#     if type(text_messages) is str:
#         layout.append([sg.Text(text_messages), sg.InputText('')])
#     elif type(text_messages) is str:
#         for msg in text_messages:
#             layout.append([sg.Text(msg), sg.InputText('')])
#     layout.append([sg.Submit(), sg.Cancel()])
#
#     window = sg.Window(title, layout)
#     button, values = window.Read()
#     return button, values


def PopupChooseFile(text_message):
    sg.ChangeLookAndFeel('Reddit')
    filename = sg.PopupGetFile(text_message)
    return filename


# class __DefaultWindow__(ABC):
class __DefaultWindow__(object):
    def __init__(self, title=__title__):
        sg.ChangeLookAndFeel('Reddit')
        self.layout = []
        self.title = title
        self.window = None
        self.close = None
        self.events = []

    def launch(self):
        self.window = sg.Window(self.title, self.layout, location=(800, 400))
        self.close = self.window.Close


class WLoadImage(__DefaultWindow__):
    def __init__(self, title=__title__):
        super(WLoadImage, self).__init__(title)
        self.layout = [[sg.Button(button_text='PLY / PCD', key='ply', size=(5, 1), font=('wingdings', 14))],
                       [sg.Button(button_text='PNGs', key='pngs', size=(5, 1), font=('wingdings', 14))]]
        self.window = sg.Window(title, self.layout, location=(800, 400))
        event, value = self.window.Read()
        if event == 'ply':
            filename = PopupChooseFile(text_message="Choose a PointCloud file:")
        elif event == 'pngs':
            self.toChoose()


class WChooseFiles(__DefaultWindow__):
    def __init__(self, title=__title__):
        super(WChooseFiles, self).__init__(title)
        self.layout = [
            [sg.Text('File RGB:', size=(10, 1)), sg.Input(), sg.FileBrowse()],
            [sg.Text('File Depth:', size=(10, 1)), sg.Input(), sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()],
            [sg.Text('', key='error_text', text_color='red', size=(20, 1), visible=False)]]

        self.window = sg.Window('Read files', self.layout, location=(800, 400))

        exit = False
        while not exit:
            event, filename = self.window.Read()
            if len(filename) == 2 and event == 'Submit' or event == 'Cancel':
                exit = True
            print(filename[0])
            print(filename[1])

        self.window.Close()
        # if file_ext is None:
        #     return filename
        # elif file_ext is not None and file_ext in filename:
        #     return filename
        # else:
        #     return None


class WStarting(__DefaultWindow__):
    def __init__(self, title=__title__):
        super(WStarting, self).__init__(title)
        self.seconds = 24
        self.paused = False
        self.layout = [[sg.Frame(title='Additional options:', layout=[
            [sg.Button(button_text='Watch Live', key='watch_live', size=(10, 1), font=('wingdings', 14)),
             sg.Button(button_text='Load File', key='load_file', size=(10, 1), font=('wingdings', 14)), ]],
                                 size=(25, 3), relief=sg.RELIEF_SUNKEN)],
                       [sg.Button(button_text='Start Component', key='start_component', size=(16, 1),
                                  font=('wingdings', 14))],
                       [sg.Text('The component will start automatically', auto_size_text=True,
                                justification='left')],
                       [sg.ProgressBar(max_value=self.seconds, key='countdown', orientation='h', size=(20, 20))],
                       [sg.Button(button_text='Exit', key='Exit', size=(10, 1), font=('verdana', 14)), ]]

        self.window = None
        self.progress_bar = None
        self.launch()

    def launch(self):
        super(WStarting, self).launch()
        self.progress_bar = self.window.FindElement('countdown')
        # TODO: implement by state machine
        while self.seconds > 0 and not self.paused:
            time.sleep(1)
            self.refresh()
            self.seconds -= 1
            # if self.paused:
            #     break
        if not self.paused:
            self.__click_start_component__()

    def refresh(self):
        event, values = self.window.Read(timeout=20)
        self.progress_bar.UpdateBar(self.seconds)
        # self.window.FindElement(key='countdown').Update(text=str(self.seconds))
        self.__handle_event__(event)

    def __click_exit__(self):
        print("EXIT button pressed")
        self.window.Close()
        pass

    def __click_watch__(self):
        print("Pushed watch button")
        state = AppState()
        state.transition = STATE_WATCHER
        self.paused = True

    def __click_load__(self):
        print("Pushed load button")
        state = AppState()
        state.transition = STATE_LOADER
        self.paused = True
        self.toLoad()

    def __click_start_component__(self):
        print("Pushed start component button")
        state = AppState()
        state.transition = STATE_COMPONENT
        self.paused = True

    def __handle_event__(self, event):
        if event == 'Exit' or event is None:
            self.__click_exit__()
        elif event == 'watch_live':
            self.__click_watch__()
        elif event == 'load_file':
            self.__click_load__()
        elif event == 'start_component':
            self.__click_start_component__()


class WException(__DefaultWindow__):
    def __init__(self, title=__title__):
        super(WException, self).__init__(title)
        self.seconds = 5
        self.layout = [[sg.Frame(title='Additional options:', layout=[
            [sg.Button(button_text='Watch Live', key='watch_live', size=(10, 1), font=('wingdings', 14)),
             sg.Button(button_text='Load File', key='load_file', size=(10, 1), font=('wingdings', 14)), ]],
                                 size=(25, 3), relief=sg.RELIEF_SUNKEN)],
                       [sg.Button(button_text='Start Component', key='start_component', size=(16, 1),
                                  font=('wingdings', 14))],
                       [sg.Text('The component will start automatically', auto_size_text=True,
                                justification='left')],
                       [sg.ProgressBar(max_value=self.seconds, key='countdown', orientation='h', size=(20, 20))],
                       [sg.Button(button_text='Exit', key='Exit', size=(10, 1), font=('verdana', 14)), ]]


class WWatchLive(__DefaultWindow__):
    def __init__(self, title=__title__, presenter=None):
        super(WWatchLive, self).__init__(title)
        self.title = title
        self.paused = True
        self.image2D = True
        self.exit = False
        self.layout = [[sg.Text(title, size=(40, 1), justification='center', font=('wingdings', 20))],
                       [sg.Button(button_text='2D', key='2D', size=(3, 1), font=('wingdings', 14)),
                        sg.Button(button_text='3D', key='3D', size=(3, 1), font=('wingdings', 14)), ],
                       [sg.Image(filename='', key='image_color'),
                        sg.Image(filename='', key='image_depth')],
                       [sg.Image(filename='', key='image_3D', visible=False)],
                       [sg.Button(button_text='Start', key='Start', size=(7, 1), font=('wingdings', 14)),
                        sg.Button(button_text='Resume', key='Resume', size=(7, 1), font=('wingdings', 14),
                                  visible=False),
                        sg.Button(button_text='Pause', key='Pause', size=(7, 1), font=('Verdana', 14)),
                        sg.Button(button_text='Stop', key='Stop', size=(7, 1), font=('Verdana', 14))],
                       [sg.Button(button_text='Save PNG', key='Save_PNG', size=(10, 1), font=('verdana', 14)),
                        sg.Button(button_text='Save Both', key='Save_Both', size=(10, 1), font=('verdana', 14)),
                        sg.Button(button_text='Take Frames', key='Take_Frames', size=(10, 1), font=('verdana', 14)),
                        sg.Button(button_text='Save PLY', key='Save_PLY', size=(10, 1), font=('verdana', 14)),
                        sg.Button(button_text='Exit', key='Exit', size=(10, 1), font=('verdana', 14)), ]]
        self.window = None

    def launch(self):
        self.window = sg.Window(self.title, self.layout, location=(800, 400))
        self.refresh()
        self.__click_stop__()

    def refresh(self):
        event, values = self.window.Read(timeout=20)
        self.__handle_event__(event)

    # TODO: complete
    def update_image(self, image_color=None, depth_image=None, image_3D=None):
        if self.image2D:
            if image_color is not None and depth_image is not None:
                # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
                depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

                imgbytes_color = cv2.imencode('.png', image_color)[1].tobytes()  # ditto
                imgbytes_depth = cv2.imencode('.png', depth_colormap)[1].tobytes()  # ditto
                self.window.FindElement('image_color').Update(data=imgbytes_color)
                self.window.FindElement('image_depth').Update(data=imgbytes_depth)
            else:
                print("ERROR")
        elif not self.image2D:
            if image_3D is not None:
                imgbytes_3D = cv2.imencode('.png', image_3D)[1].tobytes()  # ditto
                self.window.FindElement('image_3D').Update(data=imgbytes_3D)
            else:
                print("ERROR")

    # TODO: complete
    def __click_2D__(self):
        self.image2D = True
        self.window.FindElement('image_color').Update(visible=True)
        self.window.FindElement('image_depth').Update(visible=True)
        self.window.FindElement('image_3D').Update(visible=False)

    # TODO: complete
    def __click_3D__(self):
        self.image2D = False
        self.window.FindElement('image_color').Update(visible=False)
        self.window.FindElement('image_depth').Update(visible=False)
        self.window.FindElement('image_3D').Update(visible=True)

    # TODO: complete
    def __click_exit__(self):
        print("EXIT button pressed")
        self.exit = True
        # self.window.Close()

    def __click_stop__(self):
        img = np.full((480, 640), 255)
        imgbytes = cv2.imencode('.png', img)[1].tobytes()  # this is faster, shorter and needs less includes
        self.window.FindElement('image_color').Update(data=imgbytes)
        self.window.FindElement('image_depth').Update(data=imgbytes)
        self.window.FindElement('image_3D').Update(data=imgbytes)

    def __click_start__(self):
        self.paused = False
        self.window.FindElement('Start').Update(visible=False)
        self.window.FindElement('Resume').Update(visible=True)

    # TODO : complete
    def __click_save_PNG__(self):
        pass

    # TODO : complete
    def __click_save_both__(self):
        pass

    # TODO : complete
    def __click_take_frames__(self):
        pass

    # TODO : complete
    def __click_save_PLY__(self):
        pass

    def __handle_event__(self, event):
        if event == 'Exit' or event is None:
            self.__click_exit__()
        elif event == 'Start' or event == 'Resume':
            self.__click_start__()
        elif event == 'Pause':
            self.paused = True
        elif event == 'Stop':
            self.paused = True
            self.__click_stop__()
        elif event == 'Save_PNG':
            self.__click_save_PNG__()
        elif event == 'Save_Both':
            self.__click_save_both__()
        elif event == 'Take_Frames':
            self.__click_take_frames__()
        elif event == 'Save_PLY':
            self.__click_save_PLY__()


if __name__ == '__main__':
    # btn, value = Prompt("Enter the ID of the lamb:")
    #
    # print(btn)
    # print(value)

    # TwoFramesWindow()
    #
    # filename = PopupChooseFile('Choose a 3D image file to read:')
    # print(filename)
    #
    # starting = StartingWindow()
    # window = Window()
    # window.launch()
    # while not window.__getattribute__('exit'):
    #     window.refresh()

    WChooseFiles()
