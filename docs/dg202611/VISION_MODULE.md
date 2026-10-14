# Independent Manipulation Vision Module

Date: 2026-10-14. Implementation status: V1_OFFLINE + V1_ROS_DEV_WEBCAM (optional) + SKELETON default.

## Purpose and placement

`src/vision_perception` is an independent `ament_python` package for bottle/cup
detection, future depth-qualified positions and temporal tracking.
`src/vision_perception_interfaces` defines the arm-independent observation
contract per `VISION_INTEGRATION_PLAN.md` **V4**. No arm code is present or
required. Neither package depends on navigation/fusion/recovery modules or the
legacy inspection detector.

`ARM_READY=NO`. ZED production camera contract is **not** claimed in this stage.
`camera_contract` for explicit `mode:=v1_ros`: **`DEV_WEBCAM_ONLY / NOT_ZED`**.

## Current executable behaviour

### ROS skeleton node (default)

`vision_perception_node` with `mode:=skeleton`:

- Publishes `/dg/vision/status` only (`SKELETON_ONLY`).
- No RGB/depth subscriptions, no inference, no detections/objects.
- `camera_contract=NOT_RUN`.
- Legacy `mode:=v1` is rejected with non-zero exit.

### V1 ROS path (`mode:=v1_ros`, explicit only)

Requires **local** ONNX + filled `model_manifest.json` (absolute paths). The node
does **not** auto-download models and weights must not be committed.

- Subscribes to configurable `rgb_topic` (`sensor_msgs/Image`).
- Runs YOLO11n-seg-compatible preprocess/ONNX/postprocess (boxes for bottle/cup).
- Publishes `VisionDetectionArray` on `/dg/vision/detections_2d` + status.
- Does **not** publish `/dg/vision/objects`, depth, tracking, TF, or cmd_vel.

Optional launch helpers:

- `use_webcam:=true` → `vision_webcam_publisher` (V4L2/OpenCV, e.g. laptop camera).
- `use_fake_image:=true` → synthetic RGB when `/dev/video*` is missing.

### Model contract (owner-prepared artifacts)

See package `README.md` and `examples/model_manifest.template.json`.

| Field / layout | Value |
|---|---|
| Model | YOLO11n-seg COCO, export FP32 640 batch=1 opset=17, NMS not in graph |
| `input_name` / shape | `images` / `[1,3,640,640]` |
| `output0` / `output1` | `[1,116,8400]` / `[1,32,160,160]` |
| `class_map` | `bottle=39`, `cup=41` |
| Manifest | `source`, `onnx_sha256`, `license`, shapes, `class_map` (required) |

**License:** upstream Ultralytics/COCO weight terms are separate from this repository.
Do not redistribute weights until license review is complete. Suggested local paths:

```text
$HOME/vision_models/yolo11n-seg.onnx
$HOME/vision_models/model_manifest.json   # copied from examples/ template
```

Missing `model_path` / manifest on `mode:=v1_ros` → FATAL non-zero exit (by design).

### V1 offline detection path

File CLI `vision_offline_detect` → JSON/CSV with `source_kind=OFFLINE_FILE`.

## Public contract (V4)

| Topic | Type | Stage |
|---|---|---|
| `/dg/vision/detections_2d` | `VisionDetectionArray` | V1 offline + v1_ros |
| `/dg/vision/objects` | `VisionObjectArray` | V2/V3 (not published) |
| `/dg/vision/status` | `DiagnosticArray` | scaffold onward |
| `/dg/vision/webcam/image_raw` | `sensor_msgs/Image` | optional DEV webcam / fake |

## Webcam / WSL trial (shortest)

Ubuntu or WSL2 (camera visible as `/dev/video*`):

```bash
ros2 launch vision_perception vision.launch.py \
  mode:=v1_ros use_webcam:=true video_device:=0 \
  model_path:=$HOME/vision_models/yolo11n-seg.onnx \
  model_manifest_path:=$HOME/vision_models/model_manifest.json \
  camera_contract:="DEV_WEBCAM_ONLY / NOT_ZED"
```

Without model paths → expect FATAL mentioning `model_path` / manifest hint.
Without `/dev/video*` → use `use_fake_image:=true` instead of webcam.

## Verification

- Unit tests: `PYTHONPATH=src/vision_perception python3 -m pytest src/vision_perception/test -q`
- Ubuntu103 (owner): build OK, skeleton OK, `mode:=v1` reject, fake path FATAL without model, 36 passed, no `/dev/video` at last check.
- Cloud agent: no ROS/camera PASS claims.

## Existing-module boundary

Does not edit MODEL-1/2/3, Nav2/AMCL/SLAM, EKF/TF, cmd_vel, chassis, existing
perception/interfaces, ZED sources, production launch or services.
