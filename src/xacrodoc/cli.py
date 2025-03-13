import argparse
import sys

from .color import error
from .packages import look_in, PackageNotFoundError
from .xacro import XacroException
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
        "-d",
        "--pkg-dir",
        type=str,
        action="extend",
        nargs="*",
        help="Directories in which to search for packages.",
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
        doc = XacroDoc.from_file(
            args.xacro_file, subargs=subargs, remove_protocols=args.mjcf
        )
    except PackageNotFoundError as e:
        error(f"Error: package not found: {e}")
        print("You can specify additional package directories with --pkg-dir")
        return 1
    except Exception as e:
        error(f"Error: {e}")
        return 1

    # tell mujoco to keep the full paths to assets
    if args.mjcf:
        doc.add_mujoco_extension()

    # output
    if args.output:
        if args.mjcf:
            doc.to_mjcf_file(args.output)
        else:
            doc.to_urdf_file(args.output, compare_existing=False)
    else:
        print(doc.to_urdf_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
