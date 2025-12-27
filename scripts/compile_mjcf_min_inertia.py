"""Example showing how to compile a xacro file to MJCF while ensuring diagonal
values of link inertias are above a minimum threshold.

Mujoco requires strictly positive inertia eigenvalues.
"""
import sys
from xacrodoc import XacroDoc

# pass the input xacro file as the first command line argument
doc = XacroDoc.from_file(sys.argv[1])

# ensure all diagonal inertia components are at or above a minimum value
# (mujoco requires strictly positive inertia eigenvalues)
min_inertia = "1e-6"
for e in doc.dom.getElementsByTagName("inertia"):
    for attr in ["ixx", "iyy", "izz"]:
        inertia = float(e.getAttribute(attr))
        if inertia < float(min_inertia):
            e.setAttribute(attr, min_inertia)

# move all asset files to a local "assets" directory
doc.localize_assets("assets")
doc.to_mjcf_file("output.xml", strippath="true", meshdir="assets")
