import numpy as np
import pytest

from webcam_avatar.formats import (
    RGBImage,
    png_to_rgb,
    raw_to_rgb,
    rgb_to_png,
    rgb_to_raw,
)


@pytest.fixture
def random_pixels():
    return RGBImage(np.random.randint(0, 256, size=(100, 200, 3), dtype="uint8"))


def test_rgb_raw(random_pixels):
    binary = rgb_to_raw(random_pixels)
    back_to_pixels = raw_to_rgb(binary)
    assert (back_to_pixels.data == random_pixels.data).all()
    back_to_binary = rgb_to_raw(back_to_pixels)
    assert binary == back_to_binary


def test_rgb_png(random_pixels):
    binary = rgb_to_png(random_pixels)
    back_to_pixels = png_to_rgb(binary)
    assert (back_to_pixels.data == random_pixels.data).all()
    back_to_binary = rgb_to_png(back_to_pixels)
    assert binary == back_to_binary
