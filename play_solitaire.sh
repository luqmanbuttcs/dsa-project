#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Python 3.12 or newer is required. Install it from https://www.python.org/downloads/ and retry."
    read -r -p "Press Enter to close..." _ || true
    exit 2
fi

"$PYTHON" tools/launch_game.py "$@"
status=$?
if [ "$status" -ne 0 ]; then
    echo
    read -r -p "Solitaire could not start. Press Enter to close..." _ || true
fi
exit "$status"
