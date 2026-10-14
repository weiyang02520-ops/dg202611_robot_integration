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

## Current executable behaviour

### ROS skeleton node (default)

`vision_perception_node` with `mode:=skeleton`:

- Publishes `/dg/vision/status` only (`SKELETON_ONLY`).
- No RGB/depth subscriptions, no inference, no detections/objects.
- `camera_contract=NOT_RUN`.
- Legacy `mode:=v1` is rejected with non-zero exit.

### V1 ROS path (`mode:=v1_ros`, explicit only)

When started with `mode:=v1_ros`, local ONNX model/manifest, and
`detector_enabled` (auto-enabled by the node for this mode):

- Subscribes to configurable `rgb_topic` (`sensor_msgs/Image`).
- Runs the same preprocess/ONNX/postprocess path as offline V1.
- Publishes `vision_perception_interfaces/VisionDetectionArray` on
  `/dg/vision/detections_2d`.
- Continues publishing `/dg/vision/status`.
- Does **not** publish `/dg/vision/objects`, depth pairing, tracking, TF, or cmd_vel.
- `camera_contract` must be `DEV_WEBCAM_ONLY` / `NOT_ZED` (not a ZED acceptance claim).

Optional helpers (only when launch flags enable them):

- `vision_webcam_publisher` — V4L2/OpenCV device → Image (`use_webcam:=true`).
- `vision_fake_image_publisher` — synthetic or `.npy` RGB (`use_fake_image:=true`).

Default launch remains skeleton: no camera node, no inference, no detections.

### V1 offline detection path

File CLI `vision_offline_detect` → JSON/CSV with `source_kind=OFFLINE_FILE`.
Model weights are not in git.

## Public contract (V4)

| Topic | Type | Stage |
|---|---|---|
| `/dg/vision/detections_2d` | `VisionDetectionArray` | V1 offline + v1_ros |
| `/dg/vision/objects` | `VisionObjectArray` | V2/V3 (not published) |
| `/dg/vision/status` | `DiagnosticArray` | scaffold onward |
| `/dg/vision/webcam/image_raw` | `sensor_msgs/Image` | optional DEV webcam / fake |

## Configuration

Installed config: `share/vision_perception/config/vision.yaml`.
Default `rgb_topic` for this stage is `/dg/vision/webcam/image_raw`.
Reserved ZED topic names remain documented for a later authorized stage and are
not the v1_ros camera contract.

## Verification

- Unit tests (no hardware): `PYTHONPATH=src/vision_perception python3 -m pytest src/vision_perception/test -q`
- Humble VM: colcon build; skeleton launch; `mode:=v1` reject; optional webcam/fake v1_ros.
- Cloud agent environment has no ROS/camera; do not treat cloud unit tests as camera PASS.

## Existing-module boundary

Does not edit MODEL-1/2/3, Nav2/AMCL/SLAM, EKF/TF, cmd_vel, chassis, existing
perception/interfaces, ZED sources, production launch or services.
