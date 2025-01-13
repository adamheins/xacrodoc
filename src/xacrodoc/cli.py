import argparse

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
    parser.add_argument(
        "-o", "--output", type=str, help="The output URDF file."
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

    # substitution arguments
    subargs = {}
    for arg in remainder:
        key, value = arg.split(":=")
        subargs[key] = value

    # package directories
    if args.pkg_dir is not None:
        look_in(args.pkg_dir)

    # convert file with error handling
    try:
        doc = XacroDoc.from_file(args.xacro_file, subargs=subargs)
    except PackageNotFoundError as e:
        print(f"Error: package not found: {e}")
        print("You can specify additional package directories with --pkg-dir")
        return
    except XacroException as e:
        print(f"Error: {e}")
        return

    # output
    if args.output:
        doc.to_urdf_file(args.output, compare_existing=False)
    else:
        print(doc.to_urdf_string())


if __name__ == "__main__":
    main()
