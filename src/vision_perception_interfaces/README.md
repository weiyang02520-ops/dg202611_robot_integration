# vision_perception_interfaces

Arm-independent ROS 2 message package for manipulation vision (plan §3).

| Message | Used by |
|---|---|
| `VisionDetection2D` / `VisionDetectionArray` | V1 `/dg/vision/detections_2d` |
| `VisionObject` / `VisionObjectArray` | V2 `/dg/vision/objects` when `enable_objects:=true` |

Contract details: [`INTERFACE_CONTRACT.md`](INTERFACE_CONTRACT.md) (also installed
under `share/vision_perception_interfaces/`).

`enable_objects` / `enable_tracking` live in the `vision_perception` node config
and default to **false**. Enabling objects does not enable tracking or arm motion.
