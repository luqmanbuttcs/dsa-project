"""Shared offscreen fixtures for the premium UI regression tests.

The fixtures previously lived in test_premium_ui.py; they moved here so the
responsive-layout and animation regressions can reuse the exact same
deterministic window construction and teardown without duplication.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import gc  # noqa: E402

import pytest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from solitaire.ui.premium.main_window import PremiumMainWindow  # noqa: E402

SEED = 1  # deals a deterministic board with a tableau hint (H-2, tableau-5 -> tableau-4)


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.fixture()
def window(app):
    built = PremiumMainWindow(seed=SEED)
    built.show()
    app.processEvents()
    yield built
    # Deterministic teardown: halt animations while items are alive, then
    # delete the C++ tree on the spot instead of leaving it to cyclic GC
    # during a later test (this aborted CI with exit code 134).
    built.close()
    built.deleteLater()
    app.processEvents()
    gc.collect()
