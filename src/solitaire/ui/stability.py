"""Process stability for PyQt6 applications.

PyQt6's default handling of an unhandled Python exception that escapes a
slot or a reimplemented Qt virtual (``mousePressEvent``, paint handlers,
signal slots, ...) is to call ``qFatal`` after printing the traceback,
which **aborts the whole process**. One small bug on any interaction path
would therefore terminate the application the moment the user clicks.

Installing this hook changes that contract: the traceback is printed and
appended to a log file, and the application keeps running (the failed
action is abandoned). It does not mask the bug — every occurrence is
logged loudly — it only prevents a single defect from taking the whole
game down mid-interaction.
"""

from __future__ import annotations

import sys
import tempfile
import time
import traceback
from pathlib import Path

LOG_NAME = "klondike-solitaire-errors.log"


def install_slot_exception_hook(log_dir: str | Path | None = None) -> None:
    """Replace ``sys.excepthook`` with a logging, keep-running hook.

    Called from the application entry points (``solitaire.main`` and
    ``solitaire.ui.premium.app``) — never from library imports, so tooling
    that imports this package keeps the default interpreter behavior.
    """
    previous = sys.excepthook

    def slot_exception_hook(kind, value, tb) -> None:
        formatted = "".join(traceback.format_exception(kind, value, tb))
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"[{stamp}] unexpected error (application keeps running):\n{formatted}",
            file=sys.stderr,
            flush=True,
        )
        try:
            base = Path(log_dir) if log_dir is not None else Path(tempfile.gettempdir())
            with open(base / LOG_NAME, "a", encoding="utf-8") as handle:
                handle.write(f"[{stamp}]\n{formatted}\n")
        except OSError:
            # A failing diagnostic log must never become a second problem.
            pass
        # Preserve any pre-existing hook semantics after ours.
        if previous is not None and previous not in (sys.__excepthook__, slot_exception_hook):
            try:
                previous(kind, value, tb)
            except Exception:  # pragma: no cover - defensive
                pass

    sys.excepthook = slot_exception_hook
