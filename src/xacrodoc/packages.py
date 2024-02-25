from pathlib import Path
from xml.dom import minidom
import rospkg


class PackageNotFoundError(Exception):
    pass


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
        """Add additional directories to search for packages.

        Parameters
        ----------
        paths : Iterable
            A list of paths in which to search for packages. Internally, these
            are passed to `rospkg.RosPack`.
        priority : int
            Priority for the search: lower means the package is looked for
            using this method earlier.
        """
        rospack = rospkg.RosPack(ros_paths=paths)
        self.finder_funcs.insert(
            priority, (rospack.get_path, rospkg.common.ResourceNotFound)
        )

    def walk_up_from(self, path, priority=0):
        """Look for packages by walking up the directory tree from ``path``.

        Parameters
        ----------
        path : str or pathlib.Path
            The path at which to start looking for packages.
        priority : int
            Priority for the search: lower means the package is looked for
            using this method earlier.
        """
        resolved = Path(path).resolve()

        def func(pkg):
            path = resolved
            while path.as_posix() != path.root:

                # check for package.xml, get the package name from it
                package_xml_path = path / "package.xml"
                if package_xml_path.exists():
                    with open(package_xml_path) as f:
                        doc = minidom.parse(f)
                    names = doc.getElementsByTagName("name")

                    if len(names) != 1:
                        raise ValueError(
                            f"Excepted one name in {package_xml_path}, but found {len(names)}"
                        )
                    if names[0].firstChild.data == pkg:
                        return path.as_posix()

                # go up to the next directory
                path = path.parent
            raise PackageNotFoundError(pkg)

        self.finder_funcs.insert(priority, (func, PackageNotFoundError))

    def get_path(self, pkg):
        """Attempt to get the path of a package.

        Parameters
        ----------
        pkg : str
            The name of the package.

        Returns
        -------
        : str
            The path to the package.

        Raises
        ------
        PackageNotFoundError
            If the package could not be found.
        """
        for func, err in self.finder_funcs:
            try:
                return func(pkg)
            except err:
                continue

        raise PackageNotFoundError(pkg)


# global package finder
_finder = PackageFinder()


def reset():
    """Reset the package finder to the default look-up methods."""
    global _finder
    _finder = PackageFinder()


def look_in(paths, priority=0):
    """Add additional directories to search for packages.

    Parameters
    ----------
    paths : Iterable
        A list of paths in which to search for packages. Internally, these are
        passed to `rospkg.RosPack`.
    priority : int
        Priority for the search: lower means the package is looked for using
        this method earlier.
    """
    _finder.look_in(paths, priority=priority)


def walk_up_from(path, priority=0):
    """Look for packages by walking up the directory tree from ``path``.

    Parameters
    ----------
    path : str or pathlib.Path
        The path at which to start looking for packages.
    priority : int
        Priority for the search: lower means the package is looked for using
        this method earlier.
    """
    _finder.walk_up_from(path, priority=priority)


def get_path(pkg):
    """Attempt to get the path of a package.

    Parameters
    ----------
    pkg : str
        The name of the package.

    Returns
    -------
    : str
        The path to the package.

    Raises
    ------
    PackageNotFoundError
        If the package could not be found.
    """
    return _finder.get_path(pkg)
