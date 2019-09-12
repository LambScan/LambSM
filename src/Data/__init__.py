from src.Data.FrameProcessor_2 import FrameProcessor
from src.Data.RSCamera import RSCamera

if __name__ == '__main__':
    camera = RSCamera()
    processor = FrameProcessor(camera)

    camera.start()
    color_frame, depth_frame = camera.get_frame()
    result = processor.process(color_frame, depth_frame)

    if type(result) is tuple and len(result) == 2 and processor.is2DMode():
        color_image, depth_frame = result
    elif processor.is3DMode():
        image_3D = result

    camera.stop()