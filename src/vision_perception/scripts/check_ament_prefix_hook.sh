#!/usr/bin/env bash
# Regression check after colcon install (run on Humble VM).
# Usage:
#   source /opt/ros/humble/setup.bash
#   source install/setup.bash
#   bash src/vision_perception/scripts/check_ament_prefix_hook.sh
set -euo pipefail

PKG=vision_perception

if ! ros2 pkg prefix "$PKG" >/dev/null 2>&1; then
  echo "FAIL: ros2 pkg prefix $PKG failed (AMENT_PREFIX_PATH missing package?)"
  echo "AMENT_PREFIX_PATH=${AMENT_PREFIX_PATH:-<unset>}"
  exit 1
fi

PREFIX="$(ros2 pkg prefix "$PKG")"
DSV="$PREFIX/share/$PKG/package.dsv"
HOOK_DSV="$PREFIX/share/$PKG/hook/ament_prefix_path.dsv"

if [[ ! -f "$DSV" ]]; then
  echo "FAIL: missing $DSV"
  exit 1
fi

if ! grep -q 'ament_prefix_path' "$DSV"; then
  echo "FAIL: $DSV has no ament_prefix_path entry:"
  cat "$DSV"
  exit 1
fi

if [[ ! -f "$HOOK_DSV" ]]; then
  echo "FAIL: missing $HOOK_DSV"
  exit 1
fi

if ! grep -q 'AMENT_PREFIX_PATH' "$HOOK_DSV"; then
  echo "FAIL: $HOOK_DSV does not mention AMENT_PREFIX_PATH"
  cat "$HOOK_DSV"
  exit 1
fi

case ":${AMENT_PREFIX_PATH}:" in
  *":${PREFIX}:"*) ;;
  *)
    echo "FAIL: AMENT_PREFIX_PATH does not contain $PREFIX"
    echo "AMENT_PREFIX_PATH=$AMENT_PREFIX_PATH"
    exit 1
    ;;
esac

LIBEXEC="$PREFIX/lib/$PKG"
for exe in vision_perception_node vision_offline_detect vision_webcam_publisher vision_fake_image_publisher; do
  if [[ ! -x "$LIBEXEC/$exe" ]]; then
    echo "FAIL: missing executable $LIBEXEC/$exe"
    ls -la "$LIBEXEC" 2>/dev/null || true
    exit 1
  fi
done

echo "OK: $PKG prefix=$PREFIX"
echo "OK: package.dsv includes ament_prefix_path"
echo "OK: AMENT_PREFIX_PATH contains package prefix"
echo "OK: libexec scripts present under $LIBEXEC"
ros2 pkg executables "$PKG"
ros2 launch "$PKG" vision.launch.py --show-args >/dev/null
echo "OK: ros2 launch $PKG vision.launch.py --show-args"
