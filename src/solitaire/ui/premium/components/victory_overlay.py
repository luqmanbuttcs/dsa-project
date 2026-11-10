"""Victory presentation: a polished, non-blocking celebration overlay.

Shown when the engine reports a won game. Golden confetti drifts behind a
centred panel carrying the final score, moves and elapsed time, with New
Game and Return to Play actions. Reduce Motion skips the confetti motion.
The overlay never blocks the event loop — pressing either button, Escape
or clicking the backdrop returns to the live table.
"""

from __future__ import annotations

import random

from PyQt6.QtCore import QEasingCurve, QPointF, QRectF, QSettings, Qt, QTimer, QVariantAnimation, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QVBoxLayout,
    QWidget,
)

from solitaire.ui.premium.theme import FONT_DISPLAY

GOLD = "#F0C75E"
GOLD_DEEP = "#C9A227"
CONFETTI_MS_STEP = 33
# Celebration stays satisfying but leaves promptly: motes settle in ~4.5s
# (was 6.2s), shortened further by the animation-speed setting via the
# manager. The timer is event-driven and dismissible at any moment, so the
# effect never blocks gameplay.
CONFETTI_LIFETIME_MS = 4500


class _PanelFadeAnimation(QVariantAnimation):
    """Opacity ramp for the victory panel (self-contained, dies with it)."""

    def __init__(self, effect: QGraphicsOpacityEffect, parent: QWidget) -> None:
        super().__init__(parent)
        self._effect = effect
        self.setDuration(_scaled(320))
        self.setStartValue(0.0)
        self.setEndValue(1.0)
        self.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.valueChanged.connect(self._apply)

    def _apply(self, value) -> None:
        try:
            self._effect.setOpacity(float(value))
        except RuntimeError:
            pass


def _scaled(ms: int) -> int:
    """Follow the user's animation speed (2.0x = twice the speed)."""
    from solitaire.ui.premium.animations.card_animation_manager import (
        CardAnimationManager,
    )

    return CardAnimationManager.instance().duration_for(ms)


class _Confetti:
    """One golden mote drifting down behind the victory panel."""

    __slots__ = ("x", "y", "vy", "vx", "size", "spin", "angle", "color", "age")

    def __init__(self, width: float, rng: random.Random) -> None:
        self.x = rng.uniform(0.0, width)
        self.y = rng.uniform(-140.0, -6.0)
        self.vy = rng.uniform(46.0, 128.0)
        self.vx = rng.uniform(-16.0, 16.0)
        self.size = rng.uniform(2.4, 5.4)
        self.spin = rng.uniform(-3.4, 3.4)
        self.angle = rng.uniform(0.0, 6.28)
        self.age = 0.0
        palette = [(240, 199, 94), (201, 162, 39), (64, 224, 178), (246, 231, 176)]
        chosen = palette[rng.randrange(len(palette))]
        self.color = QColor(*chosen)


class VictoryOverlay(QWidget):
    """Full-area translucent celebration layer above the play workspace."""

    #: Emitted after any dismissal (Escape, backdrop click, either button)
    #: so the window can disarm its window-level Escape shortcut.
    dismissed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        # The overlay must be able to receive key events (Escape) directly:
        # present() takes focus so the key reaches keyPressEvent even when no
        # other widget held it, and the window-level shortcut covers the case
        # where focus intentionally stays elsewhere (e.g. the board view).
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Timers first: setVisible(False) below synchronously fires hideEvent.
        self._confetti: list[_Confetti] = []
        self._rng = random.Random()
        self._elapsed_ms = 0.0
        self._reduce_motion = False
        self._timer = QTimer(self)
        self._timer.setInterval(CONFETTI_MS_STEP)
        self._timer.timeout.connect(self._step_confetti)
        self.setVisible(False)

        self._panel = QFrame(self)
        self._panel.setObjectName("victoryPanel")
        self._panel.setStyleSheet(
            f"""
            QFrame#victoryPanel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #10233F, stop:1 #0A1626);
                border: 2px solid {GOLD_DEEP};
                border-radius: 18px;
            }}
            """
        )
        self._panel.setFixedSize(430, 330)

        layout = QVBoxLayout(self._panel)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(10)

        self._title = QLabel("VICTORY")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            f"font-family: {FONT_DISPLAY}; font-size: 44px; font-weight: bold;"
            f"color: {GOLD}; background: transparent; letter-spacing: 6px;"
        )
        layout.addWidget(self._title)

        self._subtitle = QLabel("All four foundations complete — a flawless table.")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setObjectName("mutedText")
        self._subtitle.setWordWrap(True)
        layout.addWidget(self._subtitle)

        layout.addSpacing(6)
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._stat_labels: dict[str, QLabel] = {}
        for key, caption in (("score", "SCORE"), ("moves", "MOVES"), ("time", "TIME")):
            column = QVBoxLayout()
            column.setSpacing(2)
            value = QLabel("0")
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value.setStyleSheet(
                f"color: {GOLD}; font-size: 24px; font-weight: bold; background: transparent;"
            )
            caption_label = QLabel(caption)
            caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            caption_label.setStyleSheet(
                "color: #9FB0C6; font-size: 10px; font-weight: bold;"
                "letter-spacing: 2px; background: transparent;"
            )
            column.addWidget(value)
            column.addWidget(caption_label)
            self._stat_labels[key] = value
            stats_row.addLayout(column, 1)
        layout.addLayout(stats_row)
        layout.addStretch(1)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.new_game_button = QPushButton("  Deal a New Game")
        self.new_game_button.setObjectName("goldButton")
        self.play_on_button = QPushButton("Return to Play")
        self.play_on_button.setObjectName("darkButton")
        buttons.addWidget(self.new_game_button, 1)
        buttons.addWidget(self.play_on_button, 1)
        layout.addLayout(buttons)

    # --- presentation -------------------------------------------------------
    def present(
        self, score: int, moves: int, seconds: int, *, reduce_motion: bool = False
    ) -> None:
        minutes, rest = divmod(max(0, seconds), 60)
        self._stat_labels["score"].setText(str(score))
        self._stat_labels["moves"].setText(str(moves))
        self._stat_labels["time"].setText(f"{minutes:02d}:{rest:02d}")
        self._reduce_motion = reduce_motion
        self._elapsed_ms = 0.0
        self._confetti = []
        self.setGeometry(self.parentWidget().rect())
        self._panel.move(
            (self.width() - self._panel.width()) // 2,
            (self.height() - self._panel.height()) // 2 - 12,
        )
        self.show()
        self.raise_()
        self.setFocus()
        if not reduce_motion:
            width = float(max(1, self.width()))
            self._confetti = [_Confetti(width, self._rng) for _ in range(90)]
            self._timer.start()
        # Gentle fade-in of the panel.
        self._panel.show()
        effect = QGraphicsOpacityEffect(self._panel)
        self._panel.setGraphicsEffect(effect)
        animation = _PanelFadeAnimation(effect, self)
        animation.start()

    # --- interaction ----------------------------------------------------------
    def hideEvent(self, event) -> None:  # noqa: N802
        timer = getattr(self, "_timer", None)
        if timer is not None:
            timer.stop()
        super().hideEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.isVisible():
            self.setGeometry(self.parentWidget().rect())
            self._panel.move(
                (self.width() - self._panel.width()) // 2,
                (self.height() - self._panel.height()) // 2 - 12,
            )

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss()
            event.accept()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if not self._panel.geometry().contains(event.position().toPoint()):
            self.dismiss()
            event.accept()
            return
        super().mousePressEvent(event)

    def dismiss(self) -> None:
        self._timer.stop()
        self.hide()
        self.dismissed.emit()

    # --- confetti ---------------------------------------------------------------
    def _step_confetti(self) -> None:
        if self._reduce_motion or not self._confetti:
            self._timer.stop()
            return
        self._elapsed_ms += CONFETTI_MS_STEP
        dt = CONFETTI_MS_STEP / 1000.0
        height = float(self.height())
        alive = False
        for mote in self._confetti:
            mote.age += dt
            if mote.y > height + 12 or mote.age * 1000.0 > CONFETTI_LIFETIME_MS:
                continue
            alive = True
            mote.y += mote.vy * dt
            mote.x += mote.vx * dt
            mote.angle += mote.spin * dt
            mote.vy = min(mote.vy + 14.0 * dt, 150.0)
        if not alive or self._elapsed_ms > CONFETTI_LIFETIME_MS:
            self._timer.stop()
            if self._elapsed_ms > CONFETTI_LIFETIME_MS:
                self._confetti = []
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        # Translucent navy backdrop keeps the finished table visible below.
        painter.fillRect(self.rect(), QColor(4, 10, 20, 208))
        if self._confetti:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            for mote in self._confetti:
                age_factor = max(0.0, 1.0 - mote.age * 1000.0 / CONFETTI_LIFETIME_MS)
                color = QColor(mote.color)
                color.setAlpha(int(235 * min(1.0, age_factor + 0.25)))
                painter.setPen(QPen(color, mote.size))
                painter.save()
                painter.translate(mote.x, mote.y)
                painter.rotate(mote.angle * 57.3)
                painter.drawLine(QPointF(-mote.size, 0), QPointF(mote.size, 0))
                painter.restore()
        painter.end()
