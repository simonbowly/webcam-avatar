import asyncio
import logging

import numpy as np

from webcam_avatar.ffmpeg_asyncio import (
    SingleFrameBuffer,
    stream_input_frames,
    stream_output_frames,
)
from webcam_avatar.formats import rgb_to_bytes, bytes_to_rgb
from webcam_avatar.facemesh import facemesh



def to_point_cloud(facemesh):

    width, height = 640, 480

    mesh = np.array(facemesh["scaledMesh"])

    x = width - mesh[:, 0] * width / 100
    x = x.round().astype("int").clip(min=0, max=width - 1)

    y = mesh[:, 1] * height / 100
    y = y.round().astype("int").clip(min=0, max=height - 1)

    arr = np.zeros((height, width))
    for xs, ys in zip(x, y):
        arr[ys, xs] = 1

    return arr



async def transform(input_buffer: SingleFrameBuffer, output_buffer: SingleFrameBuffer):
    while True:
        await asyncio.sleep(0.001)
        if input_buffer.fresh and input_buffer.raw_image:
            predictions = await facemesh(input_buffer.raw_image)
            if predictions:
                render = to_point_cloud(predictions[0])
                # image = bytes_to_rgb(
                #     {"width": 640, "height": 480, "data": input_buffer.raw_image}
                # )
                new_image = np.zeros((480, 640, 3), dtype=np.uint8)
                new_image[:, :, 2] = (1 - render) * 255
                new_image[:, :, 1] = (1 - render) * 255
                new_image[:, :, 0] = 255
                new_raw_image = rgb_to_bytes(new_image)["data"]
                output_buffer.update(new_raw_image)


async def main():
    input_buffer = SingleFrameBuffer()
    output_buffer = SingleFrameBuffer()
    await asyncio.gather(
        stream_input_frames(input_buffer),
        transform(input_buffer, output_buffer),
        stream_output_frames(output_buffer),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
