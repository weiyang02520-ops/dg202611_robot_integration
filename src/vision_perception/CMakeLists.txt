cmake_minimum_required(VERSION 3.8)
project(vision_perception)

# Hybrid ament_cmake + ament_cmake_python so `ament_package()` generates
# ament_prefix_path environment hooks. Pure setuptools ament_python installs on
# this workspace were left with package.dsv containing only pythonpath, which
# broke `ros2 pkg prefix` / launch after `source install/setup.bash`.

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Install Python modules + console_scripts from setup.py (no share/ data_files).
ament_python_install_package(${PROJECT_NAME})

install(DIRECTORY launch config examples
  DESTINATION share/${PROJECT_NAME}
)

install(FILES
  package.xml
  README.md
  requirements-runtime.txt
  DESTINATION share/${PROJECT_NAME}
)

# ament_package() registers the package index marker and writes
# share/${PROJECT_NAME}/hook/ament_prefix_path.{dsv,sh,ps1} plus package.dsv.
ament_package()
