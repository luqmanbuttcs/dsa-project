#!/usr/bin/env python3
"""Bootstrap the runtime environment and launch Klondike Solitaire.

Only the game/runtime dependencies are installed. This launcher never runs
pytest or installs the optional development dependencies.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_DIR = PROJECT_ROOT / ".game-venv"
MARKER = ENV_DIR / ".project-install-sha256"
MINIMUM_PYTHON = (3, 12)


def _python_candidates() -> list[list[str]]:
    """Return likely Python commands, preferring the interpreter running us."""
    candidates: list[list[str]] = [[sys.executable]]
    if os.name == "nt":
        candidates.extend(
            [["py", version] for version in ("-3.14", "-3.13", "-3.12", "-3")]
        )
    else:
        candidates.extend(
            [[name] for name in ("python3.14", "python3.13", "python3.12", "python3", "python")]
        )
    return candidates


def _find_base_python() -> Path | None:
    """Find an installed Python 3.12+ executable for the isolated venv."""
    seen: set[tuple[str, ...]] = set()
    for command in _python_candidates():
        key = tuple(command)
        if key in seen:
            continue
        seen.add(key)
        if command[0] not in (sys.executable, "py") and shutil.which(command[0]) is None:
            continue
        try:
            probe = subprocess.run(
                [
                    *command,
                    "-c",
                    "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}'); print(sys.executable)",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            lines = probe.stdout.strip().splitlines()
            major, minor = (int(part) for part in lines[0].split("."))
            if (major, minor) >= MINIMUM_PYTHON and len(lines) > 1:
                return Path(lines[1]).resolve()
        except (OSError, subprocess.CalledProcessError, ValueError, IndexError):
            continue
    return None


def _venv_python() -> Path:
    if os.name == "nt":
        return ENV_DIR / "Scripts" / "python.exe"
    return ENV_DIR / "bin" / "python"


def _is_supported_python(executable: Path) -> bool:
    try:
        result = subprocess.run(
            [
                str(executable),
                "-c",
                "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)",
            ],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except OSError:
        return False


def _project_fingerprint() -> str:
    """Fingerprint dependency/build configuration, not source code.

    The environment uses an editable install, so Python source edits do not
    need a reinstall. A pyproject change does.
    """
    return hashlib.sha256((PROJECT_ROOT / "pyproject.toml").read_bytes()).hexdigest()


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def _prepare_environment(base_python: Path) -> Path:
    """Create/reuse the app-only venv and install runtime dependencies once."""
    python = _venv_python()
    if not python.exists() or not _is_supported_python(python):
        # .game-venv is reserved for this launcher, so replacing it cannot
        # remove the developer's separate .venv.
        if ENV_DIR.exists():
            print("Replacing the old or incompatible Solitaire runtime environment...")
            shutil.rmtree(ENV_DIR)
        print("First launch: creating an isolated Python environment...")
        _run([str(base_python), "-m", "venv", str(ENV_DIR)])

    fingerprint = _project_fingerprint()
    installed_fingerprint = MARKER.read_text(encoding="utf-8").strip() if MARKER.exists() else ""
    imports_work = subprocess.run(
        [str(python), "-c", "import PyQt6; import solitaire"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0

    if installed_fingerprint != fingerprint or not imports_work:
        print("First launch (or project dependency change): installing game requirements...")
        print("This installs the game only. It does not run tests or install developer tools.")
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-warn-script-location",
                "--editable",
                str(PROJECT_ROOT),
            ]
        )
        MARKER.write_text(fingerprint + "\n", encoding="utf-8")
        print("Game setup complete. Future launches will reuse this environment.")

    return python


def main() -> int:
    base_python = _find_base_python()
    if base_python is None:
        print("Python 3.12 or newer is required to run the source version of this game.", file=sys.stderr)
        print(
            "Install Python 3.12+ from https://www.python.org/downloads/ and run this launcher again.",
            file=sys.stderr,
        )
        return 2

    try:
        app_python = _prepare_environment(base_python)
    except subprocess.CalledProcessError as exc:
        print(
            "\nSolitaire setup failed. Check your internet connection and Python installation, then retry.",
            file=sys.stderr,
        )
        return exc.returncode or 1
    except OSError as exc:
        print(f"\nSolitaire could not prepare its runtime environment: {exc}", file=sys.stderr)
        return 1

    print("Starting Klondike Solitaire...")
    return subprocess.run(
        [str(app_python), "-m", "solitaire.main", *sys.argv[1:]],
        cwd=PROJECT_ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
