# xacrodoc

xacrodoc is a tool for programmatically compiling xacro'd URDF files.

Why?
This can be used to e.g. put together multiple xacro files from include statements
This is convenient for putting together multiple 

## Installation

xacrodoc requires ROS to be installed on your system.

From pip:
```
pip install xacrodoc
```

For a source installation, install into a catkin workspace:
```
cd catkin_ws/src
git clone ...
catkin build
```

## Usage

A basic use-case of compiling a URDF from a xacro file:

```python
from xacrodoc import XacroDoc

doc = XacroDoc.from_file("robot.urdf.xacro")

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

## Licence

MIT
