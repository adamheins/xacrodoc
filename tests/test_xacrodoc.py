from pathlib import Path

import pytest

from xacrodoc import XacroDoc, packages


def test_from_file():
    doc = XacroDoc.from_file("files/threelink.urdf.xacro")
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_from_package_file():
    doc = XacroDoc.from_package_file(
        "xacrodoc", "tests/files/threelink.urdf.xacro"
    )
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_from_includes():
    includes = ["files/threelink.urdf.xacro", "files/tool.urdf.xacro"]
    doc = XacroDoc.from_includes(includes, name="combined")
    with open("files/combined.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_from_includes_ros_find():
    # handle $(find ...) directives
    includes = [
        "$(find xacrodoc)/tests/files/threelink.urdf.xacro",
        "$(find xacrodoc)/tests/files/tool.urdf.xacro",
    ]
    doc = XacroDoc.from_includes(includes, name="combined")
    with open("files/combined.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_subargs():
    subargs = {"mass": "2"}
    doc = XacroDoc.from_file("files/tool.urdf.xacro", subargs=subargs)
    with doc.temp_urdf_file_path() as path:
        with open(path) as f:
            text = f.read()
    with open("files/tool2.urdf") as f:
        expected = f.read()
    assert text.strip() == expected.strip()


def test_temp_urdf_file():
    doc = XacroDoc.from_file("files/threelink.urdf.xacro")
    with doc.temp_urdf_file_path() as path:
        with open(path) as f:
            text = f.read()
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert text.strip() == expected.strip()


def test_resolve_package_name():
    doc = XacroDoc.from_file("files/mesh.urdf.xacro")
    expected = Path("files/fakemesh.txt").absolute().as_posix()
    for element in doc.doc.getElementsByTagName("mesh"):
        filename = element.getAttribute("filename")
        assert filename == expected


def test_include_from_arg():
    # just see if this can compile
    # we want to ensure that $(find) can be nested in an $(arg)
    doc = XacroDoc.from_file(
        "files/combined_from_arg.urdf.xacro",
        subargs={"robotfile": "$(find xacrodoc)/tests/files/threelink.urdf.xacro"},
    )
