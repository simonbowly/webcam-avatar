from dataclasses import dataclass
from typing import Any, Optional

import aiohttp
import numpy as np

from .formats import PNGImage, RGBImage


@dataclass
class FaceMesh:
    annotations: Any
    boundingBox: Any
    faceInViewConfidence: float
    mesh: Any
    scaledMesh: Any
    image_width: int
    image_height: int


async def facemesh(image: PNGImage) -> Optional[FaceMesh]:
    width = 320
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://localhost:8080?resizeWidth={width}", data=image.data
        ) as response:
            assert response.status == 200
            predictions = await response.json()
            if predictions:
                return FaceMesh(
                    image_width=width,
                    image_height=image.height * width // image.width,
                    **predictions[0],
                )
            return None


def point_cloud(facemesh: FaceMesh, width=640, height=480) -> RGBImage:
    mesh = np.array(facemesh.scaledMesh)
    x = mesh[:, 0] * width // facemesh.image_width
    x = x.round().astype("int").clip(min=0, max=width - 1)
    y = mesh[:, 1] * height // facemesh.image_height
    y = y.round().astype("int").clip(min=0, max=height - 1)
    render = np.zeros((height, width))
    for xs, ys in zip(x, y):
        render[ys, xs] = 1
    new_image = np.zeros((height, width, 3), dtype=np.uint8)
    new_image[:, :, 2] = (render) * 255
    new_image[:, :, 1] = (render) * 255
    new_image[:, :, 0] = (render) * 255
    return RGBImage(new_image)
