#!/bin/bash
# macOS Finder double-click launcher. It opens the shared bootstrap in Terminal.
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
bash "$ROOT/play_solitaire.sh" "$@"
