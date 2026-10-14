# Vision examples (templates only)

This directory holds **JSON templates only**. It does **not** contain ONNX/PT
weights and must not be used to auto-download models.

| File | Purpose |
|---|---|
| `model_manifest.template.json` | Fill SHA256 / license after a local YOLO11n-seg ONNX export |

Copy the template next to your local ONNX (outside the repo or under a
gitignored path), fill hashes, then pass absolute paths to launch:

```bash
model_path:=/home/YOU/vision_models/yolo11n-seg.onnx
model_manifest_path:=/home/YOU/vision_models/model_manifest.json
```

See `../README.md` § “Local ONNX + manifest” for export steps and webcam trial commands.
