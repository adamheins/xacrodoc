import pytest

from xacrodoc import XacroDoc


def _ros_installed():
    # check if ROS is installed
    try:
        import roslaunch
    except ImportError:
        return False
    return True


def test_from_file():
    doc = XacroDoc.from_file("files/threelink.urdf.xacro")
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_from_package_file():
    if not _ros_installed():
        pytest.skip("ROS is required.")

    doc = XacroDoc.from_package_file(
        "xacrodoc", "tests/files/threelink.urdf.xacro"
    )
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_from_includes():
    if not _ros_installed():
        pytest.skip("ROS is required.")

    includes = ["files/threelink.urdf.xacro", "files/tool.urdf.xacro"]
    doc = XacroDoc.from_includes(includes, name="combined")
    with open("files/combined.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string().strip() == expected.strip()


def test_from_includes_ros_find():
    if not _ros_installed():
        pytest.skip("ROS is required.")

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
    if not _ros_installed():
        pytest.skip("ROS is required.")

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
