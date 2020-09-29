#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent
try:
    long_description = here.joinpath("README.md").read_text()
except FileNotFoundError:
    long_description = ""

setup(
    name="webcam_avatar",
    version="0.1.0",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Simon Bowly",
    author_email="simon.bowly@gmail.com",
    python_requires=">=3.6",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    # entry_points={"console_scripts": ["command=package.module:cli"]},
    install_requires=[],
    extras_require={},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)
