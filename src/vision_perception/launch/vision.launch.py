"""Vision launch: default skeleton; optional v1_ros + local webcam/fake Image.

mode:=v1 remains unsupported (node rejects). ZED is not started here.
camera_contract for v1_ros is DEV_WEBCAM_ONLY / NOT_ZED.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    default_config = os.path.join(
        get_package_share_directory("vision_perception"), "config", "vision.yaml"
    )
    return LaunchDescription([
        DeclareLaunchArgument("params_file", default_value=default_config),
        DeclareLaunchArgument(
            "mode",
            default_value="skeleton",
            description="skeleton (default) or v1_ros. mode:=v1 is rejected.",
        ),
        DeclareLaunchArgument(
            "use_webcam",
            default_value="false",
            description="If true, also start vision_webcam_publisher (V4L2/OpenCV).",
        ),
        DeclareLaunchArgument(
            "use_fake_image",
            default_value="false",
            description="If true, publish synthetic/file RGB (no camera hardware).",
        ),
        DeclareLaunchArgument(
            "fake_image_path",
            default_value="",
            description=(
                "Optional local RGB file for fake publisher "
                "(.jpg/.png/.npy). Real bottle/cup photo recommended for "
                "non-empty detections."
            ),
        ),
        DeclareLaunchArgument("video_device", default_value="0"),
        DeclareLaunchArgument(
            "rgb_topic",
            default_value="/dg/vision/webcam/image_raw",
        ),
        DeclareLaunchArgument("model_path", default_value=""),
        DeclareLaunchArgument("model_manifest_path", default_value=""),
        DeclareLaunchArgument(
            "camera_contract",
            default_value="DEV_WEBCAM_ONLY / NOT_ZED",
        ),
        DeclareLaunchArgument(
            "publish_debug_image",
            default_value="false",
            description=(
                "If true, publish annotated rgb8 on /dg/vision/debug_image "
                "(≤2 Hz). Default off; no GUI."
            ),
        ),
        Node(
            package="vision_perception",
            executable="vision_webcam_publisher",
            name="vision_webcam_publisher",
            output="screen",
            condition=IfCondition(LaunchConfiguration("use_webcam")),
            parameters=[{
                "video_device": LaunchConfiguration("video_device"),
                "image_topic": LaunchConfiguration("rgb_topic"),
                "frame_id": "webcam_optical_frame",
            }],
        ),
        Node(
            package="vision_perception",
            executable="vision_fake_image_publisher",
            name="vision_fake_image_publisher",
            output="screen",
            condition=IfCondition(LaunchConfiguration("use_fake_image")),
            parameters=[{
                "image_topic": LaunchConfiguration("rgb_topic"),
                "frame_id": "fake_webcam_optical_frame",
                "image_path": LaunchConfiguration("fake_image_path"),
                "fake_image_path": LaunchConfiguration("fake_image_path"),
            }],
        ),
        Node(
            package="vision_perception",
            executable="vision_perception_node",
            name="vision_perception_node",
            output="screen",
            parameters=[
                LaunchConfiguration("params_file"),
                {
                    "mode": LaunchConfiguration("mode"),
                    "rgb_topic": LaunchConfiguration("rgb_topic"),
                    "model_path": LaunchConfiguration("model_path"),
                    "model_manifest_path": LaunchConfiguration("model_manifest_path"),
                    "camera_contract": LaunchConfiguration("camera_contract"),
                    "publish_debug_image": ParameterValue(
                        LaunchConfiguration("publish_debug_image"), value_type=bool
                    ),
                },
            ],
        ),
    ])
