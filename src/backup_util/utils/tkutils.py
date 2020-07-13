import re
from tkinter import PhotoImage
from typing import Any, Optional, Callable, List, NewType

import PIL
from PIL import Image, ImageTk, ImageOps

ObsCallback = NewType('ObsCallback', Callable[[Any, Any], None])


class WatchedVariable:
    def __init__(self):
        self.observers: List[ObsCallback] = []
        self.value: Optional[Any] = None

    def get(self) -> Any:
        return self.value

    def set(self, value: Any):
        oldval = self.value
        self.value = value
        if len(self.observers) > 0:
            for obs in self.observers:
                obs(self, oldval, value)

    def trace_add(self, callback: ObsCallback):
        self.observers.append(callback)


_nonbmp = re.compile(r'[\U00010000-\U0010FFFF]')


# https://stackoverflow.com/questions/40222971/python-find-equivalent-surrogate-pair-from-non-bmp-unicode-char
def _surrogatepair(match):
    char = match.group()
    assert ord(char) > 0xffff
    encoded = char.encode('utf-16-le')
    return (
            chr(int.from_bytes(encoded[:2], 'little')) +
            chr(int.from_bytes(encoded[2:], 'little')))


def with_surrogates(text):
    return _nonbmp.sub(_surrogatepair, text)


def load_image(name: str, width=None, height=None, color=None) -> PhotoImage:
    """
    Load a png image. The image will be resized if width and/or height are specified. If only one of
    width or height is specified, the image will be a square of the given size.

    :param name: the file name without the extension
    :param width: the width of the image
    :param height: the height of the image
    :param color: the new color of the image if loading from a black and white image
    :return: the image as a `PhotoImage` for use with Tk
    """
    img: PIL.Image.Image = Image.open(f"backup_util/images/{name}.png")
    if width is not None or height is not None:
        w = width if width is not None else height
        h = height if height is not None else width
        img = img.resize((w, h), Image.ANTIALIAS)
    if color is not None:
        img = img.convert('RGBA')
        background = Image.new('RGBA', img.size, (255, 255, 255))
        img = Image.alpha_composite(background, img)
        img = img.convert("L")
        img = ImageOps.colorize(img, color, (255, 255, 255))
    return ImageTk.PhotoImage(img)
