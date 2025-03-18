import os
from pathlib import Path
import tempfile

import pytest

from xacrodoc import XacroDoc, packages


def setup_function():
    # make sure we are working in the `tests` directory
    dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir)

    # ensures packages are reset before each test
    packages.reset()


def test_from_file():
    doc = XacroDoc.from_file("files/xacro/threelink.urdf.xacro")
    with open("files/urdf/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_from_package_file():
    packages.walk_up_from(__file__)
    doc = XacroDoc.from_package_file(
        "xacrodoc", "tests/files/xacro/threelink.urdf.xacro"
    )
    with open("files/urdf/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_from_includes():
    includes = [
        "files/xacro/threelink.urdf.xacro",
        "files/xacro/tool.urdf.xacro",
    ]
    doc = XacroDoc.from_includes(includes, name="combined")
    with open("files/urdf/combined.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_from_includes_ros_find():
    packages.walk_up_from(__file__)

    # handle $(find ...) directives
    includes = [
        "$(find xacrodoc)/tests/files/xacro/threelink.urdf.xacro",
        "$(find xacrodoc)/tests/files/xacro/tool.urdf.xacro",
    ]
    doc = XacroDoc.from_includes(includes, name="combined")
    with open("files/urdf/combined.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_subargs():
    subargs = {"mass": "2"}
    doc = XacroDoc.from_file("files/xacro/tool.urdf.xacro", subargs=subargs)
    with doc.temp_urdf_file_path() as path:
        with open(path) as f:
            text = f.read()
    with open("files/urdf/tool2.urdf") as f:
        expected = f.read()
    assert text.strip() == expected.strip()


def test_temp_urdf_file():
    doc = XacroDoc.from_file("files/xacro/threelink.urdf.xacro")

    # write to a temporary file and read back
    path = doc.to_temp_urdf_file()
    with open(path) as f:
        text = f.read()

    # clean up the temp file
    os.remove(path)

    # compare to expected URDF
    with open("files/urdf/threelink.urdf") as f:
        expected = f.read()

    assert text.strip() == expected.strip()


def test_temp_urdf_file_path():
    doc = XacroDoc.from_file("files/xacro/threelink.urdf.xacro")

    # write to a temporary file and read back
    with doc.temp_urdf_file_path() as path:
        with open(path) as f:
            text = f.read()

    # compare to expected URDF
    with open("files/urdf/threelink.urdf") as f:
        expected = f.read()

    assert text.strip() == expected.strip()


def test_resolve_packages():
    # spoof package paths so these all point to the same package (this one)
    # want to test hyphens and underscores in the package names
    packages.update_package_cache(
        {
            "xacrodoc": "..",
            "fake-package": "..",
            "another_fake_package": "..",
        }
    )

    expected = "file://" + Path("files/assets/base.stl").absolute().as_posix()
    doc = XacroDoc.from_file("files/xacro/mesh_different_packages.urdf.xacro")
    for element in doc.doc.getElementsByTagName("mesh"):
        filename = element.getAttribute("filename")
        assert filename == expected


def test_include_from_arg():
    # just see if this can compile
    # we want to ensure that $(find) can be nested in an $(arg)
    doc = XacroDoc.from_file(
        "files/xacro/combined_from_arg.urdf.xacro",
        subargs={
            "robotfile": "$(find xacrodoc)/tests/files/xacro/threelink.urdf.xacro"
        },
    )


def test_package_cache():
    # manually specify a (non-resolved) path to xacrodoc and disable walking up
    # the directory tree
    packages.update_package_cache({"xacrodoc": "../.."})
    doc = XacroDoc.from_file("files/xacro/threelink.urdf.xacro", walk_up=False)
    with open("files/urdf/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_localize_assets():
    doc = XacroDoc.from_file("files/xacro/mesh2.urdf.xacro")
    with tempfile.TemporaryDirectory() as asset_dir:
        doc.localize_assets(asset_dir)
        files = os.listdir(asset_dir)
        assert len(files) == 2
        assert "base.stl" in files
        assert "base_001.stl" in files
