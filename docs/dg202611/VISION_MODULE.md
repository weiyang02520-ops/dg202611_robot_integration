# Independent Manipulation Vision Module

Date: 2026-10-14. Implementation status: V1_OFFLINE_CODE + SKELETON_ROS (camera/ROS detection not enabled).

## Purpose and placement

`src/vision_perception` is an independent `ament_python` package for bottle/cup
detection, future depth-qualified positions and temporal tracking.
`src/vision_perception_interfaces` defines the arm-independent observation
contract per `VISION_INTEGRATION_PLAN.md` **V4**. No arm code is present or
required. Neither package depends on navigation/fusion/recovery modules or the
legacy inspection detector.

Source review considers V1–V3 conditionally feasible for observations; no live
camera, Jetson performance or arm-grasp acceptance has passed.
`camera_contract=NOT_RUN`, `ARM_READY=NO`.

## Current executable behaviour

### ROS skeleton node

`vision_perception_node` (default `mode:=skeleton`) declares interface parameters
and publishes a diagnostic heartbeat on `/dg/vision/status` with `SKELETON_ONLY`.

- No RGB/depth subscriptions or image processing.
- No model loading, inference, GPU access or tracking in this node.
- No detection/object publisher, including empty arrays.
- No camera startup, TF publication, arm action or robot control.
- Non-skeleton modes (including `mode:=v1`) are rejected at ROS node startup.
  Offline file detection uses the separate CLI, not this node.

### V1 offline detection path

Pure-algorithm modules (no `rclpy` in the algorithm layer):

- `types` / `config` — observation keys, Detection, manifest validation
- `image_io` — colour decode + letterbox (NumPy; optional OpenCV for files)
- `onnx_backend` — local ONNX Runtime CPU only; hash + layout checks; no download
- `postprocess` — YOLO11-seg box decode, bottle/cup filter, per-class NMS
- `message_mapping` / `pipeline` / `offline_cli` — file → JSON/CSV evaluation

Offline results use `source_kind=OFFLINE_FILE` and `source_image_id`. They are
**not** claimed to be `LIVE_CAMERA` ROS observations. Model weights are not in
git (see `.gitignore`).

## Public contract (V4)

| Topic | Type | Stage |
|---|---|---|
| `/dg/vision/detections_2d` | `vision_perception_interfaces/VisionDetectionArray` | V1 (interface ready; ROS publish not enabled in skeleton) |
| `/dg/vision/objects` | `vision_perception_interfaces/VisionObjectArray` | V2/V3 (fields finalized; not published) |
| `/dg/vision/status` | `diagnostic_msgs/DiagnosticArray` | scaffold onward |
| `/dg/vision/debug_image` | `sensor_msgs/Image` | optional later; default off |

`VisionDetection2D` carries `detection_index`, `class_name`, `confidence`,
`vision_msgs/BoundingBox2D` (no unestimated 6D pose). Batches carry
`source_session_id`, `observation_id`, `calibration_id`, `source_kind`.

`VisionObject` extends the draft with `detection_index`, `bbox`,
`invalid_reason`, `reference_u/v`, `valid_depth_fraction`, and keeps explicit
`position_valid` / `orientation_valid` / `tracking_valid`. Invalid positions and
unknown orientations use NaN storage values with validity flags false.
`position_reference` is `visible_surface_sample` when a surface sample is
intended; failures are encoded only in `invalid_reason`.

A perception observation is not an arm grasp command. `position_valid=true`
(future) is not motion authorization.

## Configuration

Installed config: `share/vision_perception/config/vision.yaml`.
V4 defaults include `confidence_threshold=0.35`, `nms_iou_threshold=0.45`,
`max_detections=20`, `sync_tolerance_sec=0.010`, depth work range `0.5–1.5 m`.
Skeleton mode does not process depth or activate inference.

Manifest example: `share/vision_perception/config/model_manifest.example.json`
(COCO `bottle=39`, `cup=41`; expected ONNX layout `images` →
`output0=[1,116,8400]`, `output1=[1,32,160,160]`).

## Planned milestones

- V1: annotated bottle/cup 2D detection — **offline path implemented in code**;
  ROS live/replay camera adapter and metric acceptance still pending.
- V2: synchronized RGB/depth/calibration, valid metric 3D surface positions.
- V3: stable track IDs with reset session, occlusion policy and stale-track expiry.

## Verification

- Unit tests (no ROS hardware): `PYTHONPATH=src/vision_perception python3 -m pytest src/vision_perception/test -q`
- Owner Humble VM: colcon build of the two packages + skeleton launch + interface show.
- This cloud environment has **no ROS 2 Humble**; colcon/ROS launch and camera runs
  were **not** executed here. Do not treat cloud unit tests as camera PASS.

Evidence root: `evidence/vision/` (policy + future run directories). Stage tags:
`V0_SHELL`, `V1_OFFLINE`, `V1_ROS`, `V2_POSITION`, `V3_TRACKING`.

## Existing-module boundary

This addition does not edit MODEL-1/2/3, Nav2/AMCL/SLAM, EKF/TF, cmd_vel or
chassis control, existing perception/interfaces, ZED sources, deployment scripts
or services. It does not install robot-wide dependencies or alter global machine
configuration.
