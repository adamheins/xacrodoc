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

xacrodoc requires ROS to be installed on your system with Python 3.

From pip:
```
pip install xacrodoc
```

For a source installation, build in a catkin workspace:
```
cd catkin_ws/src
git clone https://github.com/adamheins/xacrodoc
catkin build
```

## Usage

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

We can also build a URDF programmatically from multiple xacro files:

```python
from xacrodoc import XacroDoc

# specify files to compose (using xacro include directives)
includes = ["robot_base.urdf.xacro", "robot_arm.urdf.xacro", "tool.urdf.xacro"]
doc = XacroDoc.from_includes(includes)

# includes can also use $(find ...) directives:
includes = [
    "$(find my_ros_package)/urdf/robot_base.urdf.xacro",
    "$(find another_ros_package)/urdf/"robot_arm.urdf.xacro",
    "tool.urdf.xacro"
]
doc = XacroDoc.from_includes(includes)
```

Finally, we can also pass in substution arguments. For example, suppose our
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

## Development

Tests use `pytest`. Ensure that the catkin workspace's setup file has been
sourced to make the package available, then do:
```
cd tests
pytest .
```

For local testing, the project needs to be built as a ROS package in a catkin
workspace, which uses the `setup.py` file. For building and publishing to
PyPI, we use `poetry` and the configuration in `pyproject.toml`.

## License

[MIT](https://github.com/adamheins/xacrodoc/blob/main/LICENSE)
