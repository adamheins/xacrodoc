# xacrodoc

xacrodoc is a tool for programmatically compiling
[xacro](https://github.com/ros/xacro)'d URDF files.

Why?

* Avoid the clutter of redundant compiled raw URDFs; only keep the xacro
  source files.
* Programmatically compose multiple xacro files and apply subtitution
  arguments to build a flexible URDF model.
* Convenient interfaces to provide URDF strings and URDF file paths as needed.
  For example, many libraries (such as
  [Pinocchio](https://github.com/stack-of-tasks/pinocchio)) accept a URDF
  string to build a model, but others (like [PyBullet](https://pybullet.org))
  only load URDFs directly from file paths.

See the documentation [here](https://xacrodoc.readthedocs.io/en/latest/).

## Installation

xacrodoc requires at least Python 3.8. Note that ROS *does not* need to be
installed on the system, but will also use its infrastructure to look for
packages if it is available.

From pip:
```
pip install xacrodoc
```

From source:
```
git clone https://github.com/adamheins/xacrodoc
cd xacrodoc
pip install .
```

## Usage

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
```

### Finding ROS packages

xacro files often make use of `$(find <pkg>)` directives to resolve paths
relative to a given ROS package.
If ROS is installed on the system, xacrodoc automatically looks for ROS
packages using the usual ROS infrastructure. If not, or if you are working
with packages outside of a ROS workspace, you'll need to tell xacrodoc where to
find packages. There are a few ways to do this:

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
# packages can located multiple levels deep from the specified directories,
# just like in a ROS workspace - the same package # search logic is used (since
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

We can also pass in substution arguments to xacro files. For example, suppose our
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

### Resolving filenames with respect to packages

Finally, one feature of URDF (not just xacro files) is that file names (e.g.,
for meshes) can be specified relative to a package by using
`package://<pkg>/relative/path/to/mesh` syntax, which depends on ROS and is not
supported by other non-ROS tools. xacrodoc automatically expands these
paths out to full absolute paths, but this can be disabled by passing
`resolve_packages=False` to the `Xacrodoc` constructor.

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

## License

[MIT](https://github.com/adamheins/xacrodoc/blob/main/LICENSE)
