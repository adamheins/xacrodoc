# xacrodoc

xacrodoc is a tool for programmatically compiling xacro'd URDF files.

This can be used to e.g. put together multiple xacro files from include statements
This is convenient for putting together multiple 

## Installation

xacrodoc depends on `xacro` and `rospkg`, which should be available if ROS is
installed on your system and available on your `$PYTHONPATH`.

From pip
```
pip install xacrodoc
```

For a local installation:
```
git clone ...
cd ...
pip install .
```

## Usage

```python
from xacrodoc import XacroDoc

doc = XacroDoc.from_file("robot.urdf.xacro")

urdf_str = doc.to_urdf_string()
# do stuff with string of URDF...

with doc.temp_urdf_file_path() as path:
  # do stuff with URDF file located at `path`...
  # file is cleaned up once context manager is exited
```

## Licence

MIT
