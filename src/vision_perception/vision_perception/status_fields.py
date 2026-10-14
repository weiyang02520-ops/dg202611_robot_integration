"""Diagnostic field helpers without rclpy (unit-testable).

Empty detections after a successful process are healthy for fake-image smoke:
status stays OK / V1_ROS_DEV_WEBCAM. Worker errors degrade; empty boxes do not.
No new input for longer than input_stale_sec → STALE (clears pending frames).

Humble diagnostic_msgs/DiagnosticStatus.level is a ``byte`` field: assignment
must be length-1 bytes (``b'\\x00'``), not a Python ``int``.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple, Union

# diagnostic_msgs/DiagnosticStatus level values as Humble expects (len==1 bytes)
LEVEL_OK = b"\x00"
LEVEL_WARN = b"\x01"
LEVEL_ERROR = b"\x02"
LEVEL_STALE = b"\x03"


def as_diagnostic_level_byte(level: Union[int, bytes, bytearray]) -> bytes:
    """Coerce a level to a length-1 bytes object for DiagnosticStatus.level."""
    if isinstance(level, (bytes, bytearray)):
        value = bytes(level)
        if len(value) != 1:
            raise ValueError(
                f"DiagnosticStatus.level must be length-1 bytes, got {value!r}"
            )
        return value
    if isinstance(level, int):
        if level < 0 or level > 255:
            raise ValueError(f"DiagnosticStatus.level int out of range: {level}")
        return bytes((level,))
    raise TypeError(
        f"DiagnosticStatus.level must be int or length-1 bytes, got {type(level)!r}"
    )


def is_input_stale(
    last_input_age_sec: Optional[float], input_stale_sec: float = 1.0
) -> bool:
    """True when age is known and exceeds the stale threshold."""
    if last_input_age_sec is None:
        return False
    return float(last_input_age_sec) > float(input_stale_sec)


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
    source_session_id: str = "",
    backend: str = "onnxruntime_cpu",
    source_kind: str = "LIVE_CAMERA",
    last_input_age_sec: Optional[float] = None,
    input_stale_sec: float = 1.0,
    publish_debug_image: bool = False,
    last_inference_ms: float = -1.0,
    calibration_id: str = "",
) -> Tuple[bytes, str, Dict[str, str]]:
    """Return (level_byte, message, key/value fields) for v1_ros status heartbeat."""
    error = (last_worker_error or "").strip()
    stale = is_input_stale(last_input_age_sec, input_stale_sec)

    if error:
        level = LEVEL_WARN
        message = "V1_ROS_DEGRADED"
    elif stale:
        level = LEVEL_STALE
        message = "STALE"
    else:
        level = LEVEL_OK
        message = "V1_ROS_DEV_WEBCAM"

    age_text = (
        f"{float(last_input_age_sec):.3f}" if last_input_age_sec is not None else ""
    )
    fields = {
        "mode": "v1_ros",
        "implementation_status": message,
        "camera_subscriptions_active": "true",
        "camera_contract": camera_contract,
        "backend": backend,
        "source_kind": source_kind,
        "source_session_id": source_session_id,
        "calibration_id": calibration_id,
        "inference_active": "true",
        "tracking_active": "false",
        "object_output_active": "false",
        "control_output_active": "false",
        "arm_ready": "NO",
        "publish_debug_image": "true" if publish_debug_image else "false",
        "v1_detections_interface": "VisionDetectionArray",
        "v2_objects_interface": "VisionObjectArray",
        "frames_received": str(int(frames_received)),
        "frames_processed": str(int(frames_processed)),
        "frames_dropped": str(int(frames_dropped)),
        "last_observation_id": str(int(last_observation_id)),
        "last_detection_count": str(int(last_detection_count)),
        "last_input_age_sec": age_text,
        "input_stale_sec": f"{float(input_stale_sec):.3f}",
        "last_inference_ms": (
            f"{float(last_inference_ms):.2f}" if last_inference_ms >= 0 else ""
        ),
        "empty_detections_healthy": "true",
        "last_worker_error": error,
        "rgb_topic": rgb_topic,
    }
    return as_diagnostic_level_byte(level), message, fields


def empty_detections_are_healthy(
    last_detection_count: int, last_worker_error: Optional[str] = None
) -> bool:
    """Fake solid-color frames often yield []; that must not mark the node unhealthy."""
    if (last_worker_error or "").strip():
        return False
    return int(last_detection_count) >= 0
