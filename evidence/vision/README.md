# Vision Evidence Policy

Status: DEV webcam / fake-image ROS path may be exercised by the owner on
Ubuntu103; this tree does **not** claim ZED or production camera acceptance.

- Skeleton / no camera run: `camera_contract=NOT_RUN`
- Explicit `mode:=v1_ros` with local webcam or fake Image:
  `camera_contract=DEV_WEBCAM_ONLY / NOT_ZED`
- `ARM_READY=NO`
- `enable_objects` / `enable_tracking` remain **false** (V2/V3 not authorized)

## Canonical V1 templates (package-local)

Empty shells ship **inside** `vision_perception` so isolated two-package syncs
do not need this monorepo `evidence/` tree:

- Source: `src/vision_perception/evidence/templates/{V1_OFFLINE,V1_ROS}/`
- Install: `share/vision_perception/evidence/templates/…`

See `src/vision_perception/evidence/README.md`.

## Run directory layout

Filled runs use `evidence/vision/<date>_<stage>_<run>/` and must never overwrite
history. Stage tags: `V0_SHELL`, `V1_OFFLINE`, `V1_ROS`, `V2_POSITION`,
`V3_TRACKING`.

Each run must preserve at least `metadata.json`, `parameters.yaml`,
`source_hash.txt`, `manifest.sha256`, `acceptance_protocol.yaml`, `logs/`,
and raw `inputs/` or rosbag as applicable.

```bash
SHARE=$(ros2 pkg prefix vision_perception)/share/vision_perception/evidence/templates/V1_ROS
# or from source: SHARE=src/vision_perception/evidence/templates/V1_ROS
RUN=evidence/vision/$(date +%Y%m%d)_V1_ROS_smoke01
mkdir -p "$RUN/logs"
cp "$SHARE"/* "$RUN/"
```

Do not label DEV_WEBCAM evidence as ZED or METRIC_VALIDATED production acceptance.
Keep failed and incomplete runs. Model weights may be gitignored; record on-disk
path and SHA256.
