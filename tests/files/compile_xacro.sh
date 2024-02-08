#!/bin/sh
# regenerate the raw URDF files
# the grep pattern gets rid of the warning banner and trailing newline

xacro threelink.urdf.xacro | grep -v "^<!--.*-->\|^$" > threelink.urdf
xacro combined.urdf.xacro | grep -v "^<!--.*-->\|^$" > combined.urdf
xacro tool.urdf.xacro | grep -v "^<!--.*-->\|^$" > tool.urdf
xacro tool.urdf.xacro mass:=2 | grep -v "^<!--.*-->\|^$" > tool2.urdf
