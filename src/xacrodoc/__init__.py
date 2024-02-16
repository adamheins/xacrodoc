from contextlib import contextmanager
import os
from pathlib import Path
import tempfile

import rospkg
import xacro


def _xacro_include(path):
    return f"""
    <xacro:include filename="{path}" />
    """


def _xacro_header(name):
    return f"""<?xml version="1.0" encoding="utf-8"?>
    <robot name="{name}" xmlns:xacro="http://www.ros.org/wiki/xacro">
    """.strip()


def _xacro_compile(text, subargs=None, max_runs=10):
    """Compile xacro string until a fixed point is reached.

    Parameters
    ----------
    text : str
        The xacro string.
    subargs : dict or None
        Optional dictionary of substitution arguments to pass into xacro.
    max_runs : int
        Maximum number of compilation runs.

    Raises
    ------
    ValueError
        If ``max_runs`` compilations are exceeded.

    Returns
    -------
    :
        The URDF XML document.
    """
    if subargs is None:
        subargs = {}
    doc = xacro.parse(text)
    s1 = doc.toxml()

    run = 1
    while run < max_runs:
        xacro.process_doc(doc, mappings=subargs)
        s2 = doc.toxml()
        if s1 == s2:
            break
        s1 = s2
        run += 1

    if run >= max_runs:
        raise ValueError("URDF file did not converge.")
    return doc


def package_path(package_name):
    """Get the path to a ROS package.

    Parameters
    ----------
    package_name : str
        The name of the package

    Returns
    -------
    : Path
        The package path.
    """
    rospack = rospkg.RosPack()
    return Path(rospack.get_path(package_name))


def package_file_path(package_name, relative_path):
    """Get the path to a file within a ROS package.

    Parameters
    ----------
    package_name : str
        The name of the ROS package.
    relative_path : str or Path
        The path of the file relative to the package root.

    Returns
    -------
    : Path
        The file path.
    """
    return package_path(package_name) / relative_path


class XacroDoc:
    """Convenience class to build URDF strings and files out of xacro components.

    Parameters
    ----------
    text : str
        The xacro text to compile into a URDF document.
    subargs : dict or None
        Optional dict of substitution arguments; i.e., the values of
        ``<xacro:arg ...>`` directives. Equivalent to writing ``value:=foo`` on
        the command line.
    max_runs : int
        The text is repeated compiled until a fixed point is reached; i.e.,
        compilation of the text just returns the same text. ``max_runs`` is the
        maximum number of times compilation will be performed.

    Attributes
    ----------
    doc :
        The underlying XML document.
    """

    def __init__(self, text, subargs=None, max_runs=10):
        self.doc = _xacro_compile(text=text, subargs=subargs, max_runs=max_runs)

    @classmethod
    def from_file(cls, path, **kwargs):
        """Load the URDF document from a xacro file.

        Parameters
        ----------
        path : str or Path
            The path to the xacro file.
        """
        with open(path) as f:
            text = f.read()
        return cls(text, **kwargs)

    @classmethod
    def from_package_file(cls, package_name, relative_path, **kwargs):
        """Load the URDF document from a xacro file in a ROS package.

        Parameters
        ----------
        package_name : str
            The name of the ROS package.
        relative_path : str or Path
            The path of the xacro file relative to the ROS package.
        """
        path = package_file_path(package_name, relative_path)
        return cls.from_file(path, **kwargs)

    @classmethod
    def from_includes(cls, includes, name="robot", **kwargs):
        """Build the URDF document from xacro includes.

        Parameters
        ----------
        includes : list
            A list of strings representing files to include in a new, otherwise
            empty, xacro file. Any string that can be used in a xacro include
            directive is valid, so look-ups like ``$(find package)`` are valid.
        name : str
            The name of the top-level robot tag.
        """
        s = _xacro_header(name)
        for incl in includes:
            s += _xacro_include(incl)
        s += "</robot>"
        return cls(s, **kwargs)

    def to_urdf_file(self, path, compare_existing=True, verbose=False):
        """Write the URDF to a file.

        Parameters
        ----------
        path : str or Path
            The path to the URDF file to be written.
        compare_existing : bool
            If ``True``, then if the file at ``path`` already exists, read it
            and only write back to it if the parsed URDF is different than the
            file content. This avoids some race conditions if the file is being
            compiled by multiple processes concurrently.
        verbose : bool
            Set to ``True`` to print information about xacro compilation,
            ``False`` otherwise.
        """
        s = self.to_urdf_string()

        # if the full path already exists, we can check if the contents are the
        # same to avoid writing it if it hasn't changed. This avoids some race
        # conditions if the file is being compiled by multiple processes
        # concurrently.
        if Path(path).exists() and compare_existing:
            with open(path) as f:
                s0 = f.read()
            if s0 == s:
                if verbose:
                    print("URDF files are the same - not writing.")
                return
            elif verbose:
                print("URDF files are not the same - writing.")

        with open(path, "w") as f:
            f.write(s)

    @contextmanager
    def temp_urdf_file_path(self, verbose=False):
        """Get the context of a temporary URDF file path.

        This is useful for temporarily writing the URDF to a file for
        consumption by other programs.

        Parameters
        ----------
        verbose : bool
            Set to ``True`` to print information about xacro compilation,
            ``False`` otherwise.

        Examples
        --------
        Use as a context manager:

        .. code-block:: python

           with doc.temp_urdf_file_path() as path:
               load_file_from_path(path)
        """
        fd, path = tempfile.mkstemp(suffix=".urdf")
        try:
            self.to_urdf_file(path, compare_existing=False, verbose=verbose)
            yield path
        finally:
            os.remove(path)

    def to_urdf_string(self, pretty=True):
        """Get the URDF as a string.

        Parameters
        ----------
        pretty : bool
            True to format the string for human readability, False otherwise.

        Returns
        -------
        : str
            The URDF represented as a string.
        """
        if pretty:
            return self.doc.toprettyxml(indent="  ")
        return self.doc.toxml()
