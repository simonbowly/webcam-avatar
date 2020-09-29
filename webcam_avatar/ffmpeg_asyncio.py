import asyncio
import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SingleFrameBuffer:
    raw_image: bytes = b""
    fresh: bool = False

    def update(self, data):
        self.raw_image = data
        self.fresh = True
        logger.debug("Frame buffer updated")


async def stream_input_frames(buffer: SingleFrameBuffer):
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
        buffer.update(raw_image)


async def stream_output_frames(buffer: SingleFrameBuffer):
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
        "/dev/video4",
    ]
    process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    while True:
        await asyncio.sleep(0.05)
        if buffer.raw_image:
            await loop.run_in_executor(None, process.stdin.write, buffer.raw_image)
