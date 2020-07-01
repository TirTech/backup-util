import datetime
import hashlib
import json
import os
import re
from tkinter import PhotoImage
from typing import Any, Tuple, Optional, Callable, List, NewType

import PIL
from PIL import Image, ImageTk, ImageOps

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


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if o is None:
            super().default(o)
        elif isinstance(o, datetime.datetime):
            return o.isoformat()
        elif CustomJSONEncoder.has_jsonify_method(o):
            return o.__jsonify__()
        else:
            super().default(o)

    @staticmethod
    def has_jsonify_method(obj) -> bool:
        return hasattr(obj, "__jsonify__") and callable(getattr(obj, "__jsonify__"))


def hash_file(path: str):
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


def find_match(lst: list, predicate) -> Tuple[Optional[int], Optional[Any]]:
    for i, v in enumerate(lst):
        if predicate(v):
            return i, v
    return None, None


def path_common_suffix(p1: str, p2: str) -> str:
    head1, tail1 = os.path.split(p1)
    head2, tail2 = os.path.split(p2)
    res = ""
    while tail1 == tail2 and len(head1) > 0 and len(head2) > 0:
        res = os.path.join(tail1, res)
        head1, tail1 = os.path.split(head1)
        head2, tail2 = os.path.split(head2)
    return res


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
