# Independent Manipulation Vision Module

Date: 2026-10-14. Implementation status: V1 offline-completable code on
`cursor/vision-v1-offline-1fcf` (PR #1). Default remains SKELETON; real-camera /
bottle-cup photo smoke is **NOT_RUN** until Ubuntu103 owner run.

## Purpose and placement

`src/vision_perception` is an independent hybrid ament_cmake + ament_cmake_python
package for bottle/cup detection, future depth-qualified positions and temporal
tracking. `src/vision_perception_interfaces` defines the arm-independent
observation contract per `VISION_INTEGRATION_PLAN.md` **V4**. No arm code is
present or required. Neither package depends on navigation/fusion/recovery
modules or the legacy inspection detector.

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
- Publishes `VisionDetectionArray` on `/dg/vision/detections_2d` + status
  (`source_session_id`, `backend`, STALE when input age &gt; `input_stale_sec`).
- Optional `publish_debug_image:=true` → `/dg/vision/debug_image` ≤2 Hz (default off).
- Does **not** publish `/dg/vision/objects`, depth, tracking, TF, or cmd_vel.
- Config gates `enable_objects` / `enable_tracking` default **false** (true rejected until authorized).
- `VisionObject*` message shapes are frozen in `vision_perception_interfaces` (types only).
- `orientation_valid` remains false in V2-shaped placeholders; `ARM_READY=NO`.

Optional launch helpers:

- `use_webcam:=true` → `vision_webcam_publisher` (V4L2/OpenCV, e.g. laptop camera).
- `use_fake_image:=true` + `fake_image_path:=/ABS/...` → file/synthetic RGB.
- `publish_debug_image:=true` → annotated overlay (no GUI).

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
Optional `--eval-annotations` / `--out-metrics` for plan §10.1 precision/recall.
Format sample: `examples/golden_format_batch.json` (not a real ONNX golden).

Isolated two-package sync: use
`bash src/vision_perception/scripts/bootstrap_isolated_ws.sh` (restores `+x`,
package-local LF attributes, pytest; optional `--build`).
V1 evidence shells live under `src/vision_perception/evidence/templates/`
(installed to share); pytest does not need the monorepo `evidence/` tree.

## Public contract (V4)

| Topic | Type | Stage |
|---|---|---|
| `/dg/vision/detections_2d` | `VisionDetectionArray` | V1 offline + v1_ros |
| `/dg/vision/objects` | `VisionObjectArray` | V2/V3 (not published) |
| `/dg/vision/status` | `DiagnosticArray` | scaffold onward |
| `/dg/vision/debug_image` | `sensor_msgs/Image` | V1 optional, default off |
| `/dg/vision/webcam/image_raw` | `sensor_msgs/Image` | optional DEV webcam / fake |

## 未做项（NOT_RUN）

- Real-time camera acceptance / bottle-cup photo non-empty detection smoke
- Navigation, chassis, `cmd_vel`, MODEL bringup
- ZED RGB-D contract and depth pairing (V2)
- `/objects`, tracking (V2/V3)
- True ONNX golden comparison against committed weights (weights stay out of git)

## Webcam / WSL / fake-image trial (shortest)

See `src/vision_perception/README.md` § Ubuntu103. Prefer Humble `ros2` over a
stale `~/.local/bin/ros2`. Do not combine `use_webcam` and `use_fake_image`.

### Runtime pins

`numpy>=1.26.4,<2`, `opencv-python-headless==4.10.0.84`, `onnxruntime==1.20.1`
(see `src/vision_perception/requirements-runtime.txt`). Install NumPy **before**
OpenCV; NumPy 2.x breaks cv2 (`_ARRAY_API`). Empty `detections=[]` on fake
frames keeps status OK (`V1_ROS_DEV_WEBCAM` / `empty_detections_healthy=true`).

## Packaging note

`vision_perception` uses **ament_cmake + ament_cmake_python** so
`ament_package()` emits `ament_prefix_path` hooks. After isolated colcon
install, `source install/setup.bash && ros2 pkg prefix vision_perception`
must work without hand-exporting `AMENT_PREFIX_PATH`. Regression script:
`src/vision_perception/scripts/check_ament_prefix_hook.sh`.
Scripts under `scripts/` are forced LF via `.gitattributes`.

## Verification

- Unit tests: `PYTHONPATH=src/vision_perception python3 -m pytest src/vision_perception/test -q`
- Ubuntu103 (owner): build OK, skeleton OK, `mode:=v1` reject, fake-image smoke with
  local ONNX + optional real bottle/cup JPG; watch NumPy&lt;2.
- Cloud agent: no ROS/camera PASS claims.

## Existing-module boundary

Does not edit MODEL-1/2/3, Nav2/AMCL/SLAM, EKF/TF, cmd_vel, chassis, existing
perception/interfaces, ZED sources, production launch or services.
