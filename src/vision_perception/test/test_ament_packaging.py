"""Guard ament_cmake_python layout that emits ament_prefix_path hooks."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_package_xml_is_ament_cmake_python_hybrid():
    xml = (ROOT / "package.xml").read_text(encoding="utf-8")
    assert "<buildtool_depend>ament_cmake</buildtool_depend>" in xml
    assert "<buildtool_depend>ament_cmake_python</buildtool_depend>" in xml
    assert "<build_type>ament_cmake</build_type>" in xml
    assert "ament_python</build_type>" not in xml


def test_cmakelists_calls_ament_package_and_python_install():
    text = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "ament_cmake_python" in text
    assert "ament_python_install_package(${PROJECT_NAME})" in text
    assert "ament_package()" in text
    assert "install(DIRECTORY launch config examples" in text
    # Document why we switched away from pure ament_python.
    assert "ament_prefix_path" in text


def test_setup_py_does_not_install_share_data_files():
    """setuptools share/ installs can clobber ament-generated hooks."""
    text = (ROOT / "setup.py").read_text(encoding="utf-8")
    assert "data_files=[]" in text or "data_files = []" in text
    assert "share/ament_index" not in text
    assert "_unique_data_files" not in text

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
    assert "data_files" in keywords
    value = keywords["data_files"]
    assert isinstance(value, ast.List)
    assert value.elts == []


def test_check_ament_prefix_hook_script_exists():
    script = ROOT / "scripts" / "check_ament_prefix_hook.sh"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "ros2 pkg prefix" in text
    assert "ament_prefix_path" in text
    assert "AMENT_PREFIX_PATH" in text


def test_package_xml_and_readme_still_present_for_cmake_install():
    assert (ROOT / "package.xml").is_file()
    assert (ROOT / "README.md").is_file()
    assert (ROOT / "requirements-runtime.txt").is_file()
    assert (ROOT / "launch" / "vision.launch.py").is_file()
