import asyncio
import logging

from webcam_avatar import formats
from webcam_avatar.facemesh import facemesh, point_cloud
from webcam_avatar.ffmpeg_asyncio import (
    SingleFrameBuffer,
    stream_input_frames,
    stream_output_frames,
)


async def transform(input_buffer: SingleFrameBuffer, output_buffer: SingleFrameBuffer):
    event = input_buffer.register()
    while True:
        await event.wait()
        event.clear()
        if (raw_image := input_buffer.get()) is not None:
            png_image = formats.rgb_to_png(formats.raw_to_rgb(raw_image))
            facemesh_result = await facemesh(png_image)
            if facemesh_result is not None:
                rgb_render = point_cloud(facemesh_result)
                new_raw_image = formats.rgb_to_raw(rgb_render)
                output_buffer.update(new_raw_image)


async def main():
    input_buffer = SingleFrameBuffer()
    output_buffer = SingleFrameBuffer()
    await asyncio.gather(
        stream_input_frames(input_buffer),
        transform(input_buffer, output_buffer),
        stream_output_frames(input_buffer, "/dev/video2"),
        stream_output_frames(output_buffer, "/dev/video3"),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
