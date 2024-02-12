from xacrodoc import XacroDoc


def test_from_file():
    doc = XacroDoc.from_file("files/threelink.urdf.xacro")
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string() == expected


def test_from_package_file():
    doc = XacroDoc.from_package_file(
        "xacrodoc", "tests/files/threelink.urdf.xacro"
    )
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string() == expected


def test_from_includes():
    includes = ["files/threelink.urdf.xacro", "files/tool.urdf.xacro"]
    doc = XacroDoc.from_includes(includes, name="combined")
    with open("files/combined.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string() == expected


def test_from_includes_ros_find():
    # handle $(find ...) directives
    includes = [
        "$(find xacrodoc)/tests/files/threelink.urdf.xacro",
        "$(find xacrodoc)/tests/files/tool.urdf.xacro",
    ]
    doc = XacroDoc.from_includes(includes, name="combined")
    with open("files/combined.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string() == expected


def test_subargs():
    doc = XacroDoc.from_file("files/tool.urdf.xacro", subargs={"mass": "2"})
    with doc.temp_urdf_file_path() as path:
        with open(path) as f:
            text = f.read()
    with open("files/tool2.urdf") as f:
        expected = f.read()
    assert text == expected


def test_temp_urdf_file():
    doc = XacroDoc.from_file("files/threelink.urdf.xacro")
    with doc.temp_urdf_file_path() as path:
        with open(path) as f:
            text = f.read()
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert text == expected
