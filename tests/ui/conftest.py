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

from solitaire.ui.premium.animations.card_animation_manager import (  # noqa: E402
    CardAnimationManager,
)
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


@pytest.fixture()
def full_motion(window):
    """Pin animation policy for tests that assert real cosmetic timelines.

    The app correctly restores Reduce Motion and animation speed from the
    user's QSettings. Tests of the 140ms lift / rejection shake must not
    inherit that personal preference, otherwise a valid Reduce Motion setup
    turns those timelines into zero-duration snaps and makes tests
    environment-dependent.
    """
    original_reduce_motion = window._reduce_motion
    original_speed = window._speed_multiplier

    window._reduce_motion = False
    window._speed_multiplier = 1.0
    window._apply_animation_settings()
    yield CardAnimationManager.instance()

    window._reduce_motion = original_reduce_motion
    window._speed_multiplier = original_speed
    window._apply_animation_settings()
