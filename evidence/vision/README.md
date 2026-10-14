# Vision Evidence Policy

Status: NO_CAMERA_OR_ROS_ACCEPTANCE_RUN_IN_THIS_TREE.
V0 shell verification evidence (if any) lives on the owner's Ubuntu 22.04 +
ROS 2 Humble VM, not necessarily in this repository. Cloud unit tests for V1
offline algorithms are not camera evidence.

`camera_contract=NOT_RUN`. `ARM_READY=NO`.

## Run directory layout

Future runs use `evidence/vision/<date>_<stage>_<run>/` and must never overwrite
history. Stage tags:

| Stage | Meaning |
|---|---|
| `V0_SHELL` | Package/shell only; `source_kind=NONE_NOT_APPLICABLE` |
| `V1_OFFLINE` | File/offline 2D detection + labels/metrics |
| `V1_ROS` | ROS replay or live 2D path (separate authorization) |
| `V2_POSITION` | Depth-qualified positions + independent truth |
| `V3_TRACKING` | Identity sequences / reset / occlusion |

Each run must preserve at least:

- `metadata.json` with REAL_CAMERA / RECORDED_CAMERA / OFFLINE_FILE / SYNTHETIC /
  NONE_NOT_APPLICABLE source classification, code commit, dirty snapshot, and
  PASS/FAIL/BLOCKED/NOT_RUN;
- `parameters.yaml`, `source_hash.txt`, `manifest.sha256`;
- `acceptance_protocol.yaml` frozen before the run;
- `logs/`; raw `inputs/` or rosbag as applicable.

V1 adds `detections.csv`, labels, boxed images and model manifest.
V2 adds `objects.csv`, `paired_frames.csv`, `rejected-input.csv`, CameraInfo
contract and independent surface-point truth.
V3 adds `tracks.csv`, identity labels and reset/occlusion timelines.
Runtime runs add `latency.csv`, `resources.csv`, `metrics.json`.

CSV common keys: `source_session_id`, `observation_id`, `detection_index`,
`source_stamp`, `frame_id`, `source_image_id` (when applicable). Missing numeric
values stay empty — never disguise as `0`.

Keep failed and incomplete runs. Never replace missing depth with a valid zero
position, fabricate an object or pose, or file an empty shell as a no-target run.
Synthetic examples, real camera results and hardware/arm experiments must remain
separately labelled. Do not copy existing navigation or UWB data here as vision
acceptance evidence. Model weights may be gitignored; record their on-disk path
and SHA256 — a hash alone does not prove the file is retained.
