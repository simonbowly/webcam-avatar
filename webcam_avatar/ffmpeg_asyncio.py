import asyncio
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Optional, List, Generic, TypeVar

from .formats import RawImage, PNGImage

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


async def stream_input_frames(buffer: SingleFrameBuffer[RawImage]):
    loop = asyncio.get_event_loop()
    frame_rate = 30
    width = 640
    height = 480
    ffmpeg_command = [
        "ffmpeg",
        "-i",
        "/dev/video0",
        "-f",
        "image2pipe",
        "-s",
        f"{width}x{height}",
        "-r",
        str(frame_rate),
        "-pix_fmt",
        "bgr24",
        "-vcodec",
        "rawvideo",
        "-",
    ]
    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, bufsize=10 ** 8)
    assert process.stdout is not None

    def read_frame():
        return process.stdout.read(width * height * 3)

    while True:
        raw_image = await loop.run_in_executor(None, read_frame)
        buffer.update(RawImage(data=raw_image, width=width, height=height))


async def stream_output_frames_raw(buffer: SingleFrameBuffer[RawImage], path: str):
    loop = asyncio.get_event_loop()
    ffmpeg_command = [
        "ffmpeg",
        "-f",
        "rawvideo",
        "-pixel_format",
        "bgr24",
        "-video_size",
        "640x480",
        "-framerate",
        "20",
        "-i",
        "-",
        "-f",
        "v4l2",
        path,
    ]
    process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    async for frame in buffer.frames():
        await loop.run_in_executor(None, process.stdin.write, frame.data)


async def stream_output_frames_png(buffer: SingleFrameBuffer[PNGImage], path: str):
    loop = asyncio.get_event_loop()
    ffmpeg_command = [
        "ffmpeg",
        "-f",
        "image2pipe",
        "-framerate",
        "30",
        "-i",
        "-",
        "-vcodec",
        "rawvideo",
        "-vf",
        "format=yuv420p",
        "-r",
        "10",
        "-f",
        "v4l2",
        path,
    ]
    process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    async for frame in buffer.frames():
        await loop.run_in_executor(None, process.stdin.write, frame.data)
