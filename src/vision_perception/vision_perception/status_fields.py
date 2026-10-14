"""Diagnostic field helpers without rclpy (unit-testable).

Empty detections after a successful process are healthy for fake-image smoke:
status stays OK / V1_ROS_DEV_WEBCAM. Worker errors degrade; empty boxes do not.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

# diagnostic_msgs/DiagnosticStatus level values
LEVEL_OK = 0
LEVEL_WARN = 1
LEVEL_ERROR = 2


def compose_v1_ros_diagnostic(
    *,
    frames_received: int,
    frames_processed: int,
    frames_dropped: int,
    last_observation_id: int,
    last_detection_count: int,
    last_worker_error: str = "",
    camera_contract: str = "DEV_WEBCAM_ONLY / NOT_ZED",
    rgb_topic: str = "/dg/vision/webcam/image_raw",
) -> Tuple[int, str, Dict[str, str]]:
    """Return (level, message, key/value fields) for v1_ros status heartbeat."""
    error = (last_worker_error or "").strip()
    if error:
        level = LEVEL_WARN
        message = "V1_ROS_DEGRADED"
    else:
        level = LEVEL_OK
        message = "V1_ROS_DEV_WEBCAM"

    fields = {
        "mode": "v1_ros",
        "implementation_status": "V1_ROS_DEV_WEBCAM",
        "camera_subscriptions_active": "true",
        "camera_contract": camera_contract,
        "inference_active": "true",
        "tracking_active": "false",
        "object_output_active": "false",
        "control_output_active": "false",
        "arm_ready": "NO",
        "v1_detections_interface": "VisionDetectionArray",
        "v2_objects_interface": "VisionObjectArray",
        "frames_received": str(int(frames_received)),
        "frames_processed": str(int(frames_processed)),
        "frames_dropped": str(int(frames_dropped)),
        "last_observation_id": str(int(last_observation_id)),
        "last_detection_count": str(int(last_detection_count)),
        "empty_detections_healthy": "true",
        "last_worker_error": error,
        "rgb_topic": rgb_topic,
    }
    return level, message, fields


def empty_detections_are_healthy(
    last_detection_count: int, last_worker_error: Optional[str] = None
) -> bool:
    """Fake solid-color frames often yield []; that must not mark the node unhealthy."""
    if (last_worker_error or "").strip():
        return False
    return int(last_detection_count) >= 0
