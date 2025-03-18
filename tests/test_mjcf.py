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
    doc = XacroDoc.from_file("files/xacro/mesh.urdf.xacro")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mesh.xml"

        # try with and without stripping the absolute path
        doc.to_mjcf_file(path, strippath="false")

        # this fails because we haven't copied the file over despite stripping
        # the path
        with pytest.raises(ValueError):
            doc.to_mjcf_file(path, strippath="true")

        asset_dir = Path(tmp) / "assets"
        doc.localize_assets(asset_dir)
        doc.to_mjcf_file(path, meshdir="assets", strippath="true")


def test_mjcf_existing_mujoco_ext():
    # check that this works when a mujoco extension is already present
    doc = XacroDoc.from_file("files/xacro/threelink_mujoco.urdf.xacro")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "threelink.xml"
        doc.to_mjcf_file(path)
