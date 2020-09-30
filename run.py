import asyncio
import logging

from webcam_avatar.formats import raw_to_rgb, rgb_to_raw, RawImage, RGBImage, rgb_to_png
from webcam_avatar.facemesh import facemesh, point_cloud
from webcam_avatar.ffmpeg_asyncio import (
    SingleFrameBuffer,
    stream_ffmpeg_input,
    stream_ffmpeg_output,
    buffer_filter,
)


# Breakdown performance metrics of encoders?
# Need some way to trace the lag moving through the encoders.


async def facemesh_transform(
    input_buffer: SingleFrameBuffer[RGBImage],
    output_buffer: SingleFrameBuffer[RGBImage],
):
    async for frame in input_buffer.frames():
        facemesh_result = await facemesh(rgb_to_png(frame))
        if facemesh_result is not None:
            rgb_render = point_cloud(facemesh_result, width=400, height=300)
            # Possibly need the conversions to be in a thread?
            # The main purpose of the async code here is to avoid
            # race conditions on the frames. All processing should
            # be awaited to avoid interupting streams?
            output_buffer.update(rgb_render)


async def main():
    input_raw_buffer: SingleFrameBuffer[RawImage] = SingleFrameBuffer()
    input_rgb_buffer: SingleFrameBuffer[RGBImage] = SingleFrameBuffer()
    output_rgb_buffer: SingleFrameBuffer[RGBImage] = SingleFrameBuffer()
    output_raw_buffer: SingleFrameBuffer[RawImage] = SingleFrameBuffer()
    await asyncio.gather(
        stream_ffmpeg_input(input_raw_buffer, source="/dev/video2"),
        stream_ffmpeg_output(input_raw_buffer, "/dev/video4"),
        buffer_filter(raw_to_rgb)(input_raw_buffer, input_rgb_buffer),
        facemesh_transform(input_rgb_buffer, output_rgb_buffer),
        buffer_filter(rgb_to_raw)(output_rgb_buffer, output_raw_buffer),
        stream_ffmpeg_output(output_raw_buffer, "/dev/video5", width=400, height=300),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
