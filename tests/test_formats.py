import numpy as np

from webcam_avatar.formats import bytes_to_rgb, rgb_to_bytes


def test_rgb_bytes():
    height = 100
    width = 200
    pixels = np.random.randint(0, 256, size=(height, width, 3), dtype="uint8")
    binary = rgb_to_bytes(pixels)
    back_to_pixels = bytes_to_rgb(binary)
    back_to_binary = rgb_to_bytes(back_to_pixels)
    assert (back_to_pixels == pixels).all()
    assert back_to_binary == binary
