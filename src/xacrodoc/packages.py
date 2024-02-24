from pathlib import Path
from xml.dom import minidom
import rospkg


class PackageFinder:
    """Utility to find ROS packages.

    But without relying too much on ROS infrastructure.
    """
    def __init__(self):
        # list of tuples (func, err): func(pkg) looks for the path to package
        # `pkg`, raised error of type `err` if it is not found
        self.finder_funcs = []

        try:
            # ament (ROS 2)
            from ament_index_python.packages import (
                get_package_share_directory,
                PackageNotFoundError,
            )

            self.finder_funcs.append(
                (get_package_share_directory, PackageNotFoundError)
            )
        except ImportError:
            # if no ament, fall back to rospkg (ROS 1)
            rospack = rospkg.RosPack()
            self.finder_funcs.append(
                (rospack.get_path, rospkg.common.ResourceNotFound)
            )

    def look_in(self, paths, priority=0):
        rospack = rospkg.RosPack(ros_paths=paths)
        self.finder_funcs.insert(
            priority, (rospack.get_path, rospkg.common.ResourceNotFound)
        )

    def walk_up_from(self, path):
        outer_path = Path(path).resolve()

        def func(pkg):
            path = outer_path
            while path.as_posix() != path.root:

                # check for package.xml, get the package name from it
                package_xml_path = path / "package.xml"
                if package_xml_path.exists():
                    with open(package_xml_path) as f:
                        doc = minidom.parse(f)
                    names = doc.getElementsByTagName("name")

                    # TODO could be zero if malformed
                    assert len(names) == 1, "Multiple names in package.xml"
                    print(f"names = {names}")
                    if names[0].firstChild.data == pkg:
                        return path.as_posix()

                # go up to the next directory
                path = path.parent
            raise ValueError("did not find package")

        self.finder_funcs.append((func, ValueError))

    def get_path(self, pkg):
        for func, err in self.finder_funcs:
            try:
                return func(pkg)
            except err:
                continue

        # TODO use a different error message
        raise ValueError(f"Could not find package {pkg}.")


finder = PackageFinder()
