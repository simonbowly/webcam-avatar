import subprocess
import time

import requests

frame_rate = 20
width = 640
height = 480

command = [
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
    "rgb24",
    "-vcodec",
    "rawvideo",
    "-",
]
pipe = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10 ** 8)

average_over = 30

try:
    frame_times = []
    i = 0
    while True:
        raw_image = pipe.stdout.read(width * height * 3)
        # Make this a shared thing in asyncio scheme that's overwritten on each new frame.
        frame_times.append(time.time())
        if len(frame_times) > average_over and i % frame_rate == 0:
            fps = average_over / (frame_times[-1] - frame_times[-average_over - 1])
            # Asynchronously get this from the latest frame on a schedule.
            response = requests.post(
                # Pass image dimensions for the ra w decoder
                f"http://localhost:8080?resizeWidth={width}",
                data=raw_image,
            )
            print(f"{fps=} {type(raw_image)=} {response.status_code}\n")

        i += 1
except KeyboardInterrupt:
    print("Aborted")
finally:
    pipe.stdout.close()
    pipe.kill()
    pipe.wait()


"""
Something like this? Writing it this way because if nodejs server generates the
mesh and blender server generates the image then running the supervising process
asyncronously should recruit more things in parallel to better keep up with the
frame rate?
"""


import asyncio
from dataclasses import dataclass


@dataclass
class SingleFrameBuffer:
    raw_image: bytes = None
    fresh: bool = False

    def update(self, data):
        self.raw_image = data
        self.fresh = True


async def stream_input_frames(buffer: SingleFrameBuffer, frame_bytes: int):
    ffmpeg_command = ["ffmpeg"]
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_command, stdout=subprocess.PIPE
    )
    # Handle various exit conditions for the subprocess.
    while True:
        raw_image = await process.stdout.read(frame_bytes)
        buffer.update(raw_image)


async def facemesh(image_buffer: SingleFrameBuffer, mesh_buffer):
    """ Update the mesh buffer as fast as possible. """
    while True:
        if buffer.fresh:
            raw_image = copy(image_buffer.raw_image)
            response = await aiohttp.Client.post(
                "http://localhost:8080/?width=width&height=height",
                data=raw_image,
            )
            facemesh = await response.json()
            mesh_buffer.update(facemesh)
        else:
            # Sleep if not fresh (although a wake trigger might be nicer).
            asyncio.sleep(0.01)


async def render():
    """ Something similar for mesh -> image, run only when fresh. """
    # This should do the trick as a rawvideo or image2pipe
    assert len(np.zeros((640, 480, 3), dtype="int8").tobytes()) == 640 * 480 * 3
    pass


async def stream_output_frames(render_buffer):
    """Create another ffmpeg process and write the frame (whether fresh or not)
    on a regular schedule. Could also run several of these to multiple virtual
    cameras so that all the intermediate results are available to switch between.
    """
    # ffmpeg -f rawvideo -pixel_format bgr24 -video_size 640x480 -framerate 30 -i - foo.avi
    # Framerate should match the schedule, video_size the dimensions, bgr the order
    # render_buffer class should contain and check this info
    # Note bgr24 = 24 bits per pixel (3 x 8)
    # Presumably buffer[:, :, 0] is blue channel?
    pass


async def main():
    # Create intermediate buffers.
    # Create all coroutines.
    # Run all with gather or similar?
    pass


# For command instruction help:
# https://github.com/kkroening/ffmpeg-python
