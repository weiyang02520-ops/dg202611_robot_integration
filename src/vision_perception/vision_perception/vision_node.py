"""ROS2 vision node: skeleton (default) or explicit v1_ros RGB detection.

skeleton: status only — no camera, no inference, no detections.
v1_ros: subscribe sensor_msgs/Image, run DetectionEngine, publish
        VisionDetectionArray on /dg/vision/detections_2d + status.
mode:=v1 (legacy) remains rejected. No depth/objects/cmd_vel/TF/ZED SDK.
camera_contract for v1_ros: DEV_WEBCAM_ONLY / NOT_ZED.
"""

from __future__ import annotations

import sys
from typing import Any, Optional

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Image

from vision_perception.config import (
    CAMERA_CONTRACT_NOT_RUN,
    normalize_ros_node_mode,
    vision_config_from_mapping,
)
from vision_perception.frame_worker import LatestFrameWorker
from vision_perception.message_mapping import try_build_vision_detection_array_msg
from vision_perception.pipeline import DetectionEngine
from vision_perception.ros_image_bridge import decode_sensor_image_msg
from vision_perception.runtime_deps import check_numpy_opencv_compat, check_v1_runtime_imports
from vision_perception.status_fields import compose_v1_ros_diagnostic


class VisionPerceptionNode(Node):
    """Skeleton status shell, or v1_ros Image→detections path when explicitly enabled."""

    def __init__(self):
        super().__init__("vision_perception_node")
        defaults = {
            "mode": "skeleton",
            "rgb_topic": "/dg/vision/webcam/image_raw",
            "depth_topic": "/zed/zed_node/depth/depth_registered",
            "camera_info_topic": "/zed/zed_node/rgb/color/rect/camera_info",
            "detections_topic": "/dg/vision/detections_2d",
            "objects_topic": "/dg/vision/objects",
            "status_topic": "/dg/vision/status",
            "target_classes": ["bottle", "cup"],
            "backend": "unconfigured",
            "model_path": "",
            "model_manifest_path": "",
            "detector_enabled": False,
            "tracking_enabled": False,
            "publish_debug_image": False,
            "output_frame_policy": "input_optical_header",
            "sync_tolerance_sec": 0.010,
            "min_depth_m": 0.5,
            "max_depth_m": 1.5,
            "inference_rate_hz": 5.0,
            "confidence_threshold": 0.35,
            "nms_iou_threshold": 0.45,
            "max_detections": 20,
            "ort_threads": 2,
            "model_input_size": 640,
            "status_rate_hz": 1.0,
            "video_device": 0,
            "image_frame_id": "webcam_optical_frame",
            "camera_contract": CAMERA_CONTRACT_NOT_RUN,
            "pending_frames": 1,
        }
        for name, default in defaults.items():
            self.declare_parameter(name, default)

        mode = normalize_ros_node_mode(self.get_parameter("mode").value)
        self._mode = mode
        self._engine: Optional[DetectionEngine] = None
        self._worker: Optional[LatestFrameWorker] = None
        self._detections_pub = None
        self._image_sub = None
        self._frames_received = 0
        self._last_observation_id = 0
        self._last_detection_count = 0
        self._implementation_status = "SKELETON_ONLY"
        self._camera_contract = CAMERA_CONTRACT_NOT_RUN
        self._inference_active = False
        self._camera_subscriptions_active = False

        status_topic = self.get_parameter("status_topic").value
        if not status_topic.startswith("/dg/vision/"):
            raise ValueError("status_topic must remain within /dg/vision/")
        self._status_publisher = self.create_publisher(DiagnosticArray, status_topic, 1)

        if mode == "skeleton":
            self._init_skeleton()
        else:
            self._init_v1_ros()

        rate_hz = float(self.get_parameter("status_rate_hz").value)
        if rate_hz <= 0:
            raise ValueError("status_rate_hz must be > 0")
        self._timer = self.create_timer(1.0 / rate_hz, self._publish_status)

    def _param_map(self) -> dict:
        names = [
            "mode",
            "backend",
            "model_path",
            "model_manifest_path",
            "detector_enabled",
            "tracking_enabled",
            "publish_debug_image",
            "status_topic",
            "detections_topic",
            "objects_topic",
            "rgb_topic",
            "depth_topic",
            "camera_info_topic",
            "target_classes",
            "inference_rate_hz",
            "pending_frames",
            "ort_threads",
            "model_input_size",
            "confidence_threshold",
            "nms_iou_threshold",
            "max_detections",
            "status_rate_hz",
            "output_frame_policy",
            "sync_tolerance_sec",
            "min_depth_m",
            "max_depth_m",
            "video_device",
            "image_frame_id",
            "camera_contract",
        ]
        return {name: self.get_parameter(name).value for name in names}

    def _init_skeleton(self) -> None:
        enabled = any(
            self.get_parameter(name).value
            for name in ("detector_enabled", "tracking_enabled", "publish_debug_image")
        )
        if enabled or self.get_parameter("backend").value != "unconfigured":
            raise ValueError(
                "Inference, tracking and debug rendering are not active in skeleton mode"
            )
        self._implementation_status = "SKELETON_ONLY"
        self._camera_contract = CAMERA_CONTRACT_NOT_RUN
        self.get_logger().warning(
            "SKELETON_ONLY: no camera subscriptions, inference, object output or control; "
            "use mode:=v1_ros for DEV webcam/Image detection"
        )

    def _init_v1_ros(self) -> None:
        # Fail fast on NumPy 2.x / missing ORT before opening cameras or models.
        check_numpy_opencv_compat()
        notes = check_v1_runtime_imports(require_opencv=False)
        for line in notes:
            self.get_logger().info(f"runtime_dep: {line}")

        raw = self._param_map()
        # Force documented contract label for this stage.
        if not str(raw.get("camera_contract", "")).strip() or str(
            raw.get("camera_contract")
        ) == CAMERA_CONTRACT_NOT_RUN:
            raw["camera_contract"] = "DEV_WEBCAM_ONLY / NOT_ZED"
        if not raw.get("detector_enabled"):
            raw["detector_enabled"] = True
        if raw.get("backend") in ("", "unconfigured"):
            raw["backend"] = "onnxruntime_cpu"
        cfg = vision_config_from_mapping(raw)

        try:
            from vision_perception_interfaces.msg import VisionDetectionArray
        except ImportError as exc:
            raise RuntimeError(
                "vision_perception_interfaces is required for v1_ros detections publish"
            ) from exc

        detections_topic = cfg.detections_topic
        self._detections_pub = self.create_publisher(
            VisionDetectionArray, detections_topic, 10
        )
        self._engine = DetectionEngine.from_config(cfg)
        min_interval = 1.0 / float(cfg.inference_rate_hz)
        self._worker = LatestFrameWorker(
            self._process_pending_frame,
            min_interval_sec=min_interval,
        )
        self._worker.start()
        self._image_sub = self.create_subscription(
            Image, cfg.rgb_topic, self._on_image, 10
        )
        self._implementation_status = "V1_ROS_DEV_WEBCAM"
        self._camera_contract = str(cfg.camera_contract)
        self._inference_active = True
        self._camera_subscriptions_active = True
        self.get_logger().warning(
            f"v1_ros DEV_WEBCAM_ONLY / NOT_ZED: subscribing {cfg.rgb_topic}, "
            f"publishing {detections_topic}; no depth/objects/cmd_vel/ZED SDK; "
            "empty detections=[] is healthy for blank fake frames"
        )

    def _on_image(self, msg: Image) -> None:
        self._frames_received += 1
        if self._worker is None:
            return
        # Decode off the worker to keep invalid encodings out of the queue early.
        try:
            decoded = decode_sensor_image_msg(msg)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"image decode failed: {exc}")
            return
        self._worker.submit(decoded)

    def _process_pending_frame(self, decoded: Any) -> None:
        if self._engine is None or self._detections_pub is None:
            return
        batch = self._engine.process_rgb_array(
            decoded.rgb,
            frame_id=decoded.header.frame_id,
            stamp_sec=decoded.header.stamp_sec,
            stamp_nanosec=decoded.header.stamp_nanosec,
            source_kind="LIVE_CAMERA",
        )
        self._last_observation_id = int(batch.key.observation_id)
        self._last_detection_count = len(batch.detections)
        message = try_build_vision_detection_array_msg(batch)
        self._detections_pub.publish(message)

    def _publish_status(self):
        message = DiagnosticArray()
        message.header.stamp = self.get_clock().now().to_msg()
        status = DiagnosticStatus()
        status.name = "dg/vision/node"
        if self._mode == "skeleton":
            status.level = DiagnosticStatus.WARN
            status.message = "SKELETON_ONLY"
            fields = {
                "mode": self._mode,
                "implementation_status": self._implementation_status,
                "camera_subscriptions_active": "false",
                "camera_contract": self._camera_contract,
                "inference_active": "false",
                "tracking_active": "false",
                "object_output_active": "false",
                "control_output_active": "false",
                "arm_ready": "NO",
                "v1_detections_interface": "VisionDetectionArray",
                "v2_objects_interface": "VisionObjectArray",
            }
        else:
            dropped = self._worker.dropped if self._worker is not None else 0
            processed = self._worker.processed if self._worker is not None else 0
            last_error = self._worker.last_error if self._worker is not None else ""
            level, msg, fields = compose_v1_ros_diagnostic(
                frames_received=self._frames_received,
                frames_processed=processed,
                frames_dropped=dropped,
                last_observation_id=self._last_observation_id,
                last_detection_count=self._last_detection_count,
                last_worker_error=last_error or "",
                camera_contract=self._camera_contract,
                rgb_topic=str(self.get_parameter("rgb_topic").value),
            )
            status.level = level
            status.message = msg
        status.values = [KeyValue(key=key, value=value) for key, value in fields.items()]
        message.status = [status]
        self._status_publisher.publish(message)

    def destroy_node(self):
        if self._worker is not None:
            self._worker.stop()
            self._worker = None
        super().destroy_node()


def main(args=None):
    """Run skeleton or v1_ros; unsupported configuration exits non-zero."""
    rclpy.init(args=args)
    node = None
    exit_code = 0
    try:
        node = VisionPerceptionNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except (ValueError, RuntimeError, FileNotFoundError, OSError) as exc:
        hint = ""
        text = str(exc)
        if "model_path" in text or "model manifest" in text or "model file" in text:
            hint = (
                " Hint: v1_ros needs absolute local paths "
                "model_path:=/ABS/yolo11n-seg.onnx "
                "model_manifest_path:=/ABS/model_manifest.json "
                "(no auto-download; weights are not in git). "
                "See share/vision_perception/examples/model_manifest.template.json"
            )
        print(f"[vision_perception_node] FATAL: {exc}{hint}", file=sys.stderr)
        exit_code = 1
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
