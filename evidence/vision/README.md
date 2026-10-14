# Vision Evidence Policy

Status: DEV webcam / fake-image ROS path may be exercised by the owner on
Ubuntu103; this tree does **not** claim ZED or production camera acceptance.

- Skeleton / no camera run: `camera_contract=NOT_RUN`
- Explicit `mode:=v1_ros` with local webcam or fake Image:
  `camera_contract=DEV_WEBCAM_ONLY / NOT_ZED`
- `ARM_READY=NO`
- `enable_objects` / `enable_tracking` remain **false** (V2/V3 not authorized)

## Run directory layout

Future runs use `evidence/vision/<date>_<stage>_<run>/` and must never overwrite
history. Stage tags:

| Stage | Meaning |
|---|---|
| `V0_SHELL` | Package/shell only; `source_kind=NONE_NOT_APPLICABLE` |
| `V1_OFFLINE` | File/offline 2D detection + labels/metrics |
| `V1_ROS` | ROS Image path (dev webcam / fake / bag) — label source clearly |
| `V2_POSITION` | Depth-qualified positions + independent truth (**not authorized**) |
| `V3_TRACKING` | Identity sequences / reset / occlusion (**not authorized**) |

Each run must preserve at least:

- `metadata.json` with REAL_CAMERA / RECORDED_CAMERA / OFFLINE_FILE / SYNTHETIC /
  DEV_WEBCAM / NONE_NOT_APPLICABLE, code commit, and PASS/FAIL/BLOCKED/NOT_RUN;
- `parameters.yaml`, `source_hash.txt`, `manifest.sha256`;
- `acceptance_protocol.yaml` frozen before formal acceptance runs;
- `logs/`; raw `inputs/` or rosbag as applicable.

V1 adds `detections.csv`, labels, boxed images and model manifest.
Do not file a skeleton status heartbeat as a no-target detection run.
Do not label DEV_WEBCAM evidence as ZED or METRIC_VALIDATED production acceptance.

## Empty templates (copy then fill)

| Template | Use |
|---|---|
| `templates/V1_OFFLINE/` | Offline CLI runs |
| `templates/V1_ROS/` | `mode:=v1_ros` fake/webcam smokes |

```bash
RUN=evidence/vision/$(date +%Y%m%d)_V1_ROS_smoke01
mkdir -p "$RUN/logs"
cp evidence/vision/templates/V1_ROS/* "$RUN/"
# rename *.template → final names, fill fields, then run and attach logs
```

Keep failed and incomplete runs. Model weights may be gitignored; record on-disk
path and SHA256.
