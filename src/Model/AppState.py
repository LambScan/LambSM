from src.Data import RSCamera
from src.Data.Processor import Processor
from src.View.GUI import WWatchLive


class AppState:
    def __init__(self):
        self.paused = True
        self.image2D = True
        self.window = None
        self.cams = None


def cams():
    pass
    # camera = RSCamera()
    # processor = Processor(camera.__pipeline__)
    #
    # camera.start()
    # color_frame, depth_frame = camera.get_frame()
    # result = processor.process(color_frame, depth_frame)
    #
    # if type(result) is tuple and len(result) == 2 and processor.is2DMode():
    #     color_image, depth_frame = result
    # elif processor.is3DMode():
    #     image_3D = result
    #
    # camera.stop()


if __name__ == '__main__':
    camera = RSCamera()
    camera.start()
    get_frame = Processor(camera.__pipeline__)
    window = WWatchLive()

    # processor.changeMode(image3D=True)
    window.image2D = False
    window.launch()

    while True:
        window.refresh()
        color_frame, depth_frame = camera.get_frame()
        result = get_frame(color_frame, depth_frame)
        print(result)
        # if type(result) is tuple and len(result) == 2 and processor.is2DMode():
        #     color_image, depth_image = result
        #     print("2D")
        #     window.update_image(image_color=color_image, depth_image=depth_image)
        # elif processor.is3DMode():
        #     print("we're in 3D mode")
        #     print(type(result))
        #     print(result)
        #     window.update_image(image_3D=result)
        window.update_image(image_3D=result)

    camera.stop()
