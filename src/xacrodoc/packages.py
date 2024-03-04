from pathlib import Path
from xml.dom import minidom
import rospkg


class PackageNotFoundError(Exception):
    """Raised when a package could not be found."""
    pass


class PackageFinder:
    """Utility to find ROS packages.

    But without relying too much on ROS infrastructure.
    """

    def __init__(self):
        # list of tuples (func, err): func(pkg) looks for the path to package
        # `pkg`, raised error of type `err` if it is not found
        self.finder_funcs = []

        self.package_cache = {}

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

        def finder_func(pkg):
            path = resolved
            while path.as_posix() != path.root:

                # check for package.xml, get the package name from it
                package_xml_path = path / rospkg.common.PACKAGE_FILE
                if package_xml_path.exists():
                    with open(package_xml_path) as f:
                        doc = minidom.parse(f)
                    names = doc.getElementsByTagName("name")

                    if len(names) != 1:
                        raise ValueError(
                            f"Expected one name in {package_xml_path}, but found {len(names)}"
                        )
                    if names[0].firstChild.data == pkg:
                        return path.as_posix()

                # check for manifest.xml (used in the old, deprecated rosbuild
                # system); if it exists, the package name is the directory name
                manifest_xml_path = path / rospkg.common.MANIFEST_FILE
                if manifest_xml_path.exists():
                    return path.as_posix()

                # go up to the next directory
                path = path.parent
            raise PackageNotFoundError(pkg)

        self.finder_funcs.insert(priority, (finder_func, PackageNotFoundError))

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
        # try the cache first
        if pkg in self.package_cache:
            return self.package_cache[pkg]

        # otherwise try a lookup
        for func, err in self.finder_funcs:
            try:
                path = func(pkg)
                self.package_cache[pkg] = path  # add to cache
                return path
            except err:
                continue

        raise PackageNotFoundError(pkg)

    def update_package_cache(self, pkgpaths):
        """Update the package cache.

        Parameters
        ----------
        pkgpaths : dict
            Map from package names to package paths. The paths are resolved,
            made absolute, and converted to strings.
        """
        pkgpaths = {
            pkg: Path(path).resolve().absolute().as_posix()
            for pkg, path in pkgpaths.items()
        }
        self.package_cache.update(pkgpaths)


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


def get_file_path(pkg, relative_path):
    """Get the path to a file within a ROS package.

    Parameters
    ----------
    pkg : str
        The name of the ROS package.
    relative_path : str or Path
        The path of the file relative to the package root.

    Returns
    -------
    : str
        The file path.
    """
    pkgpath = Path(get_path(pkg))
    filepath = pkgpath / relative_path
    return filepath.as_posix()


def update_package_cache(pkgpaths):
    """Update the package cache.

    This allows the user to manually specify the location of packages on the
    filesystem. The path does not actually need to be a proper ROS package,
    meaning that there is no need to have a package.xml file there.

    Parameters
    ----------
    pkgpaths : dict
        Map from package names to package paths. The paths are resolved,
        made absolute, and converted to strings.
    """
    _finder.update_package_cache(pkgpaths)
