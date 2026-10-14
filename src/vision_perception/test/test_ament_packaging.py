"""Guard ament_python install layout (no ROS required).

Duplicate setuptools data_files destinations drop earlier files (e.g. package.xml),
which breaks ament_prefix_path / ``ros2 pkg prefix`` after isolated colcon install.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_setup_py_uses_unique_data_files_helper():
    text = (ROOT / "setup.py").read_text(encoding="utf-8")
    assert "def _unique_data_files" in text
    assert "duplicate data_files destinations" in text
    assert 'resource/" + PACKAGE_NAME' in text or "resource/" + "vision_perception" in text
    assert '"package.xml"' in text
    assert '"requirements-runtime.txt"' in text
    # package.xml must be installed together with other share/pkg files (one dest).
    assert "share_pkg" in text


def test_resource_marker_and_package_xml_exist():
    assert (ROOT / "resource" / "vision_perception").is_file()
    assert (ROOT / "package.xml").is_file()
    xml = (ROOT / "package.xml").read_text(encoding="utf-8")
    assert "<name>vision_perception</name>" in xml
    assert "ament_python" in xml


def test_setup_py_ast_calls_unique_data_files():
    tree = ast.parse((ROOT / "setup.py").read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setup"
    ]
    assert calls, "setup() call not found"
    setup_call = calls[0]
    keywords = {kw.arg: kw.value for kw in setup_call.keywords if kw.arg}
    assert "data_files" in keywords
    value = keywords["data_files"]
    assert isinstance(value, ast.Call)
    assert isinstance(value.func, ast.Name)
    assert value.func.id == "_unique_data_files"


def test_unique_data_files_runs_and_includes_ament_marker():
    # Execute helper in package directory context without invoking setup().
    ns: dict = {"__file__": str(ROOT / "setup.py")}
    code = (ROOT / "setup.py").read_text(encoding="utf-8")
    # Strip the setup() call so importing logic is safe under pytest.
    trimmed = code.split("\nsetup(")[0] + "\n"
    import os

    prev = os.getcwd()
    os.chdir(ROOT)
    try:
        exec(compile(trimmed, str(ROOT / "setup.py"), "exec"), ns, ns)
        entries = ns["_unique_data_files"]()
    finally:
        os.chdir(prev)

    destinations = [dest for dest, _ in entries]
    assert len(destinations) == len(set(destinations))
    assert "share/ament_index/resource_index/packages" in destinations
    share_files = dict(entries)["share/vision_perception"]
    assert "package.xml" in share_files
    assert "requirements-runtime.txt" in share_files
    marker_files = dict(entries)["share/ament_index/resource_index/packages"]
    assert marker_files == ["resource/vision_perception"]
