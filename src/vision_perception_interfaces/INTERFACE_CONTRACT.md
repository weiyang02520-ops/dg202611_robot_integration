# vision_perception_interfaces — frozen observation contract (plan §3)

| Topic | Message | First publish stage |
|---|---|---|
| `/dg/vision/detections_2d` | `VisionDetectionArray` | V1 |
| `/dg/vision/objects` | `VisionObjectArray` | **V2 only (not authorized yet)** |
| `/dg/vision/status` | `diagnostic_msgs/DiagnosticArray` | V0+ |
| `/dg/vision/debug_image` | `sensor_msgs/Image` | V1 optional, default off |

## Observation keys (shared)

`source_session_id`, `observation_id`, `detection_index`, `header`, `calibration_id`, `source_kind`.

## Hard semantics

- `orientation_valid` is **always false** through V1–V3; orientation components are NaN when unknown.
- `position_valid=true` is **not** arm authorization. `ARM_READY` is a status diagnostic field only (`NO` until an arm stage is authorized).
- V1 must not publish `/dg/vision/objects`.
- V2: `object_id` and `tracking_session_id` empty; `tracking_valid=false`.
- Consumers of legacy `/perception/localized_objects` are out of scope; this package does not replace them silently.

## Consumers audit (this repo)

No in-repo subscriber to `vision_perception_interfaces/VisionObject*` was found when this contract was finalized. If one appears before V2, pause and re-authorize interface changes.
