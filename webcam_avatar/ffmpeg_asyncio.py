import asyncio
import logging
from dataclasses import dataclass, field
from typing import Generic, List, Optional, TypeVar

import ffmpeg
import numpy as np

from .formats import RawImage, RGBImage, raw_to_rgb, rgb_to_raw

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class SingleFrameBuffer(Generic[T]):

    events: List[asyncio.Event] = field(default_factory=list)
    frame: Optional[T] = field(default=None)

    def register(self):
        event = asyncio.Event()
        self.events.append(event)
        return event

    def update(self, data: T):
        self.frame = data
        for event in self.events:
            event.set()
        logger.debug("Frame buffer updated")

    def get(self) -> Optional[T]:
        return self.frame

    async def frames(self):
        event = self.register()
        while True:
            await event.wait()
            event.clear()
            if (frame := self.get()) is not None:
                yield frame


async def stream_ffmpeg_input(
    buffer: SingleFrameBuffer[RawImage],
    source: str,
    frame_rate=20,
    width=800,
    height=600,
):
    loop = asyncio.get_event_loop()
    process = (
        ffmpeg.input(source, format="video4linux2", s=f"{width}x{height}", r=frame_rate)
        .output("pipe:", format="rawvideo", pix_fmt="rgb24")
        .run_async(pipe_stdout=True)
    )
    assert process.stdout is not None
    while True:
        raw_image = await loop.run_in_executor(
            None, process.stdout.read, width * height * 3
        )
        buffer.update(RawImage(data=raw_image, width=width, height=height))
        logger.debug(f"Read frame {len(raw_image)=}")


async def stream_ffmpeg_output(
    buffer: SingleFrameBuffer[RawImage],
    sink: str,
    frame_rate=20,
    width=800,
    height=600,
):
    loop = asyncio.get_event_loop()
    process = (
        ffmpeg.input(
            "pipe:",
            format="rawvideo",
            pix_fmt="rgb24",
            s="{}x{}".format(width, height),
            r=frame_rate,
        )
        .output(sink, format="video4linux2", pix_fmt="yuv420p", r=frame_rate)
        .run_async(pipe_stdin=True)
    )
    assert process.stdin is not None
    async for frame in buffer.frames():
        await loop.run_in_executor(None, process.stdin.write, frame.data)
        logger.debug(f"Wrote frame {len(frame.data)=}")


def buffer_filter(func):
    async def transform_(input_buffer, output_buffer):
        async for input_frame in input_buffer.frames():
            output_frame = func(input_frame)
            if output_frame is not None:
                output_buffer.update(output_frame)

    return transform_


def wash(channel):
    @buffer_filter
    def channel_filter(in_frame: RGBImage) -> RGBImage:
        out_frame = np.zeros(in_frame.data.shape, dtype=np.uint8)
        out_frame[:, :, channel] = in_frame.data[:, :, channel]
        return RGBImage(out_frame)

    return channel_filter


if __name__ == "__main__":

    async def main():
        input_raw_buffer: SingleFrameBuffer[RawImage] = SingleFrameBuffer()
        input_rgb_buffer: SingleFrameBuffer[RGBImage] = SingleFrameBuffer()
        filters = [
            stream_ffmpeg_input(input_raw_buffer, source="/dev/video2"),
            buffer_filter(raw_to_rgb)(input_raw_buffer, input_rgb_buffer),
        ]
        for channel in [0, 1, 2]:
            washed_rgb_buffer: SingleFrameBuffer[RGBImage] = SingleFrameBuffer()
            washed_raw_buffer: SingleFrameBuffer[RawImage] = SingleFrameBuffer()
            filters.extend(
                [
                    wash(channel)(input_rgb_buffer, washed_rgb_buffer),
                    buffer_filter(rgb_to_raw)(washed_rgb_buffer, washed_raw_buffer),
                    stream_ffmpeg_output(
                        washed_raw_buffer, sink=f"/dev/video{channel+4}"
                    ),
                ]
            )
        await asyncio.gather(*filters)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
