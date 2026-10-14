# vision_perception

Independent manipulation-vision ROS2 package (arm-independent).

## Current behaviour

| Path | Status |
|---|---|
| ROS `vision_perception_node` (mode=`skeleton`) | Publishes only `/dg/vision/status` (`SKELETON_ONLY`). No image subscriptions, no `/objects`, no control. |
| V1 offline CLI `vision_offline_detect` | File-based bottle/cup 2D detection when a **local** ONNX + `model_manifest.json` are supplied. No auto-download. |
| Live camera ROS detection (V1-C) | Not enabled. `camera_contract=NOT_RUN`. |
| V2 depth position / V3 tracking | Not implemented. `ARM_READY=NO`. |

Interface package `vision_perception_interfaces` (V4 contract):

- V1: `VisionDetection2D` / `VisionDetectionArray` on `/dg/vision/detections_2d` (ROS publish path not enabled in skeleton).
- V2/V3: extended `VisionObject` / `VisionObjectArray` on `/dg/vision/objects` (not published yet).

Design and acceptance criteria:

- `../../docs/dg202611/VISION_INTEGRATION_PLAN.md` (V4)
- `../../docs/dg202611/VISION_MODULE.md`
- `../../evidence/vision/README.md`

## Linux ROS2 build / skeleton run (owner Humble VM)

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select vision_perception_interfaces vision_perception
source install/setup.bash
ros2 interface show vision_perception_interfaces/msg/VisionDetectionArray
ros2 launch vision_perception vision.launch.py
# Rejection checks (must fail startup with non-zero exit; must NOT stay in SKELETON_ONLY):
ros2 launch vision_perception vision.launch.py mode:=v1
ros2 run vision_perception vision_perception_node --ros-args -p mode:=v1
```

## Offline unit tests (no ROS / no camera)

```bash
PYTHONPATH=src/vision_perception python3 -m pytest src/vision_perception/test -q
```

## Offline detection CLI (requires local model; not committed)

```bash
# After colcon build + source install/setup.bash on Humble:
ros2 run vision_perception vision_offline_detect -- \
  --images /path/to/img.npy \
  --model /path/to/yolo11n-seg.onnx \
  --manifest /path/to/model_manifest.json \
  --out-json /tmp/v1_offline.json \
  --out-csv /tmp/detections.csv
```

Manifest shape example: `config/model_manifest.example.json`. Model weights (`.onnx`/`.pt`) are gitignored and must not be committed.

No TensorRT/CUDA, ZED SDK, arm, cmd_vel or production bringup dependency is required by the skeleton or the offline unit tests.
