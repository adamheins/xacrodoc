import os
import tempfile

import pytest

from xacrodoc import packages
import xacrodoc


def setup_function():
    # make sure we are working in the `tests` directory
    dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir)

    # ensures packages are reset before each test
    packages.reset()


def test_no_args(capsys):
    with pytest.raises(SystemExit) as e:
        xacrodoc.cli.main(args=[])
    assert e.value.code == 2
    out, err = capsys.readouterr()


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        xacrodoc.cli.main(args=["--version"])
    assert e.value.code == 0
    out, err = capsys.readouterr()
    assert out.strip() == xacrodoc.__version__


def test_urdf(capsys):
    with open("files/urdf/threelink.urdf") as f:
        expected = f.read()
    xacrodoc.cli.main(args=["files/xacro/threelink.urdf.xacro"])
    out, err = capsys.readouterr()
    assert out.strip() == expected.strip()


def test_subargs(capsys):
    with open("files/urdf/tool2.urdf") as f:
        expected = f.read()
    xacrodoc.cli.main(args=["files/xacro/tool.urdf.xacro", "mass:=2"])
    out, err = capsys.readouterr()
    assert out.strip() == expected.strip()


def test_localize_assets(capsys):
    with tempfile.TemporaryDirectory() as asset_dir:
        xacrodoc.cli.main(
            args=["files/xacro/mesh2.urdf.xacro", "-c", asset_dir]
        )
        out, err = capsys.readouterr()

        files = os.listdir(asset_dir)
        assert len(files) == 2
        assert "base.stl" in files
        assert "base_001.stl" in files


def test_package_paths(capsys):
    # here we are really just testing that the argument is accepted
    xacrodoc.cli.main(
        args=["files/xacro/tool.urdf.xacro", "-d", "..", "mass:=2"]
    )
    out, err = capsys.readouterr()


def test_mjcf(capsys):
    try:
        import mujoco
    except ModuleNotFoundError:
        pytest.skip("mujoco could not be imported")

    xacrodoc.cli.main(args=["files/xacro/mesh2.urdf.xacro", "--mjcf"])
    out, err = capsys.readouterr()
