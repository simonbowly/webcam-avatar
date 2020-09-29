"""
Pass various image data formats to the server.
"""

import itertools
import json
import pprint

import cv2
import requests
from matplotlib import image


def head(d):
    return "\n".join(itertools.islice(pprint.pformat(d).split("\n"), 5))


with open("examples/input.jpg", "rb") as infile:
    jpeg_image_data = infile.read()

image_pixels = image.imread("examples/input.jpg")
png_image_data = cv2.imencode(".png", image_pixels)[1].tobytes()

response = requests.post("http://localhost:8080?resizeWidth=100", data=b"")
assert response.status_code == 400

for width in [160, 320, 640]:
    response = requests.post(
        f"http://localhost:8080?resizeWidth={width}", data=png_image_data
    )
    assert response.status_code == 200
    predictions = response.json()
    assert len(predictions) == 1

for width in [160, 320, 640]:
    response = requests.post(
        f"http://localhost:8080?resizeWidth={width}", data=jpeg_image_data
    )
    assert response.status_code == 200
    predictions = response.json()
    assert len(predictions) == 1
    with open(f"examples/facemesh-{width}.json", "w") as outfile:
        json.dump(predictions, outfile, sort_keys=True, indent=4)

facemesh = response.json()[0]
print(facemesh.keys())

for key in ["faceInViewConfidence", "boundingBox", "mesh", "scaledMesh", "annotations"]:
    print()
    print(f"=== {key} ===")
    print(head(facemesh[key]))
