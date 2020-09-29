import numpy as np


def rgb_to_bytes(data):
    height, width, channels = data.shape
    if channels != 3:
        raise ValueError("Require 3 channels to convert")
    if data.dtype != np.uint8:
        raise ValueError("Require uint 8 type")
    return {"height": height, "width": width, "data": data.tobytes()}


def bytes_to_rgb(data):
    return np.frombuffer(data["data"], np.uint8).reshape(
        (data["height"], data["width"], 3)
    )
