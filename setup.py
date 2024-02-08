#!/usr/bin/env python

# ! DO NOT MANUALLY INVOKE THIS setup.py, USE CATKIN INSTEAD

from setuptools import setup
from catkin_pkg.python_setup import generate_distutils_setup

setup_args = generate_distutils_setup(
    name="xacrodoc",
    version="0.0.1",
    packages=["xacrodoc"],
    package_dir={"": "xacrodoc"},
    install_requires=["xacro", "rospkg"],
)

setup(**setup_args)
