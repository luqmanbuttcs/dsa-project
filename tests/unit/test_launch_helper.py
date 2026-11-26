from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "launch_game.py"
SPEC = importlib.util.spec_from_file_location("solitaire_launch_game", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


def test_project_fingerprint_tracks_pyproject(tmp_path, monkeypatch):
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text('[project]\nname = "test-game"\n', encoding="utf-8")
    monkeypatch.setattr(launcher, "PROJECT_ROOT", tmp_path)

    expected = hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert launcher._project_fingerprint() == expected

    manifest.write_text('[project]\nname = "changed-game"\n', encoding="utf-8")
    assert launcher._project_fingerprint() != expected


def test_game_environment_is_separate_from_developer_venv(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "ENV_DIR", tmp_path / ".game-venv")
    path = launcher._venv_python()
    assert path.parent.name in {"Scripts", "bin"}
    assert ".game-venv" in path.parts
    assert ".venv" not in path.parts


def test_python_minimum_matches_project_metadata():
    import tomllib

    metadata = tomllib.loads((SCRIPT.parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["requires-python"] == ">=3.12"
    assert launcher.MINIMUM_PYTHON == (3, 12)
