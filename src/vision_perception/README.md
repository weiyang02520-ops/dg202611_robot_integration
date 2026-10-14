# vision_perception

Independent manipulation-vision ROS2 package (arm-independent).

## Current behaviour

| Path | Status |
|---|---|
| ROS `mode:=skeleton` (default) | `/dg/vision/status` only (`SKELETON_ONLY`). No image sub, no inference, no detections. |
| ROS `mode:=v1_ros` (explicit) | Subscribe `sensor_msgs/Image` on configurable `rgb_topic`, run ONNX bottle/cup detector, publish `VisionDetectionArray` on `/dg/vision/detections_2d` + status. |
| Optional `vision_webcam_publisher` | V4L2/OpenCV → Image. Started only with `use_webcam:=true`. |
| Optional `vision_fake_image_publisher` | Synthetic/file RGB for no-camera smoke tests (`use_fake_image:=true`). |
| Offline CLI `vision_offline_detect` | File → JSON/CSV. No ROS camera claim. |
| Legacy `mode:=v1` | **Rejected** (non-zero exit). |
| ZED / production camera contract | **Not authorized here.** `camera_contract=DEV_WEBCAM_ONLY / NOT_ZED` for v1_ros. |
| V2 depth / V3 tracking / arm | Not implemented. `ARM_READY=NO`. |

## Build (Humble)

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select vision_perception_interfaces vision_perception
source install/setup.bash
```

## Skeleton (default — safe)

```bash
ros2 launch vision_perception vision.launch.py
# Must still reject:
ros2 launch vision_perception vision.launch.py mode:=v1
ros2 run vision_perception vision_perception_node --ros-args -p mode:=v1
```

## V1 ROS + front webcam (DEV_WEBCAM_ONLY / NOT_ZED)

Requires a **local** ONNX + `model_manifest.json` (not in git). Example:

```bash
# List devices (on the Humble machine)
ls -l /dev/video*

# Front webcam index is often 0; adjust video_device if needed.
ros2 launch vision_perception vision.launch.py \
  mode:=v1_ros \
  use_webcam:=true \
  video_device:=0 \
  rgb_topic:=/dg/vision/webcam/image_raw \
  model_path:=/ABS/PATH/yolo11n-seg.onnx \
  model_manifest_path:=/ABS/PATH/model_manifest.json \
  camera_contract:="DEV_WEBCAM_ONLY / NOT_ZED"
```

Watch topics:

```bash
ros2 topic echo /dg/vision/status --once
ros2 topic echo /dg/vision/detections_2d --once
ros2 topic hz /dg/vision/detections_2d
```

### No webcam on Ubuntu103 — fake Image or external topic

```bash
# Synthetic RGB (no /dev/video required)
ros2 launch vision_perception vision.launch.py \
  mode:=v1_ros \
  use_fake_image:=true \
  rgb_topic:=/dg/vision/webcam/image_raw \
  model_path:=/ABS/PATH/yolo11n-seg.onnx \
  model_manifest_path:=/ABS/PATH/model_manifest.json

# Or publish your own Image (usb_cam / v4l2_camera / rosbag) and point rgb_topic at it:
ros2 launch vision_perception vision.launch.py \
  mode:=v1_ros \
  use_webcam:=false \
  rgb_topic:=/camera/image_raw \
  model_path:=/ABS/PATH/yolo11n-seg.onnx \
  model_manifest_path:=/ABS/PATH/model_manifest.json
```

Do **not** set `use_webcam:=true` and `use_fake_image:=true` together.

## Unit tests (no ROS / no camera)

```bash
PYTHONPATH=src/vision_perception python3 -m pytest src/vision_perception/test -q
```

## Offline file CLI

```bash
ros2 run vision_perception vision_offline_detect -- \
  --images /path/to/img.npy \
  --model /path/to/yolo11n-seg.onnx \
  --manifest /path/to/model_manifest.json \
  --out-json /tmp/v1_offline.json \
  --out-csv /tmp/detections.csv
```

Manifest example: `config/model_manifest.example.json`. Weights are gitignored.

## Boundaries

No MODEL-1/2/3, Nav2/AMCL/SLAM, EKF/TF, cmd_vel, chassis, production bringup, `ylhb_*`, or ZED SDK changes. This package does not publish `/dg/vision/objects` in v1_ros.
