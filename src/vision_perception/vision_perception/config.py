"""Startup-only configuration helpers for the vision module.

Values mirror VISION_INTEGRATION_PLAN.md V4 defaults. Invalid config fails
loudly; nothing is silently corrected at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

from vision_perception.types import ALLOWED_CLASSES, ModelManifest


@dataclass(frozen=True)
class VisionConfig:
    mode: str = "skeleton"
    backend: str = "unconfigured"
    model_path: str = ""
    model_manifest_path: str = ""
    detector_enabled: bool = False
    tracking_enabled: bool = False
    publish_debug_image: bool = False
    status_topic: str = "/dg/vision/status"
    detections_topic: str = "/dg/vision/detections_2d"
    objects_topic: str = "/dg/vision/objects"
    rgb_topic: str = "/zed/zed_node/rgb/color/rect/image"
    depth_topic: str = "/zed/zed_node/depth/depth_registered"
    camera_info_topic: str = "/zed/zed_node/rgb/color/rect/camera_info"
    target_classes: Tuple[str, ...] = ALLOWED_CLASSES
    inference_rate_hz: float = 5.0
    pending_frames: int = 1
    ort_threads: int = 2
    model_input_size: int = 640
    confidence_threshold: float = 0.35
    nms_iou_threshold: float = 0.45
    max_detections: int = 20
    mask_threshold: float = 0.5
    status_rate_hz: float = 1.0
    output_frame_policy: str = "input_optical_header"
    sync_tolerance_sec: float = 0.010
    min_depth_m: float = 0.5
    max_depth_m: float = 1.5


DEFAULTS = VisionConfig()

# ROS vision_perception_node allows only skeleton. Offline detection is CLI-only.
ROS_NODE_ALLOWED_MODES = frozenset({"skeleton"})


def require_ros_skeleton_mode(mode: Any) -> str:
    """Reject any non-skeleton mode for the ROS node (non-zero startup failure).

    Offline file detection must use vision_offline_detect, not mode:=offline/v1.
    """
    normalized = str(mode).strip()
    if normalized not in ROS_NODE_ALLOWED_MODES:
        raise ValueError(
            f"Unsupported ROS mode={normalized!r}; only mode='skeleton' is allowed. "
            "Use vision_offline_detect for V1 file-based offline detection (no camera)."
        )
    return normalized


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _as_tuple_str(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ALLOWED_CLASSES
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
        return tuple(parts) if parts else ALLOWED_CLASSES
    return tuple(str(item) for item in value)


def vision_config_from_mapping(raw: Mapping[str, Any] | None = None) -> VisionConfig:
    data: Dict[str, Any] = {} if raw is None else dict(raw)
    cfg = VisionConfig(
        mode=str(data.get("mode", DEFAULTS.mode)),
        backend=str(data.get("backend", DEFAULTS.backend)),
        model_path=str(data.get("model_path", DEFAULTS.model_path)),
        model_manifest_path=str(data.get("model_manifest_path", DEFAULTS.model_manifest_path)),
        detector_enabled=_as_bool(data.get("detector_enabled", DEFAULTS.detector_enabled)),
        tracking_enabled=_as_bool(data.get("tracking_enabled", DEFAULTS.tracking_enabled)),
        publish_debug_image=_as_bool(
            data.get("publish_debug_image", DEFAULTS.publish_debug_image)
        ),
        status_topic=str(data.get("status_topic", DEFAULTS.status_topic)),
        detections_topic=str(data.get("detections_topic", DEFAULTS.detections_topic)),
        objects_topic=str(data.get("objects_topic", DEFAULTS.objects_topic)),
        rgb_topic=str(data.get("rgb_topic", DEFAULTS.rgb_topic)),
        depth_topic=str(data.get("depth_topic", DEFAULTS.depth_topic)),
        camera_info_topic=str(data.get("camera_info_topic", DEFAULTS.camera_info_topic)),
        target_classes=_as_tuple_str(data.get("target_classes", DEFAULTS.target_classes)),
        inference_rate_hz=float(data.get("inference_rate_hz", DEFAULTS.inference_rate_hz)),
        pending_frames=int(data.get("pending_frames", DEFAULTS.pending_frames)),
        ort_threads=int(data.get("ort_threads", DEFAULTS.ort_threads)),
        model_input_size=int(data.get("model_input_size", DEFAULTS.model_input_size)),
        confidence_threshold=float(
            data.get("confidence_threshold", DEFAULTS.confidence_threshold)
        ),
        nms_iou_threshold=float(data.get("nms_iou_threshold", DEFAULTS.nms_iou_threshold)),
        max_detections=int(data.get("max_detections", DEFAULTS.max_detections)),
        mask_threshold=float(data.get("mask_threshold", DEFAULTS.mask_threshold)),
        status_rate_hz=float(data.get("status_rate_hz", DEFAULTS.status_rate_hz)),
        output_frame_policy=str(
            data.get("output_frame_policy", DEFAULTS.output_frame_policy)
        ),
        sync_tolerance_sec=float(
            data.get("sync_tolerance_sec", DEFAULTS.sync_tolerance_sec)
        ),
        min_depth_m=float(data.get("min_depth_m", DEFAULTS.min_depth_m)),
        max_depth_m=float(data.get("max_depth_m", DEFAULTS.max_depth_m)),
    )
    validate_vision_config(cfg)
    return cfg


def validate_vision_config(cfg: VisionConfig) -> None:
    if cfg.mode not in {"skeleton", "offline"}:
        raise ValueError(
            f"Unsupported mode={cfg.mode!r}; allowed modes are 'skeleton' and 'offline'"
        )
    if not cfg.status_topic.startswith("/dg/vision/"):
        raise ValueError("status_topic must remain within /dg/vision/")
    if not cfg.detections_topic.startswith("/dg/vision/"):
        raise ValueError("detections_topic must remain within /dg/vision/")
    if not cfg.objects_topic.startswith("/dg/vision/"):
        raise ValueError("objects_topic must remain within /dg/vision/")
    if cfg.inference_rate_hz <= 0:
        raise ValueError("inference_rate_hz must be > 0")
    if cfg.pending_frames != 1:
        raise ValueError("pending_frames must be 1 in V1")
    if cfg.ort_threads < 1:
        raise ValueError("ort_threads must be >= 1")
    if cfg.model_input_size != 640:
        raise ValueError("model_input_size must be 640 in V1")
    if not (0.0 < cfg.confidence_threshold <= 1.0):
        raise ValueError("confidence_threshold must be in (0, 1]")
    if not (0.0 < cfg.nms_iou_threshold <= 1.0):
        raise ValueError("nms_iou_threshold must be in (0, 1]")
    if cfg.max_detections < 1 or cfg.max_detections > 20:
        raise ValueError("max_detections must be in [1, 20]")
    for name in cfg.target_classes:
        if name not in ALLOWED_CLASSES:
            raise ValueError(f"target_classes contains unsupported class {name!r}")
    if cfg.min_depth_m <= 0 or cfg.max_depth_m <= cfg.min_depth_m:
        raise ValueError("depth range must satisfy 0 < min_depth_m < max_depth_m")
    if cfg.mode == "skeleton":
        if cfg.detector_enabled or cfg.tracking_enabled or cfg.publish_debug_image:
            raise ValueError("skeleton mode forbids enabling detector/tracker/debug")
        if cfg.backend != "unconfigured":
            raise ValueError("skeleton mode requires backend=unconfigured")
    if cfg.mode == "offline":
        if cfg.backend != "onnxruntime_cpu":
            raise ValueError("offline mode requires backend=onnxruntime_cpu")
        if not cfg.model_path:
            raise ValueError("offline mode requires model_path")
        if not cfg.model_manifest_path:
            raise ValueError("offline mode requires model_manifest_path")
        if cfg.tracking_enabled:
            raise ValueError("V1 offline path does not enable tracking")


def load_model_manifest(path: str) -> ModelManifest:
    """Load and validate model_manifest.json. Does not fetch weights."""
    import json
    from pathlib import Path

    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"model manifest not found: {manifest_path}")
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = (
        "source",
        "onnx_sha256",
        "license",
        "input_name",
        "input_shape",
        "output0_shape",
        "output1_shape",
        "class_map",
    )
    missing = [key for key in required if key not in raw]
    if missing:
        raise ValueError(f"model manifest missing keys: {missing}")
    class_map = {str(k): int(v) for k, v in dict(raw["class_map"]).items()}
    for name in ALLOWED_CLASSES:
        if name not in class_map:
            raise ValueError(f"model manifest class_map missing required class {name!r}")
    # Standard COCO ids are the baseline contract.
    if class_map["bottle"] != 39 or class_map["cup"] != 41:
        raise ValueError(
            "class_map must use COCO ids bottle=39 and cup=41 unless explicitly re-authorized"
        )
    return ModelManifest(
        source=str(raw["source"]),
        onnx_sha256=str(raw["onnx_sha256"]).lower(),
        license=str(raw["license"]),
        input_name=str(raw["input_name"]),
        input_shape=tuple(int(x) for x in raw["input_shape"]),
        output0_shape=tuple(int(x) for x in raw["output0_shape"]),
        output1_shape=tuple(int(x) for x in raw["output1_shape"]),
        class_map=class_map,
        weights_sha256=str(raw.get("weights_sha256", "")).lower(),
        export_tool_versions=dict(raw["export_tool_versions"])
        if raw.get("export_tool_versions")
        else None,
    )


def verify_file_sha256(path: str, expected: str) -> str:
    import hashlib
    from pathlib import Path

    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"model file not found: {file_path}")
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest().lower()
    if expected and actual != expected.lower():
        raise ValueError(
            f"ONNX SHA256 mismatch for {file_path}: expected {expected}, got {actual}"
        )
    return actual


def validate_manifest_shapes(manifest: ModelManifest) -> None:
    if tuple(manifest.input_shape) != (1, 3, 640, 640):
        raise ValueError(f"unexpected input_shape={manifest.input_shape}")
    if tuple(manifest.output0_shape) != (1, 116, 8400):
        raise ValueError(
            f"unexpected output0_shape={manifest.output0_shape}; expected (1, 116, 8400)"
        )
    if tuple(manifest.output1_shape) != (1, 32, 160, 160):
        raise ValueError(
            f"unexpected output1_shape={manifest.output1_shape}; expected (1, 32, 160, 160)"
        )
    if manifest.input_name != "images":
        raise ValueError(f"unexpected input_name={manifest.input_name!r}; expected 'images'")
