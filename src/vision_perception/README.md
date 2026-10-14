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

**Hard rules:** the node never auto-downloads weights; `.onnx` / `.pt` must stay out of git (see root `.gitignore`). License of upstream YOLO/COCO weights is separate from this repo — review before use; do not publish or redistribute weights until cleared.

## Build (Humble)

`vision_perception` is **ament_cmake + ament_cmake_python** (not pure
`ament_python`) so `ament_package()` writes `ament_prefix_path` hooks into
`package.dsv`. Pure setuptools installs on Ubuntu103 left only `pythonpath`
hooks, which broke `ros2 pkg prefix` after `source install/setup.bash`.

```bash
source /opt/ros/humble/setup.bash
# Clean rebuild required after packaging-type change:
rm -rf build/vision_perception install/vision_perception
colcon build --symlink-install --packages-select vision_perception_interfaces vision_perception
source install/setup.bash

# Must work WITHOUT manually exporting AMENT_PREFIX_PATH:
ros2 pkg list | grep vision_perception
ros2 pkg prefix vision_perception
grep ament_prefix_path "$(ros2 pkg prefix vision_perception)/share/vision_perception/package.dsv"
bash src/vision_perception/scripts/check_ament_prefix_hook.sh
ros2 launch vision_perception vision.launch.py --show-args
```

## Runtime Python pins (NumPy &lt; 2 — required)

`v1_ros` / webcam / offline need:

| Package | Pin |
|---|---|
| NumPy | `>=1.26.4,<2` |
| OpenCV | `opencv-python-headless==4.10.0.84` (full `opencv-python` also OK if same major) |
| ONNX Runtime | `onnxruntime==1.20.1` (CPU) |

**Install order matters.** NumPy 2.x breaks many OpenCV wheels (`_ARRAY_API not found` / `numpy.core.multiarray failed to import`). Observed on Ubuntu103 when NumPy 2 was present with an older cv2.

```bash
# Preferred one-shot (after workspace source, from repo or install share):
python3 -m pip install --user -r src/vision_perception/requirements-runtime.txt
# same file also installed as:
#   share/vision_perception/requirements-runtime.txt

# Or strictly in this order:
python3 -m pip install --user 'numpy>=1.26.4,<2'
python3 -m pip install --user 'opencv-python-headless==4.10.0.84'
python3 -m pip install --user 'onnxruntime==1.20.1'

# Verify (must show numpy 1.x)
python3 -c "import numpy,cv2,onnxruntime as o; print(numpy.__version__, cv2.__version__, o.__version__)"
```

Do **not** `pip install -U numpy` afterward. `setup.py` / `runtime_deps.py` encode the same pins; `mode:=v1_ros` refuses to start on NumPy ≥ 2.

## Local ONNX + manifest (required for v1_ros / offline)

Pipeline expects **YOLO11n-seg** COCO layout (V4 plan):

| Item | Required value |
|---|---|
| Input name | `images` |
| Input shape | `[1, 3, 640, 640]` FP32, values in `[0,1]` after `/255` |
| `output0` | `[1, 116, 8400]` = 4 xywh + 80 class scores + 32 mask coeffs |
| `output1` | `[1, 32, 160, 160]` mask prototypes (V1 publishes boxes only) |
| Classes used | COCO `bottle=39`, `cup=41` only |
| Export | FP32, imgsz=640, batch=1, `dynamic=false`, `simplify=false`, opset=17, **NMS not embedded** |

### Manifest template (JSON only, no weights in repo)

- Source template: `examples/model_manifest.template.json` (also installed under `share/vision_perception/examples/`)
- Copy beside your local ONNX, fill hashes/license:

```bash
# Example local layout (outside git / gitignored)
mkdir -p "$HOME/vision_models"
cp src/vision_perception/examples/model_manifest.template.json \
  "$HOME/vision_models/model_manifest.json"
# After export:
#   $HOME/vision_models/yolo11n-seg.onnx
#   edit model_manifest.json → onnx_sha256 / weights_sha256 / license
sha256sum "$HOME/vision_models/yolo11n-seg.onnx"
```

Required JSON fields: `source`, `onnx_sha256`, `license`, `input_name`, `input_shape`,
`output0_shape`, `output1_shape`, `class_map` (`bottle`→39, `cup`→41). Optional:
`weights_sha256`, `export_tool_versions`.

### How to obtain / export (isolated env — do not touch robot global Python)

Plan baseline: Ultralytics **8.3.0**, PyTorch **2.4.1**, torchvision **0.19.1**, ONNX **1.16.2**, Python 3.10 venv. Export is a **manual owner step**; this package will not download.

```bash
# On Ubuntu or WSL2 — separate venv (example only; pin versions you review)
python3.10 -m venv "$HOME/yolo11_export_venv"
source "$HOME/yolo11_export_venv/bin/activate"
pip install 'ultralytics==8.3.0' 'torch==2.4.1' 'torchvision==0.19.1' 'onnx==1.16.2'

# Ultralytics may fetch pretrained weights into its cache when you first load the name.
# That is outside this ROS package. Review upstream license before use.
python - <<'PY'
from ultralytics import YOLO
model = YOLO("yolo11n-seg.pt")  # local path preferred if you already have the file
model.export(
    format="onnx",
    imgsz=640,
    batch=1,
    dynamic=False,
    simplify=False,
    opset=17,
)
print("Move the produced .onnx next to your filled model_manifest.json")
PY
deactivate

# Deploy runtime (Humble side) needs onnxruntime CPU, e.g.:
#   pip install --user 'onnxruntime==1.20.1'   # or apt/wheel policy you choose
# Inference process must NOT import ultralytics/torch.
```

After export, verify ONNX I/O names/shapes match the table, fill `onnx_sha256`, set `license` only after review.

## Skeleton (default — safe)

```bash
ros2 launch vision_perception vision.launch.py
# Must still reject:
ros2 launch vision_perception vision.launch.py mode:=v1
ros2 run vision_perception vision_perception_node --ros-args -p mode:=v1
```

## Shortest webcam trial (Ubuntu / WSL2 + `/dev/video*`)

WSL2 needs USB camera attached to WSL (`usbipd` on Windows) so that `ls /dev/video*` works inside the Linux distro that runs Humble. Native Ubuntu: built-in laptop camera is usually `/dev/video0` (index `0`).

### Expected FATAL without model (by design)

```bash
ros2 launch vision_perception vision.launch.py mode:=v1_ros use_webcam:=true
# → non-zero exit, stderr like:
# [vision_perception_node] FATAL: v1_ros mode requires model_path
#   Hint: v1_ros needs absolute local paths model_path:=... model_manifest_path:=...
```

Same if `model_path` is set but the file/manifest is missing or SHA256 mismatches.

### With local model + front camera

```bash
ls -l /dev/video*          # must exist for use_webcam:=true
source /opt/ros/humble/setup.bash
source install/setup.bash  # your colcon workspace

ros2 launch vision_perception vision.launch.py \
  mode:=v1_ros \
  use_webcam:=true \
  video_device:=0 \
  rgb_topic:=/dg/vision/webcam/image_raw \
  model_path:=$HOME/vision_models/yolo11n-seg.onnx \
  model_manifest_path:=$HOME/vision_models/model_manifest.json \
  camera_contract:="DEV_WEBCAM_ONLY / NOT_ZED"
```

Watch:

```bash
ros2 topic echo /dg/vision/status --once
ros2 topic echo /dg/vision/detections_2d --once
ros2 topic hz /dg/vision/detections_2d
```

If `use_webcam:=true` but no device: webcam publisher FATALS with “Failed to open V4L2/OpenCV device”.

### No `/dev/video` (e.g. Ubuntu103) — fake Image smoke

Owner-verified path (models under `/home/weiyang/vision_models/`):

```bash
ros2 launch vision_perception vision.launch.py \
  mode:=v1_ros \
  use_fake_image:=true \
  rgb_topic:=/dg/vision/webcam/image_raw \
  model_path:=$HOME/vision_models/yolo11n-seg.onnx \
  model_manifest_path:=$HOME/vision_models/model_manifest.json \
  camera_contract:="DEV_WEBCAM_ONLY / NOT_ZED"
```

Expect:

- `/dg/vision/status` → `message=V1_ROS_DEV_WEBCAM`, level OK; fields include `empty_detections_healthy=true`
- `/dg/vision/detections_2d` ~ few Hz; solid-color fake frames often have `detections=[]` — **that is healthy**, not a fault
- Do **not** combine `use_webcam:=true` and `use_fake_image:=true`

## Unit tests (no ROS / no camera)

```bash
PYTHONPATH=src/vision_perception python3 -m pytest src/vision_perception/test -q
```

## Offline file CLI

```bash
ros2 run vision_perception vision_offline_detect -- \
  --images /path/to/img.npy \
  --model $HOME/vision_models/yolo11n-seg.onnx \
  --manifest $HOME/vision_models/model_manifest.json \
  --out-json /tmp/v1_offline.json \
  --out-csv /tmp/detections.csv
```

## Boundaries

No MODEL-1/2/3, Nav2/AMCL/SLAM, EKF/TF, cmd_vel, chassis, production bringup, `ylhb_*`, or ZED SDK changes. This package does not publish `/dg/vision/objects` in v1_ros.
