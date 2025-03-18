import argparse
import sys

from .xacro.xacro.color import error
from .xacro.xacro import XacroException
from .packages import look_in, PackageNotFoundError
from .version import __version__
from .xacrodoc import XacroDoc


def main():
    parser = argparse.ArgumentParser(
        description="Convert a xacro file to URDF. Substitution arguments can be passed as key-value pairs of the form `key:=value`."
    )
    parser.add_argument(
        "xacro_file", type=str, help="The xacro file to convert."
    )
    parser.add_argument("-o", "--output", type=str, help="The output file.")
    parser.add_argument(
        "--mjcf",
        action="store_true",
        help="Convert the xacro file to an MJCF XML file.",
    )
    parser.add_argument(
        "-c",
        "--copy-assets-to",
        type=str,
        help="Localize the file by copying all assets to a local directory.",
    )
    parser.add_argument(
        "-d",
        "--pkg-dir",
        type=str,
        action="extend",
        nargs=1,
        help="Directories in which to search for packages.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=__version__
    )
    args, remainder = parser.parse_known_args()

    if args.mjcf:
        try:
            import mujoco
        except ModuleNotFoundError:
            error(f"Error: could not import mujoco")
            print("You must have mujoco installed to export MJCF XML files.")
            return 1

    # substitution arguments
    subargs = {}
    for arg in remainder:
        key, value = arg.split(":=")
        subargs[key] = value

    # package directories
    if args.pkg_dir is not None:
        look_in(args.pkg_dir)

    # convert file with error handling
    # if converting to mujoco format, then we need to remove the file://
    # protocol from file paths
    try:
        doc = XacroDoc.from_file(args.xacro_file, subargs=subargs)
    except PackageNotFoundError as e:
        error(f"Error: package not found: {e}")
        print("You can specify additional package directories with --pkg-dir")
        return 1
    except Exception as e:
        error(f"Error: {e}")
        return 1

    # it is recommended to localize assets if converted to MJCF
    mjcf_compiler_opts = {}
    if args.copy_assets_to is not None:
        doc.localize_assets(args.copy_assets_to)
        print(f"Copied assets to {args.copy_assets_to}")
        if args.output is not None:
            parent = Path(args.output).parent
            meshdir = os.path.relpath(args.copy_assets_to, parent)
        else:
            meshdir = args.copy_assets_to
        mjcf_compiler_opts["strippath"] = "true"
        mjcf_compiler_opts["meshdir"] = meshdir
    else:
        mjcf_compiler_opts["strippath"] = "false"

    if args.output:
        if args.mjcf:
            doc.to_mjcf_file(args.output, **mjcf_compiler_opts)
        else:
            doc.to_urdf_file(args.output, compare_existing=False)
    else:
        if args.mjcf:
            s = doc.to_mjcf_string(**mjcf_compiler_opts)
        else:
            s = doc.to_urdf_string()
        print(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
