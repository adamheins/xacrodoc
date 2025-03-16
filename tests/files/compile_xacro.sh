#!/bin/sh
# regenerate the raw URDF files
# the grep pattern gets rid of the warning banner and trailing newline

xacro xacro/threelink.urdf.xacro | grep -v "^<!--.*-->\|^$" > urdf/threelink.urdf
xacro xacro/combined.urdf.xacro | grep -v "^<!--.*-->\|^$" > urdf/combined.urdf
xacro xacro/tool.urdf.xacro | grep -v "^<!--.*-->\|^$" > urdf/tool.urdf
xacro xacro/tool.urdf.xacro mass:=2 | grep -v "^<!--.*-->\|^$" > urdf/tool2.urdf
