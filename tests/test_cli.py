import os
import re
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

    with pytest.raises(SystemExit) as e:
        xacrodoc.cli.main(args=["files/xacro/threelink.urdf.xacro"])
    assert e.value.code == 0

    out, err = capsys.readouterr()
    assert out.strip() == expected.strip()


def test_subargs(capsys):
    with open("files/urdf/tool2.urdf") as f:
        expected = f.read()

    with pytest.raises(SystemExit) as e:
        xacrodoc.cli.main(args=["files/xacro/tool.urdf.xacro", "mass:=2"])
    assert e.value.code == 0

    out, err = capsys.readouterr()
    assert out.strip() == expected.strip()


def test_localize_assets(capsys):
    with tempfile.TemporaryDirectory() as asset_dir:
        with pytest.raises(SystemExit) as e:
            xacrodoc.cli.main(
                args=["files/xacro/mesh2.urdf.xacro", "-c", asset_dir]
            )
        assert e.value.code == 0

        files = os.listdir(asset_dir)
        assert len(files) == 2
        assert "base.stl" in files
        assert "base_001.stl" in files

    # also test when we have an output file
    with tempfile.TemporaryDirectory() as dir:
        asset_dir = os.path.join(dir, "assets")
        urdf_file = os.path.join(dir, "output.urdf")
        with pytest.raises(SystemExit) as e:
            xacrodoc.cli.main(
                args=[
                    "files/xacro/mesh2.urdf.xacro",
                    "-c",
                    asset_dir,
                    "-o",
                    urdf_file,
                ]
            )
        assert e.value.code == 0

        files = os.listdir(asset_dir)
        assert len(files) == 2
        assert "base.stl" in files
        assert "base_001.stl" in files


def test_package_paths(capsys):
    # first check it fails without the package path
    with pytest.raises(SystemExit) as e:
        xacrodoc.cli.main(args=["files/xacro/mesh_external_package.urdf.xacro"])
    assert e.value.code == 1

    # then check it works when we provide the package path
    with pytest.raises(SystemExit) as e:
        xacrodoc.cli.main(
            args=[
                "files/xacro/mesh_external_package.urdf.xacro",
                "-p",
                "my_pkg:=packages/my_pkg",
            ]
        )
    assert e.value.code == 0

    # alternatively, we can just set a package directory to automatically find
    # packages
    with pytest.raises(SystemExit) as e:
        xacrodoc.cli.main(
            args=[
                "files/xacro/mesh_external_package.urdf.xacro",
                "-d",
                "packages",
            ]
        )
    assert e.value.code == 0


def test_mjcf(capsys):
    try:
        import mujoco
    except ModuleNotFoundError:
        pytest.skip("mujoco could not be imported")

    # this will complain because we need -c when there are assets
    with pytest.raises(SystemExit) as e:
        xacrodoc.cli.main(args=["files/xacro/mesh2.urdf.xacro", "--mjcf"])
    assert e.value.code == 1

    # this URDF has no assets, so we don't need -c
    with pytest.raises(SystemExit) as e:
        xacrodoc.cli.main(args=["files/xacro/threelink.urdf.xacro", "--mjcf"])
    assert e.value.code == 0
