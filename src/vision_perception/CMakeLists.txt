cmake_minimum_required(VERSION 3.8)
project(vision_perception)

# Hybrid ament_cmake + ament_cmake_python so `ament_package()` generates
# ament_prefix_path environment hooks. Pure setuptools ament_python installs on
# this workspace were left with package.dsv containing only pythonpath, which
# broke `ros2 pkg prefix` / launch after `source install/setup.bash`.
#
# Note: ament_python_install_package() generates its own setup.py without
# setuptools entry_points, so console scripts are installed explicitly below
# into lib/${PROJECT_NAME}/ (required by ros2 launch / libexec).

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

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

# ROS 2 libexec location for package executables.
install(PROGRAMS
  scripts/vision_perception_node
  scripts/vision_offline_detect
  scripts/vision_webcam_publisher
  scripts/vision_fake_image_publisher
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
