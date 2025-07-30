xacrodoc
========

xacrodoc is a tool for compiling `xacro <https://github.com/ros/xacro>`_ files
to plain URDF files or Mujoco MJCF files from within Python code or via the
command line. It is fully functional whether ROS is installed on the system or
not.

xacrodoc requires at least Python 3.8. Note that ROS *does not* need to be
installed on the system, but xacrodoc will also use its infrastructure to look
for packages if it is available.

The library can be installed from pip:

.. code-block:: shell

  pip install xacrodoc

  # or to also include conversion to MJCF files:
  pip install "xacrodoc[mujoco]"

or from source:

.. code-block:: shell

  git clone --recurse-submodules https://github.com/adamheins/xacrodoc
  cd xacrodoc
  pip install .

It is recommended to install the command line tool into an isolated environment
using `uv <https://docs.astral.sh/uv/>`_:

.. code-block:: shell

  uv tool install xacrodoc

  # for conversion to MJCF files, use:
  uv tool install "xacrodoc[mujoco]"

or `pipx <https://pipx.pypa.io>`_:

.. code-block:: shell

  pipx install xacrodoc
  # or
  pipx install "xacrodoc[mujoco]"

Code and usage examples can be found `here
<https://github.com/adamheins/xacrodoc>`_, while the class and function
reference can be found below.

.. toctree::
   :maxdepth: 1
   :caption: Reference

   reference
