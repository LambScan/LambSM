import numpy as np

# Constants to filter and crop the numpy images
__w_crop = 95
__h_crop = 45
__edged_RGB__ = 140  # no lamb > edged > lamb
__edged_Depth__ = 1100  # no lamb > edged > lamb


def filterColor(color_image):
    pass


def filterDepth(depth_image):
    pass


def cropImage(image):
    pass


def mustSave(color_image, depth_image):
    return True


def isThereALamb(color_image, depth_image):
    depth_result = isLamb(depth_image, depth=True)
    # DO NOT DELETE. WE WON'T USE THIS CRITERIA RIGHT NOW BUT WE WILL.
    # color_result = isLamb(color_image)
    # if not (False in color_result or False in depth_result):
    #     print("There's a Lamb")
    #     return "lamb"
    # elif not (True in color_result or True in depth_result):
    #     print("There's nothing")
    #     return "no_lamb"
    # elif not (False in depth_result):
    #     print("Probably a lamb")
    #     return "probably"
    # elif not (False in color_result):
    #     print("Check_this")
    #     return "check"
    # else:
    #     print("Error")
    #     return "error"
    # THIS IS THE ONLY CRITERIA WE USE RIGHT NOW
    if not (False in depth_result):
        print("There's probably a lamb")
        return "lamb"
    elif not (True) in depth_result:
        print("There's nothing")
        return "no_lamb"
    else:
        print("Error")
        print "error"


_startx = _starty = None


def __crop__(img, cropx, cropy, depth):
    global _startx, _starty
    if depth:
        y, x = img.shape
    else:
        y, x, _ = img.shape
    _startx = x // 2 - (cropx // 2)
    _starty = y // 2 - (cropy // 2) + 45
    return _startx, _starty


def __crop_center__(img, cropx, cropy, depth=False):
    if _startx is None or _starty is None:
        startx, starty = __crop__(img, cropx, cropy, depth)
    return img[_starty:_starty + cropy, _startx:_startx + cropx]


def __crop_left__(img, cropx, cropy, depth=False):
    if _startx is None or _starty is None:
        startx, starty = __crop__(img, cropx, cropy, depth)
    else:
        startx, starty = _startx, _starty
    startx -= 160
    return img[starty:starty + cropy, startx:startx + cropx]


def __crop_right__(img, cropx, cropy, depth=False):
    if _startx is None or _starty is None:
        startx, starty = __crop__(img, cropx, cropy, depth)
    else:
        startx, starty = _startx, _starty
    startx += 140
    return img[starty:starty + cropy, startx:startx + cropx]


def isLamb(image, depth=False):
    conf = (image, __w_crop, __h_crop, depth)
    average_left = np.mean(__crop_left__(*conf))
    average_center = np.mean(__crop_center__(*conf))
    average_right = np.mean(__crop_right__(*conf))

    if depth:
        result = (average_left < __edged_Depth__,
                  average_center < __edged_Depth__, average_right < __edged_Depth__)

    else:
        result = (average_left > __edged_RGB__,
                  average_center > __edged_RGB__, average_right > __edged_RGB__)

    return result
