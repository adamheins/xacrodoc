from xacrodoc import XacroDoc


def test_compile():
    doc = XacroDoc.from_file("files/threelink.urdf.xacro")
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string() == expected


def test_from_includes():
    doc = XacroDoc.from_file("files/threelink.urdf.xacro")
    with open("files/threelink.urdf") as f:
        expected = f.read()
    assert doc.to_urdf_string() == expected


def test_temp_urdf_file():
    pass
