#!/bin/sh
# compile xacro files into raw URDFs
# note that we run each command more than once to resolve nested macros

xacro threelink.urdf.xacro -o threelink.urdf
xacro tool.urdf.xacro -o tool.urdf
xacro combined.urdf.xacro -o combined.urdf
