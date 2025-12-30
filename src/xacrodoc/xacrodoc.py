from contextlib import contextmanager
import os
from pathlib import Path
import re
import shutil
import tempfile
from xml.dom.minidom import parseString
import warnings

from . import packages
from .xacro import xacro
from .xacro.xacro import substitution_args
from .xacro.xacro.color import warning


# monkey patch to replace xacro's package finding infrastructure
# NOTE: we include a vendored version of xacro here to ensure we always have
# compatibility even if the user has a different version of xacro installed
substitution_args._eval_find = lambda pkg: packages.get_path(pkg)


def _xacro_include(path):
    return f'<xacro:include filename="{path}"/>'


def _xacro_header(name):
    return f"""<?xml version="1.0" encoding="utf-8"?>
    <robot name="{name}" xmlns:xacro="http://www.ros.org/wiki/xacro">
    """.strip()


def _compile_xacro_file(text, subargs=None, max_runs=10):
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
    : xml.dom.minidom.Document
        The URDF XML document.
    """
    if subargs is None:
        subargs = {}

    dom = xacro.parse(text)
    s1 = dom.toxml()

    # keep compiling until a fixed point is reached (i.e., the document doesn't
    # change anymore)
    run = 1
    while run < max_runs:
        xacro.process_doc(dom, mappings=subargs)  # modifies dom in place
        s2 = dom.toxml()
        if s1 == s2:
            break
        s1 = s2
        run += 1

    if run >= max_runs:
        raise ValueError("URDF file did not converge.")

    return dom


def _urdf_elements_with_filenames(dom):
    """Get all elements in the URDF document with a filename attribute.

    Parameters
    ----------
    dom : xml.dom.minidom.Document
        The XML document.

    Returns
    -------
    : list
        List of elements which have a filename attribute.
    """
    elements = dom.getElementsByTagName("mesh") + dom.getElementsByTagName(
        "material"
    )
    return [e for e in elements if e.hasAttribute("filename")]


def _resolve_packages(dom):
    """Convert all filenames specified with package:// to a full absolute path.

    Parameters
    ----------
    dom : xml.dom.minidom.Document
        The XML document, which is modified in place.
    """
    pkg_regex = re.compile(r"package://([ \w-]+)/")
    for e in _urdf_elements_with_filenames(dom):
        filename = e.getAttribute("filename")
        if filename.startswith("package://"):
            pkg = pkg_regex.search(filename).group(1)

            # ROS doesn't support spaces in package names, so neither do we;
            # explicitly check and tell the user about this
            if " " in pkg:
                raise ValueError(
                    f"Package name '{pkg}' contains spaces, which is not allowed."
                )
            abspath = Path(packages.get_path(pkg)).absolute().as_posix()
            filename = re.sub(f"package://{pkg}", f"file://{abspath}", filename)
            e.setAttribute("filename", filename)


def _set_mjcf_compile_options(dom, **kwargs):
    """Add or set compiler options in the mujoco extension.

    All ``kwargs`` are used as Mujoco compiler options; see
    https://mujoco.readthedocs.io/en/stable/modeling.html#curdf

    Parameters
    ----------
    dom : xml.dom.minidom.Document
        The XML document, which is modified in place.
    """
    mujoco_nodes = dom.getElementsByTagName("mujoco")
    if len(mujoco_nodes) > 1:
        raise ValueError("Multiple <mujoco> elements found.")
    if len(mujoco_nodes) == 0:
        mujoco_node = dom.createElement("mujoco")
        dom.documentElement.appendChild(mujoco_node)
    else:
        mujoco_node = mujoco_nodes[0]

    compiler_nodes = mujoco_node.getElementsByTagName("compiler")
    if len(compiler_nodes) > 1:
        raise ValueError("Multiple <compiler> elements found.")
    if len(compiler_nodes) == 0:
        compiler_node = dom.createElement("compiler")
        mujoco_node.appendChild(compiler_node)
    else:
        compiler_node = compiler_nodes[0]

    for k, v in kwargs.items():
        if type(v) != str:
            raise TypeError(
                f"MJCF compile option values must be strings, but got {v} which is of type {type(v)}."
            )
        compiler_node.setAttribute(str(k), v)


def _make_name_unique(name, existing_names):
    """Make a unique name for a file name.

    The name will have a number suffix incremented until it is unique.

    Parameters
    ----------
    name : str
        The file name to make unique.
    existing_names : set[str]
        The set of existing file names; name must be different than these.

    Returns
    -------
    : str
        The new unique name.
    """
    if name not in existing_names:
        return name

    stem, ext = os.path.splitext(name)
    count = 1
    while count <= 100:
        new_name = f"{stem}_{count:03}{ext}"
        if new_name not in existing_names:
            return new_name
        count += 1
    raise ValueError(f"Failed to generate unique name for {name}.")


def _split_path_protocol(path, delim="://"):
    """Split a path into its protocol prefix and the rest of the path.

    Parameters
    ----------
    path : str
        The path to split.
    delim : str
        The delimiter to split on.

    Returns
    -------
    : tuple
        A tuple of (protocol, path) where protocol is the protocol prefix
        including the delimiter, or an empty string if there is no protocol.
    """
    parts = path.split(delim, maxsplit=1)
    path = parts[-1]
    protocol = parts[0] + delim if len(parts) == 2 else ""
    return protocol, path


def _strip_path_protocol(path):
    """Remove the protocol prefix from a path, if there is one.

    Parameters
    ----------
    path : str
        The path to strip the protocol from.

    Returns
    -------
    : str
        The path without the protocol prefix.
    """
    return _split_path_protocol(path)[1]


def _copy_dom(dom):
    """Make a deep copy of a DOM tree.

    Parameters
    ----------
    dom : xml.dom.minidom.Document
        The XML document to copy.

    Returns
    -------
    : xml.dom.minidom.Document
        The copied XML document.
    """
    # NOTE: this is not quite as efficient as doing a deep clone of the node
    # and copying it into a new document, but it is very simple
    return parseString(dom.toxml())


def _copy_dom_change_paths(
    dom, file_protocols=True, paths_relative_to=None, rootdir=None
):
    """Make a deep copy of the DOM tree with modified asset paths.

    Parameters
    ----------
    dom : xml.dom.minidom.Document
        The XML document to copy.
    file_protocols : bool
        If ``True``, all asset filenames will be prefixed with ``file://``.
        Otherwise, no protocol prefix is used.
    paths_relative_to : str or Path or None
        If not ``None``, all asset filenames will be made relative to this
        path. Otherwise, paths are changed according to the value of
        ``rootdir`` (see below). Note that some applications may not support
        relative paths.
    rootdir : str or Path or None
        If ``paths_relative_to`` is ``None`` but ``rootdir`` is not, make all
        asset filenames absolute by resolving relative paths relative to
        ``rootdir``. If the filename is already absolute, it is left unchanged.

    Returns
    -------
    : xml.dom.minidom.Document
        The copied XML document with modified asset paths.
    """
    dom = _copy_dom(dom)
    for e in _urdf_elements_with_filenames(dom):
        path = e.getAttribute("filename")
        path = _strip_path_protocol(path)
        path = Path(path)

        if paths_relative_to is not None:
            start = Path(paths_relative_to)

            # we always want to be relative to a directory
            if start.is_file():
                start = start.parent
            path = os.path.relpath(path, start=start)
        elif rootdir is not None:
            # if the path is not absolute, resolve it relative to rootdir
            if not path.is_absolute():
                path = (Path(rootdir) / path).resolve()

        prefix = ""
        if file_protocols:
            prefix = "file://"

        e.setAttribute("filename", f"{prefix}{path}")
    return dom


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
    resolve_packages : bool
        If ``True``, resolve package protocol URIs in the compiled URDF.
        Otherwise, they are left unchanged.

    Attributes
    ----------
    dom :
        The underlying XML document.
    """

    def __init__(
        self,
        text,
        subargs=None,
        max_runs=10,
        resolve_packages=True,
    ):
        warnings.warn(
            "Calling XacroDoc's `__init__` directly is deprecated and its behaviour will change in xacrodoc version 2.0. Please use the `from_string` method instead.",
            DeprecationWarning,
        )
        self.dom = _compile_xacro_file(
            text=text,
            subargs=subargs,
            max_runs=max_runs,
        )
        if resolve_packages:
            _resolve_packages(self.dom)

    @property
    def doc(self):
        warnings.warn(
            "The attribute ``doc`` is deprecated and will be removed in xacrodoc version 2.0. Please use the attribute ``dom`` instead.",
            DeprecationWarning,
        )
        return self.dom

    @doc.setter
    def doc(self, value):
        warnings.warn(
            "The attribute ``doc`` is deprecated and will be removed in xacrodoc version 2.0. Please use the attribute ``dom`` instead.",
            DeprecationWarning,
        )
        self.dom = value

    @classmethod
    def from_string(
        cls,
        text,
        subargs=None,
        max_runs=10,
        resolve_packages=True,
        rootdir=None,
    ):
        dom = _compile_xacro_file(
            text=text,
            subargs=subargs,
            max_runs=max_runs,
        )
        if resolve_packages:
            _resolve_packages(dom)

        # TODO: until we change __init__
        obj = cls.__new__(cls)
        obj.dom = dom
        obj.rootdir = rootdir
        return obj

    @classmethod
    def from_file(cls, path, walk_up=True, **kwargs):
        """Load the URDF document from a xacro or plain URDF file.

        Parameters
        ----------
        path : str or Path
            The path to the xacro file.
        walk_up : bool
            If ``True``, look for packages by walking up the directory tree
            from ``path``.
        """
        if walk_up:
            packages.walk_up_from(path)

        with open(path) as f:
            text = f.read()
        rootdir = Path(path).parent
        return cls.from_string(text, rootdir=rootdir, **kwargs)

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
        path = packages.get_file_path(package_name, relative_path)
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
            The name attribute of the top-level robot tag.
        """
        s = _xacro_header(name)
        for incl in includes:
            s += _xacro_include(incl)
        s += "</robot>"
        return cls.from_string(s, **kwargs)

    def _elements_with_filenames(self):
        """Returns a list of all elements that have filename attributes."""
        return _urdf_elements_with_filenames(self.dom)

    def count_assets(self):
        """Count the number of unique asset files referenced in the document.

        Returns
        -------
        : int
            The number of unique asset files.
        """
        paths = set()
        for e in self._elements_with_filenames():
            path = e.getAttribute("filename")
            path = _strip_path_protocol(path)
            paths.add(path)
        return len(paths)

    def localize_assets(self, asset_dir, exist_ok=True):
        """Copy all assets to a local directory and update all filenames in the
        document accordingly.

        This is particularly useful when converting to MJCF format. The local
        assets are given unique names in the case of name collisions.

        Parameters
        ----------
        asset_dir : str or Path
            The path to the local directory where all the assets should be
            copied to.
        """
        basenames = set()
        path_map = {}

        # make the destination directory
        asset_dir = Path(asset_dir)
        asset_dir.mkdir(exist_ok=exist_ok)

        for e in self._elements_with_filenames():
            path = e.getAttribute("filename")
            protocol, path = _split_path_protocol(path)

            if path in path_map:
                basename = path_map[path]
            else:
                basename = _make_name_unique(Path(path).name, basenames)
                basenames.add(basename)
                path_map[path] = basename

            # point to the new path
            new_path = (asset_dir / basename).absolute().as_posix()
            e.setAttribute("filename", f"{protocol}{new_path}")

        # copy all the assets
        for abspath, name in path_map.items():
            shutil.copyfile(abspath, asset_dir / name)

    def _to_mjcf_spec(self, path, **kwargs):
        """Convert a Mujoco spec relative to ``path``.

        All ``kwargs`` are used as Mujoco compiler options; see
        https://mujoco.readthedocs.io/en/stable/modeling.html#curdf
        """
        import mujoco

        dom = _copy_dom_change_paths(
            self.dom, file_protocols=False, rootdir=self.rootdir
        )

        # set compile options
        _set_mjcf_compile_options(dom, **kwargs)

        # we need to create a temporary URDF file (rather than just work with
        # the XML string) because mujoco will use paths to assets relative to
        # the URDF file when strippath="false"
        # NOTE we use the .xml suffix rather than .urdf because mujoco may not
        # recognize the latter properly
        path = Path(path)
        with tempfile.NamedTemporaryFile(
            suffix=".xml", dir=path.parent, mode="w", delete=False
        ) as f:
            # write the URDF
            f.write(dom.toxml())
            f.close()

            # convert the URDF to MJCF
            urdf_path = (path.parent / f.name).as_posix()
            try:
                spec = mujoco.MjSpec.from_file(urdf_path)
            except TypeError:
                # Python 3.8
                spec = mujoco.MjSpec()
                spec.from_file(urdf_path)
        os.unlink(f.name)
        spec.compile()
        return spec

    def to_mjcf_file(self, path, **kwargs):
        """Convert and write to a Mujoco MJCF XML file.

        This requires the ``mujoco`` module to be installed and available for
        import.

        All ``kwargs`` are used as Mujoco compiler options; see
        https://mujoco.readthedocs.io/en/stable/modeling.html#curdf

        Parameters
        ----------
        path : str or Path
            The path to the MJCF XML file to be written.
        """
        path = Path(path)
        spec = self._to_mjcf_spec(path, **kwargs)
        try:
            spec.to_file(path.as_posix())
        except AttributeError:
            # Python 3.8
            with open(path, "w") as f:
                f.write(spec.to_xml())

    def to_mjcf_string(self, **kwargs):
        """Convert to a string in Mujoco MJCF XML format.

        This requires the ``mujoco`` module to be installed and available for
        import.

        All ``kwargs`` are used as Mujoco compiler options; see
        https://mujoco.readthedocs.io/en/stable/modeling.html#curdf

        Returns
        ----------
        : str
            The string of XML.
        """
        return self._to_mjcf_spec(".", **kwargs).to_xml()

    def to_urdf_file(
        self,
        path,
        compare_existing=True,
        file_protocols=True,
        relative_paths=False,
        verbose=False,
    ):
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
        file_protocols : bool
            If ``True``, all asset filenames will be prefixed with ``file://``.
            Otherwise, no protocol prefix is used.
        relative_paths : bool
            If ``True``, convert all asset filenames to be relative to the
            specified output ``path``. Otherwise, absolute paths are used. Note
            that some applications may not support relative paths.
        verbose : bool
            Set to ``True`` to print information about xacro compilation,
            ``False`` otherwise.
        """
        paths_relative_to = path if relative_paths else None
        s = self.to_urdf_string(
            file_protocols=file_protocols,
            paths_relative_to=paths_relative_to,
            pretty=True,
        )

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

    def to_temp_urdf_file(self, verbose=False):
        """Write the URDF to a temporary file.

        Clean-up is left to the user. If you want the tempfile to be
        automatically deleted, use the context manager ``temp_urdf_file_path``.

        Parameters
        ----------
        verbose : bool
            Set to ``True`` to print information about xacro compilation,
            ``False`` otherwise.

        Returns
        -------
        : str
            The path to the temporary URDF file.
        """
        _, path = tempfile.mkstemp(suffix=".urdf")
        self.to_urdf_file(path, compare_existing=False, verbose=verbose)
        return path

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
        _, path = tempfile.mkstemp(suffix=".urdf")
        try:
            self.to_urdf_file(path, compare_existing=False, verbose=verbose)
            yield path
        finally:
            os.remove(path)

    def to_urdf_string(
        self, file_protocols=True, paths_relative_to=None, pretty=True
    ):
        """Get the URDF as a string.

        Parameters
        ----------
        file_protocols : bool
            If ``True``, all asset filenames will be prefixed with ``file://``.
            Otherwise, no protocol prefix is used.
        file_protocols : bool
            If ``True``, all asset filenames will be prefixed with ``file://``.
            Otherwise, no protocol prefix is used.
        paths_relative_to : str or Path or None
            If not ``None``, all asset filenames will be made relative to this
            path. Otherwise, absolute paths are used. Note that some applications
            may not support relative paths.
        pretty : bool
            True to format the string for human readability, False otherwise.

        Returns
        -------
        : str
            The URDF represented as a string.
        """
        dom = _copy_dom_change_paths(
            self.dom,
            file_protocols=file_protocols,
            paths_relative_to=paths_relative_to,
            rootdir=self.rootdir,
        )
        if pretty:
            return dom.toprettyxml(indent="  ")
        return dom.toxml()
