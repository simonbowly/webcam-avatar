import aiohttp
import cv2

from .formats import bytes_to_rgb


async def facemesh(raw_image_data):
    image_pixels = bytes_to_rgb({"width": 640, "height": 480, "data": raw_image_data})
    png_image_data = cv2.imencode(".png", image_pixels)[1].tobytes()
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8080?resizeWidth=100", data=png_image_data
        ) as response:
            assert response.status == 200
            return await response.json()
