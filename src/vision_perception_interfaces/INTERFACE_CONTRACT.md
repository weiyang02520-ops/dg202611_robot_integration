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

## Runtime gates (vision_perception package)

Until separately authorized, `vision_perception` keeps:

- `enable_objects:=false` (true rejected at config validation)
- `enable_tracking:=false` / `tracking_enabled:=false` (true rejected)

Message types here are frozen only; enabling those flags does **not** implement
depth pairing, `/objects` publish, or tracking.

## V1 evidence shells

Empty metadata templates ship inside `vision_perception` (not this interfaces
package): `src/vision_perception/evidence/templates/` →
`share/vision_perception/evidence/templates/`. Isolated two-package syncs do
not need the monorepo `evidence/` tree.

## Consumers audit (this repo)

No in-repo subscriber to `vision_perception_interfaces/VisionObject*` was found
when this contract was finalized. If one appears before V2, pause and
re-authorize interface changes.
