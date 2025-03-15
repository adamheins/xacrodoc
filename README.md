# xacrodoc

xacrodoc is a tool for programmatically compiling
[xacro](https://github.com/ros/xacro) files to plain URDF files or Mujoco MJCF
files. It is fully functional whether ROS is installed on the system or not.

Why?

* Compile xacro files without a ROS installation.
* Convert xacro files to Mujoco MJCF files.
* Avoid the clutter of redundant compiled raw URDFs; only keep the xacro
  source files.
* Programmatically compose multiple xacro files and apply substitution
  arguments to build a flexible URDF model directly in your code.
* Convenient interfaces to provide URDF strings and (temporary) URDF file paths
  as needed. For example, many libraries (such as
  [Pinocchio](https://github.com/stack-of-tasks/pinocchio)) accept a URDF
  string to build a model, but others (like [PyBullet](https://pybullet.org))
  only load URDFs directly from file paths.

See the documentation [here](https://xacrodoc.readthedocs.io/en/latest/).

## Installation

xacrodoc requires at least Python 3.8. Note that ROS *does not* need to be
installed on the system, but xacrodoc will also use its infrastructure to look
for packages if it is available.

From pip:
```sh
pip install xacrodoc
```

From source:
```sh
git clone https://github.com/adamheins/xacrodoc
cd xacrodoc
pip install .
```

## Python Usage

### Basic

A basic use-case of compiling a URDF from a xacro file:

```python
from xacrodoc import XacroDoc

doc = XacroDoc.from_file("robot.urdf.xacro")

# or relative to a ROS package
# e.g., for a file located at some_ros_package/urdf/robot.urdf.xacro:
doc = XacroDoc.from_package_file("some_ros_package", "urdf/robot.urdf.xacro")

# convert to a string of URDF
urdf_str = doc.to_urdf_string()

# or write to a file
doc.to_urdf_file("robot.urdf")

# or just work with a temp file
# this is useful for working with libraries that expect a URDF *file* (rather
# than a string)
with doc.temp_urdf_file_path() as path:
  # do stuff with URDF file located at `path`...
  # file is cleaned up once context manager is exited

# you can also manage the temp file yourself if you don't want to clean it up
# right away
path = doc.to_temp_urdf_file()
# ...do stuff with path...
# ...manually delete the temp file
```

### Finding ROS packages

xacro files often make use of `$(find <pkg>)` directives to resolve paths
relative to a given ROS package. If ROS is installed on the system, xacrodoc
automatically looks for ROS packages using the usual ROS infrastructure. If
not, or if you are working with packages outside of a ROS workspace, you'll
need to tell xacrodoc where to find packages. There are a few ways to do this:

```python
import xacrodoc as xd

# `from_file` automatically resolves packages by looking in each parent
# directory of the given path to check for required ROS packages (as marked by
# a package.xml file)
doc = xd.XacroDoc.from_file("robot.urdf.xacro")

# if you want to disable this, pass `walk_up=False`:
doc = xd.XacroDoc.from_file("robot.urdf.xacro", walk_up=False)

# we can also tell xacrodoc to walk up a directory tree manually
xd.packages.walk_up_from("some/other/path")

# or we can give paths to directories to search for packages
# packages can be located multiple levels deep from the specified directories,
# just like in a ROS workspace - the same package search logic is used (since
# we actually use rospkg under the hood)
xd.packages.look_in(["somewhere/I/keep/packages", "another/directory/with/packages"])
```

### Multiple URDFs

We can also build a URDF programmatically from multiple xacro files:

```python
import xacrodoc as xd

# setup where to look for packages, if needed; for example:
xd.packages.look_in(["somewhere/I/keep/packages"])

# specify files to compose (using xacro include directives)
includes = ["robot_base.urdf.xacro", "robot_arm.urdf.xacro", "tool.urdf.xacro"]
doc = xd.XacroDoc.from_includes(includes)

# includes can also use $(find ...) directives:
includes = [
    "$(find my_ros_package)/urdf/robot_base.urdf.xacro",
    "$(find another_ros_package)/urdf/"robot_arm.urdf.xacro",
    "tool.urdf.xacro"
]
doc = xd.XacroDoc.from_includes(includes)
```

### Substitution arguments

We can also pass in substitution arguments to xacro files. For example, suppose our
file `robot.urdf.xacro` contains the directive `<xacro:arg name="mass" default="1"/>`.
On the command line, we could write
```
xacro robot_base.urdf.xacro -o robot_base.urdf mass:=2
```
to set the mass value. Programmatically, we do
```python
from xacrodoc import XacroDoc

doc = XacroDoc.from_file("robot.urdf.xacro", subargs={"mass": "2"})
```

### Resolving file names with respect to packages

Finally, one feature of URDF (not just xacro files) is that file names (e.g.,
for meshes) can be specified relative to a package by using
```
package://<pkg>/relative/path/to/mesh
```
syntax, which depends on ROS and is not supported by other non-ROS tools.
xacrodoc automatically expands these paths out to full absolute paths, e.g.,
```
file:///abs/path/to/mesh
```
but this can be disabled by passing `resolve_packages=False` to the `XacroDoc`
constructor. Note that the `file://` protocol prefix can be removed by passing
`remove_protocols=True` to the `XacroDoc` constructor, which is useful when
converting to MJCF.

### Conversion to MJCF format

Mujoco has basic support for URDFs, but natively uses its own MJCF XML format.
If you want to use Mujoco, you probably want to convert any xacro file you have
to MJCF. xacrodoc provides basic functionality to do this, by ensuring Mujoco
resolves paths properly. Note that `mujoco` must be installed and importable
for this to work. For example:
```python
from xacrodoc import XacroDoc

# remove file protocols and add the Mujoco extension so that Mujoco resolves
# file paths properly
doc = XacroDoc.from_file("input.urdf.xacro", remove_protocols=True)
doc.add_mujoco_extension()
doc.to_mjcf_file("output.xml")
```
MJCF conversion is also available in the command line tool (see below).

## Command Line Usage

In addition to the Python API described above, this packages also includes a
`xacrodoc` command line tool. It is similar to `xacro`, except that directories
in which to search for packages can be provided manually. Examples:
```sh
# compile and print to stdout
xacrodoc input.urdf.xacro

# compile and output to provided output file
xacrodoc input.urdf.xacro -o output.urdf

# provide directories in which to look for packages referenced in input.urdf.xacro
xacrodoc input.urdf.xacro -d ~/my_pkg_dir ~/my_other_pkg_dir

# substitution arguments use := notation, like xacro
xacrodoc input.urdf.xacro mass:=1

# convert to MJCF (requires Mujoco)
xacrodoc input.urdf.xacro --mjcf -o output.xml
```

It is recommended to install the command line tool using [uv](https://docs.astral.sh/uv/):
```
uv tool install xacrodoc
```
or [pipx](https://pipx.pypa.io):
```
pipx install xacrodoc
```

## Testing

Tests use `pytest`. Some tests depend on additional submodules, which you can
clone using:
```
git submodule update --init --recursive
```
Then do:
```
cd tests
pytest .
```
To test the Mujoco MJCF features, you'll also need `mujoco` installed.

## License

[MIT](https://github.com/adamheins/xacrodoc/blob/main/LICENSE)
