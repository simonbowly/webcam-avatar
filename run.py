import asyncio
import logging

import numpy as np

from webcam_avatar.ffmpeg_asyncio import (
    SingleFrameBuffer,
    stream_input_frames,
    stream_output_frames,
)
from webcam_avatar.formats import rgb_to_bytes, bytes_to_rgb


async def transform(input_buffer: SingleFrameBuffer, output_buffer: SingleFrameBuffer):
    while True:
        await asyncio.sleep(0.001)
        if input_buffer.fresh and input_buffer.raw_image:
            image = bytes_to_rgb(
                {"width": 640, "height": 480, "data": input_buffer.raw_image}
            )
            new_image = np.zeros((480, 640, 3), dtype=np.uint8)
            new_image[:, :, 2] = image[:, :, 2]
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
