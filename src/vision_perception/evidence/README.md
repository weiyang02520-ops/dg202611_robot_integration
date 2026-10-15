# Vision evidence templates (package-local)

Canonical empty shells for isolated workspaces that only sync
`vision_perception` + `vision_perception_interfaces`.

| Path | Stage |
|---|---|
| `templates/V1_OFFLINE/` | Offline 2D CLI |
| `templates/V1_ROS/` | `mode:=v1_ros` fake/webcam |
| `templates/V2_POSITION/` | Offline objects / fake-depth smoke (`enable_objects`) |

Installed to: `share/vision_perception/evidence/templates/…`

```bash
# From source tree (isolated ws):
SHARE_SRC=src/vision_perception/evidence/templates/V2_POSITION
# After colcon install:
SHARE=$(ros2 pkg prefix vision_perception)/share/vision_perception/evidence/templates/V2_POSITION

RUN=evidence/vision/$(date +%Y%m%d)_V2_POSITION_smoke01
mkdir -p "$RUN/logs"
cp "$SHARE"/* "$RUN/"
# rename *.template → final names, fill fields, attach logs
```

Filled run directories still belong under the workspace/repo
`evidence/vision/<date>_<stage>_<run>/` (never overwrite history).
`ARM_READY=NO`. Synthetic / fake depth must keep `v2_accuracy=BLOCKED`.
Do not claim ZED acceptance from these shells.
