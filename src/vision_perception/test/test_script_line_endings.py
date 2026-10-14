"""Ensure vision scripts stay LF-only (CRLF shebang -> python3\\r exit 127)."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
REPO_ROOT = ROOT.parents[1]


def test_gitattributes_forces_lf_for_vision_scripts():
    text = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "src/vision_perception/scripts/**" in text
    assert "eol=lf" in text


def test_scripts_directory_files_have_no_crlf():
    paths = sorted(p for p in SCRIPTS.iterdir() if p.is_file())
    assert paths, "expected scripts under src/vision_perception/scripts"
    for path in paths:
        data = path.read_bytes()
        assert b"\r\n" not in data and b"\r" not in data, (
            f"{path} contains CR; keep Unix LF only "
            "(see .gitattributes src/vision_perception/scripts/**)"
        )
        if path.name != "check_ament_prefix_hook.sh":
            assert data.startswith(b"#!/usr/bin/env python3\n"), path


def test_check_script_accepts_environment_prefix_wiring():
    text = (SCRIPTS / "check_ament_prefix_hook.sh").read_text(encoding="utf-8")
    assert "environment/ament_prefix_path.sh" in text
    assert "local_setup.dsv" in text
    # Must not require package.dsv -> hook/ alone (false FAIL on ament_cmake).
    assert "Do not require the hook/ path alone" in text
