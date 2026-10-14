"""Map pure DetectionBatch structures to serialisable dicts / optional ROS messages.

ROS message imports are optional so unit tests run without a Humble install.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from vision_perception.types import (
    POSITION_REFERENCE,
    Detection,
    DetectionBatch,
)


def detection_to_dict(detection: Detection) -> Dict[str, Any]:
    return {
        "detection_index": int(detection.detection_index),
        "class_name": detection.class_name,
        "confidence": float(detection.confidence),
        "bbox": {
            "center_x": float(detection.bbox.center_x),
            "center_y": float(detection.bbox.center_y),
            "size_x": float(detection.bbox.size_x),
            "size_y": float(detection.bbox.size_y),
            "theta": float(detection.bbox.theta),
        },
    }


def detection_batch_to_dict(batch: DetectionBatch) -> Dict[str, Any]:
    key = batch.key
    return {
        "header": {
            "frame_id": key.frame_id,
            "stamp": {
                "sec": int(key.source_stamp_sec),
                "nanosec": int(key.source_stamp_nanosec),
            },
        },
        "source_session_id": key.source_session_id,
        "observation_id": int(key.observation_id),
        "calibration_id": key.calibration_id,
        "source_kind": key.source_kind,
        "source_image_id": key.source_image_id,
        "image_width": int(batch.image_width),
        "image_height": int(batch.image_height),
        "detections": [detection_to_dict(item) for item in batch.detections],
    }


def nan_point_dict() -> Dict[str, float]:
    return {"x": float("nan"), "y": float("nan"), "z": float("nan")}


def nan_quaternion_dict() -> Dict[str, float]:
    return {"x": float("nan"), "y": float("nan"), "z": float("nan"), "w": float("nan")}


def placeholder_object_dict_from_detection(
    detection: Detection,
    *,
    frame_id: str = "",
    stamp_sec: int = 0,
    stamp_nanosec: int = 0,
    invalid_reason: str = "DEPTH_UNPAIRED",
) -> Dict[str, Any]:
    """V2-shaped object stub from a 2D detection. Not published in V1."""
    return {
        "header": {
            "frame_id": frame_id,
            "stamp": {"sec": stamp_sec, "nanosec": stamp_nanosec},
        },
        "detection_index": int(detection.detection_index),
        "object_id": "",
        "class_name": detection.class_name,
        "confidence": float(detection.confidence),
        "bbox": detection_to_dict(detection)["bbox"],
        "position": nan_point_dict(),
        "position_valid": False,
        "position_reference": POSITION_REFERENCE,
        "invalid_reason": invalid_reason,
        "reference_u": float("nan"),
        "reference_v": float("nan"),
        "valid_depth_fraction": 0.0,
        "orientation": nan_quaternion_dict(),
        "orientation_valid": False,
        "tracking_valid": False,
    }


def try_build_vision_detection_array_msg(batch: DetectionBatch):
    """Build vision_perception_interfaces/VisionDetectionArray when ROS msgs exist."""
    try:
        from vision_msgs.msg import BoundingBox2D, Pose2D
        from vision_perception_interfaces.msg import (
            VisionDetection2D,
            VisionDetectionArray,
        )
    except ImportError as exc:
        raise RuntimeError(
            "ROS message packages are unavailable in this environment"
        ) from exc

    message = VisionDetectionArray()
    message.header.frame_id = batch.key.frame_id
    message.header.stamp.sec = int(batch.key.source_stamp_sec)
    message.header.stamp.nanosec = int(batch.key.source_stamp_nanosec)
    message.source_session_id = batch.key.source_session_id
    message.observation_id = int(batch.key.observation_id)
    message.calibration_id = batch.key.calibration_id
    message.source_kind = batch.key.source_kind

    detections: List[Any] = []
    for item in batch.detections:
        det = VisionDetection2D()
        det.detection_index = int(item.detection_index)
        det.class_name = item.class_name
        det.confidence = float(item.confidence)
        bbox = BoundingBox2D()
        centre = Pose2D()
        centre.x = float(item.bbox.center_x)
        centre.y = float(item.bbox.center_y)
        centre.theta = float(item.bbox.theta)
        bbox.center = centre
        bbox.size_x = float(item.bbox.size_x)
        bbox.size_y = float(item.bbox.size_y)
        det.bbox = bbox
        detections.append(det)
    message.detections = detections
    return message


def is_nan_number(value: float) -> bool:
    return isinstance(value, float) and math.isnan(value)
