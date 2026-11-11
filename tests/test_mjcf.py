import os
from pathlib import Path
import re
import tempfile

import pytest

from xacrodoc import XacroDoc, packages


def assert_mjcf_equivalent(actual, expected):
    """Assert that two MJCF strings compile to equivalent models.

    The exact XML that mujoco writes (attribute order, whether default values
    are written out) varies across mujoco versions, so we compare the compiled
    models rather than the raw strings.

    Parameters
    ----------
    actual : str
        Actual string of Mujoco XML.
    expected: str
        Expected string of Mujoco XML.
    """
    import mujoco
    import numpy as np

    m1 = mujoco.MjModel.from_xml_string(actual)
    m2 = mujoco.MjModel.from_xml_string(expected)

    for name in dir(m1):
        if name.startswith("_"):
            continue
        try:
            a, b = getattr(m1, name), getattr(m2, name)
        except Exception:
            continue
        if isinstance(a, np.ndarray):
            assert a.shape == b.shape, name
            assert np.allclose(a, b, equal_nan=True), name
        elif isinstance(a, (bool, int, float, str, bytes)):
            assert a == b, name


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


def test_mjcf_existing_mujoco_extension():
    with open("files/mjcf/threelink.xml") as f:
        expected = f.read()

    # check that this works when a mujoco extension is already present
    doc = XacroDoc.from_file("files/xacro/threelink_mujoco.urdf.xacro")
    assert_mjcf_equivalent(doc.to_mjcf_string(), expected)


def test_to_mjcf_file():
    doc = XacroDoc.from_file("files/xacro/threelink_mujoco.urdf.xacro")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "threelink.xml"
        doc.to_mjcf_file(path)


def test_rootdir():
    doc = XacroDoc.from_file("files/xacro/mesh_rel_path.urdf.xacro")

    # the mesh file is specified with a relative path to the URDF file
    # ensure that it resolves correctly
    s = doc.to_mjcf_string(strippath="false")
    matches = re.findall(r'file="(.+)"', s)
    assert Path(matches[0]).exists()
