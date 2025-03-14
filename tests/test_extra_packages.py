"""Test compiling xacro files from third-party repositories."""
import os
from pathlib import Path

import pytest

from xacrodoc import XacroDoc, packages


def setup_function():
    # make sure we are working in the `tests` directory
    dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir)

    # ensures packages are reset before each test
    packages.reset()


def test_walkman():
    # walkman is an old package and therefore contains a manifest.xml instead
    # of package.xml
    walkman_pkg_path = Path("packages/iit-walkman-ros-pkg/walkman_urdf")
    if not walkman_pkg_path.exists():
        pytest.skip(
            "Submodule iit-walkman-ros-pkg does not appear to be cloned."
        )
    doc = XacroDoc.from_file(walkman_pkg_path / "urdf/walkman_robot.urdf.xacro")


def test_ur():
    # this is a recent package that makes heavy use of substitutions and other
    # modern xacro features
    ur_urdf_path = Path("packages/Universal_Robots_ROS2_Description/urdf")
    if not ur_urdf_path.exists():
        pytest.skip(
            "Submodule Universal_Robots_ROS2_Description does not appear to be cloned."
        )
    doc = XacroDoc.from_file(
        ur_urdf_path / "ur.urdf.xacro",
        subargs={"ur_type": "ur10", "name": "ur"},
    )
