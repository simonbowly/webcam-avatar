from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class RawImage:
    width: int
    height: int
    data: bytes


@dataclass
class RGBImage:
    data: np.ndarray

    @property
    def width(self):
        return self.data.shape[1]

    @property
    def height(self):
        return self.data.shape[0]


@dataclass
class PNGImage:
    width: int
    height: int
    data: bytes


def rgb_to_raw(image: RGBImage) -> RawImage:
    height, width, channels = image.data.shape
    if channels != 3:
        raise ValueError("Require 3 channels to convert")
    if image.data.dtype != np.uint8:
        raise ValueError("Require uint 8 type")
    return RawImage(height=height, width=width, data=image.data.tobytes())


def raw_to_rgb(image: RawImage) -> RGBImage:
    return RGBImage(
        np.frombuffer(image.data, np.uint8).reshape((image.height, image.width, 3))
    )


def rgb_to_png(image: RGBImage) -> PNGImage:
    return PNGImage(
        width=image.width,
        height=image.height,
        data=cv2.imencode(".png", image.data)[1].tobytes(),
    )


def png_to_rgb(image: PNGImage) -> RGBImage:
    return RGBImage(
        cv2.imdecode(np.frombuffer(image.data, dtype="uint8"), cv2.IMREAD_UNCHANGED)
    )
