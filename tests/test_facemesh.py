import json
import pathlib

import pytest

from webcam_avatar.facemesh import FaceMesh, point_cloud

here = pathlib.Path(__file__).parent


@pytest.fixture
def facemesh_320():
    with open(
        here.parent.joinpath("model_server", "examples", "facemesh-320.json")
    ) as infile:
        return FaceMesh(image_width=320, image_height=240, **json.load(infile)[0])


def test_point_cloud(facemesh_320):
    """ This needs work! """
    image = point_cloud(facemesh_320)
    # Previous conversion was based on width 100?
    assert (image.data == 255).sum() > 1000
