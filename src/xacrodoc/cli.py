import argparse
import os
from pathlib import Path
import sys

from .xacro.xacro.color import error, warning
from .xacro.xacro import XacroException
from .packages import look_in, update_package_cache, PackageNotFoundError
from .version import __version__
from .xacrodoc import XacroDoc


def main(prog="xacrodoc", args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog=prog,
        description="Convert a xacro file to URDF. Substitution arguments can be passed as key-value pairs of the form `key:=value`.",
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
        "-p",
        "--pkg-path",
        type=str,
        action="extend",
        nargs=1,
        help="Mappings of package names to paths, of the form 'name:=path'.",
    )
    parser.add_argument(
        "-r",
        "--relative-paths",
        action="store_true",
        help="Make all asset file paths relative to the output file. Has no effect when exporting to MJCF with --mjcf.",
    )
    parser.add_argument(
        "-s",
        "--strip-protocols",
        action="store_true",
        help="Remove all file:// protocols from asset paths. Has no effect when exporting to MJCF with --mjcf (protocols are always stripped in this case).",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=__version__
    )
    args, remainder = parser.parse_known_args(args)

    if args.mjcf:
        try:
            import mujoco
        except ModuleNotFoundError:
            error(f"Error: could not import mujoco")
            print("You must have mujoco installed to export MJCF XML files.")
            sys.exit(1)

    # substitution arguments
    subargs = {}
    for arg in remainder:
        try:
            key, value = arg.split(":=", maxsplit=1)
        except ValueError:
            error(
                f"Error: expected substitution argument of the form 'name:=value', but got '{arg}'."
            )
            sys.exit(1)
        subargs[key] = value

    # package directories
    if args.pkg_dir is not None:
        look_in(args.pkg_dir)

    # direct mapping from package names to paths
    if args.pkg_path is not None:
        pkg_cache = {}
        for pkg_path in args.pkg_path:
            try:
                name, path = pkg_path.split(":=", maxsplit=1)
            except ValueError:
                error(
                    f"Error: expected package path mapping of the form 'name:=path', but got '{pkg_path}'."
                )
                sys.exit(1)
            pkg_cache[name] = path
        update_package_cache(pkg_cache)

    # convert file with error handling
    try:
        doc = XacroDoc.from_file(args.xacro_file, subargs=subargs)
    except PackageNotFoundError as e:
        error(f"Error: package not found: {e}")
        print(
            "You can specify additional package locations with --pkg-dir or --pkg-path."
        )
        print("See --help for more details.")
        sys.exit(1)
    except Exception as e:
        error(f"Error: {e}")
        sys.exit(1)

    num_assets = doc.count_assets()
    if args.mjcf:
        if num_assets > 0 and args.copy_assets_to is None:
            error(
                f"Error: when exporting to MJCF, --copy-assets-to must be specified when the file references assets."
            )
            sys.exit(1)
        if args.relative_paths:
            warning(
                "Warning: --relative-paths has no effect when exporting to MJCF."
            )

    mjcf_compiler_opts = {}
    if args.copy_assets_to is not None:
        if num_assets == 0:
            warning(
                "Warning: ignoring --copy-assets-to because the file does not reference any assets."
            )
        else:
            doc.localize_assets(args.copy_assets_to)
            print(f"Copied assets to '{args.copy_assets_to}'.")

            # we always use a relative path to the meshdir
            parent = (
                Path(args.output).parent
                if args.output is not None
                else Path.cwd()
            )
            meshdir = os.path.relpath(
                os.path.abspath(args.copy_assets_to), parent
            )

            mjcf_compiler_opts["meshdir"] = meshdir
            mjcf_compiler_opts["strippath"] = "true"

    if args.output:
        if args.mjcf:
            doc.to_mjcf_file(args.output, **mjcf_compiler_opts)
        else:
            doc.to_urdf_file(
                args.output,
                compare_existing=False,
                relative_paths=args.relative_paths,
                file_protocols=not args.strip_protocols,
            )
    else:
        if args.mjcf:
            s = doc.to_mjcf_string(**mjcf_compiler_opts)
        else:
            paths_relative_to = Path.cwd() if args.relative_paths else None
            s = doc.to_urdf_string(
                paths_relative_to=paths_relative_to,
                file_protocols=not args.strip_protocols,
            )
        print(s)
    sys.exit(0)
