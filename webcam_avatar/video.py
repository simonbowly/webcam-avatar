import subprocess
import atexit
import contextlib
import time

import cv2
import requests
import numpy as np


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


@contextlib.contextmanager
def video_capture(arg):
    cap = cv2.VideoCapture(arg)
    try:
        yield cap
    finally:
        cap.release()


command = [
    "ffmpeg",
    "-f",
    "rawvideo",
    "-pix_fmt",
    "bgr24",
    "-s",
    "640x480",
    "-r",
    "20",  # 30 fps
    "-i",
    "-",  # Read from piped stdin
    "-an",  # No audio
    "-f",
    "v4l2",  # output format
    "-r",
    "20",  # output fps
    "/dev/video2",
]


def close_proc(proc):
    print("cleanly exiting {}".format("ffmpeg"))
    proc.stdin.close()
    if proc.stderr is not None:
        proc.stderr.close()
    proc.wait()


print("Control-C to exit.")
proc = subprocess.Popen(command, stdin=subprocess.PIPE)
atexit.register(lambda: close_proc(proc))


cv2.imshow("frame", np.zeros((480, 640)))

with video_capture(0) as cap:

    frame_times = []

    while True:

        # Capture frame-by-frame
        start_read_frame = time.perf_counter_ns()
        ret, frame = cap.read()
        end_read_frame = time.perf_counter_ns()
        data = cv2.imencode(".jpg", frame)[1].tobytes()
        end_encode = time.perf_counter_ns()
        response = requests.post("http://localhost:8080", data=data)
        predictions = response.json()
        end_prediction = time.perf_counter_ns()

        if len(predictions) > 0:
            if predictions[0]["faceInViewConfidence"] > 0.5:
                status = "GOOD"
                render = to_point_cloud(predictions[0])
                render_rgb = cv2.cvtColor(
                    (render * 255).round().astype("uint8"), cv2.COLOR_GRAY2RGB
                )
                cv2.imshow("frame", render_rgb)
                proc.stdin.write(render_rgb.tostring())
            else:
                status = "LOW_CONFIDENCE"
        else:
            status = "NO_DETECTION"
        end_render = time.perf_counter_ns()

        time_read_frame = (end_read_frame - start_read_frame) * 10 ** -6
        time_encode = (end_encode - end_read_frame) * 10 ** -6
        time_facemesh = (end_prediction - end_encode) * 10 ** -6
        time_render = (end_render - end_prediction) * 10 ** -6
        frame_times.append((end_render - start_read_frame) * 10 ** -6)

        # Now we just plot some points and imshow or pipe?

        fps = 0.0
        if len(frame_times) > 10:
            fps = 10000.0 / sum(frame_times[-10:])
        print(
            f"{time_read_frame=:6.2f}ms {time_encode=:6.2f}ms {time_facemesh=:6.2f}ms {time_render=:6.2f}ms {fps=:5.1f} {status=}"
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
