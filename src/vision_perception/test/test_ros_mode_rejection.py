"""ROS skeleton mode must reject non-skeleton values (no silent fallback)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vision_perception.config import require_ros_skeleton_mode


LAUNCH_PATH = Path(__file__).resolve().parents[1] / "launch" / "vision.launch.py"
NODE_PATH = Path(__file__).resolve().parents[1] / "vision_perception" / "vision_node.py"


@pytest.mark.parametrize("mode", ["v1", "offline", "V1", "ready", "", "detect"])
def test_require_ros_skeleton_mode_rejects_non_skeleton(mode: str):
    with pytest.raises(ValueError, match="Unsupported ROS mode"):
        require_ros_skeleton_mode(mode)


def test_require_ros_skeleton_mode_accepts_skeleton():
    assert require_ros_skeleton_mode("skeleton") == "skeleton"
    assert require_ros_skeleton_mode(" skeleton ") == "skeleton"


def test_launch_declares_and_forwards_mode_argument():
    text = LAUNCH_PATH.read_text(encoding="utf-8")
    assert 'DeclareLaunchArgument(\n            "mode"' in text or 'DeclareLaunchArgument("mode"' in text
    assert '"mode": LaunchConfiguration("mode")' in text
    assert "default_value=\"skeleton\"" in text or "default_value='skeleton'" in text


def test_node_main_exits_nonzero_on_value_error():
    text = NODE_PATH.read_text(encoding="utf-8")
    assert "require_ros_skeleton_mode" in text
    assert "sys.exit(exit_code)" in text
    assert "except ValueError" in text
