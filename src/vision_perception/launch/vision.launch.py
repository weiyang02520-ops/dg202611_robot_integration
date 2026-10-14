"""Start only the inert vision shell; never include hardware or robot bringup.

Launch argument mode is forwarded to the node parameter. Non-skeleton values
must cause the node to reject startup with a non-zero exit (same as
`ros2 run ... --ros-args -p mode:=v1`).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    default_config = os.path.join(
        get_package_share_directory("vision_perception"), "config", "vision.yaml"
    )
    return LaunchDescription([
        DeclareLaunchArgument("params_file", default_value=default_config),
        DeclareLaunchArgument(
            "mode",
            default_value="skeleton",
            description=(
                "ROS node mode. Only 'skeleton' is supported; "
                "v1/offline/other values must fail startup."
            ),
        ),
        Node(
            package="vision_perception",
            executable="vision_perception_node",
            name="vision_perception_node",
            output="screen",
            parameters=[
                LaunchConfiguration("params_file"),
                # Override YAML so `mode:=v1` is not silently ignored.
                {"mode": LaunchConfiguration("mode")},
            ],
        ),
    ])
