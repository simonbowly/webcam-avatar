import asyncio
import logging

from webcam_avatar import formats

from webcam_avatar.facemesh import facemesh, point_cloud
from webcam_avatar.ffmpeg_asyncio import (
    SingleFrameBuffer,
    stream_input_frames,
    stream_output_frames_png,
    stream_output_frames_raw,
)


async def transform(
    input_buffer: SingleFrameBuffer[formats.RawImage],
    output_buffer: SingleFrameBuffer[formats.PNGImage],
):
    async for frame in input_buffer.frames():
        png_image = formats.rgb_to_png(formats.raw_to_rgb(frame))
        facemesh_result = await facemesh(png_image)
        if facemesh_result is not None:
            rgb_render = point_cloud(facemesh_result)
            output_buffer.update(formats.rgb_to_png(rgb_render))


# async def transform(
#     input_buffer: SingleFrameBuffer[formats.RawImage],
#     output_buffer: SingleFrameBuffer[formats.PNGImage],
# ):
#     async for frame in input_buffer.frames():
#         output_buffer.update(formats.rgb_to_png(formats.raw_to_rgb(frame)))


async def main():
    input_buffer: SingleFrameBuffer[formats.RawImage] = SingleFrameBuffer()
    output_buffer: SingleFrameBuffer[formats.PNGImage] = SingleFrameBuffer()
    await asyncio.gather(
        stream_input_frames(input_buffer),
        transform(input_buffer, output_buffer),
        stream_output_frames_raw(input_buffer, "/dev/video2"),
        stream_output_frames_png(output_buffer, "/dev/video3"),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
