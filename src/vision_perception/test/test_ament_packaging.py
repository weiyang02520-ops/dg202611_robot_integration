"""Guard ament_cmake_python layout: prefix hooks + libexec scripts."""

from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXEC_NAMES = (
    "vision_perception_node",
    "vision_offline_detect",
    "vision_webcam_publisher",
    "vision_fake_image_publisher",
)


def test_package_xml_is_ament_cmake_python_hybrid():
    xml = (ROOT / "package.xml").read_text(encoding="utf-8")
    assert "<buildtool_depend>ament_cmake</buildtool_depend>" in xml
    assert "<buildtool_depend>ament_cmake_python</buildtool_depend>" in xml
    assert "<build_type>ament_cmake</build_type>" in xml
    assert "ament_python</build_type>" not in xml


def test_package_xml_comments_contain_no_double_hyphen():
    """XML comments cannot contain '--' (breaks package_xml_2_cmake.py)."""
    xml = (ROOT / "package.xml").read_text(encoding="utf-8")
    comments = re.findall(r"<!--(.*?)-->", xml, flags=re.DOTALL)
    assert comments, "expected at least one XML comment"
    for comment in comments:
        assert "--" not in comment, f"illegal '--' inside XML comment: {comment!r}"


def test_cmakelists_installs_libexec_scripts():
    text = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "ament_python_install_package(${PROJECT_NAME})" in text
    assert "ament_package()" in text
    assert "DESTINATION lib/${PROJECT_NAME}" in text
    assert "install(PROGRAMS" in text
    for name in EXEC_NAMES:
        assert f"scripts/{name}" in text


def test_libexec_script_wrappers_exist():
    for name in EXEC_NAMES:
        path = ROOT / "scripts" / name
        assert path.is_file(), path
        text = path.read_text(encoding="utf-8")
        assert text.startswith("#!/usr/bin/env python3")
        # CMake install(PROGRAMS) installs with execute permission even if the
        # working-tree bit is lost on some checkouts; prefer shebang + CMake list.


def test_setup_py_does_not_install_share_or_console_entry_points():
    text = (ROOT / "setup.py").read_text(encoding="utf-8")
    assert "data_files=[]" in text or "data_files = []" in text
    assert "share/ament_index" not in text
    tree = ast.parse(text)
    setup_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setup"
    ]
    assert setup_calls
    keywords = {kw.arg: kw.value for kw in setup_calls[0].keywords if kw.arg}
    assert isinstance(keywords["data_files"], ast.List)
    assert keywords["data_files"].elts == []
    # ament_python_install_package ignores setuptools console_scripts.
    assert "entry_points" not in keywords


def test_check_ament_prefix_hook_script_exists():
    script = ROOT / "scripts" / "check_ament_prefix_hook.sh"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "ros2 pkg prefix" in text
    assert "ament_prefix_path" in text
