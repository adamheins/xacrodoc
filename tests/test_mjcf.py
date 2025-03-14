import os
from pathlib import Path
import tempfile

import pytest

from xacrodoc import XacroDoc, packages


def setup_function():
    try:
        import mujoco
    except ModuleNotFoundError:
        pytest.skip("mujoco could not be imported")

    # make sure we are working in the `tests` directory
    dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir)

    # ensures packages are reset before each test
    packages.reset()


def test_mjcf():
    doc = XacroDoc.from_file(
        "files/threelink.urdf.xacro", remove_protocols=True
    )
    doc.add_mujoco_extension()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "threelink.xml"
        doc.to_mjcf_file(path)


def test_mjcf_existing_mujoco_ext():
    # check that this works when a mujoco extension is already present
    doc = XacroDoc.from_file(
        "files/threelink_mujoco.urdf.xacro", remove_protocols=True
    )
    doc.add_mujoco_extension()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "threelink.xml"
        doc.to_mjcf_file(path)
