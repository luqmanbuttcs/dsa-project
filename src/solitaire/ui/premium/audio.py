"""Optional, dependency-free UI sound playback.

Sounds are tiny bundled WAVs played through QtMultimedia's QSoundEffect —
no new Python dependencies and no external services. Everything degrades
silently: if QtMultimedia is unavailable (some headless containers) the
manager simply reports itself unavailable and the game stays fully
functional. The mute control lives in Game Mode & settings and persists
via QSettings; volume is deliberately low (0.22).
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QSettings

from solitaire.ui.premium import resources

SOUND_NAMES = (
    "card_pick",
    "card_place",
    "stock_draw",
    "card_flip",
    "foundation",
    "invalid",
    "victory",
)

_SETTINGS_KEY = "sound_enabled"


class SoundManager(QObject):
    """Lazily-initialised QSoundEffect pool with a persisted mute switch."""

    _instance: SoundManager | None = None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.enabled = QSettings("CSC200", "KlondikeSolitairePremium").value(
            _SETTINGS_KEY, True, type=bool
        )
        self.available = False
        self._effects: dict[str, object] = {}
        self._initialised = False

    @classmethod
    def instance(cls) -> SoundManager:
        if cls._instance is None:
            cls._instance = SoundManager()
        return cls._instance

    # --- lifecycle ------------------------------------------------------------
    def _ensure_initialised(self) -> None:
        if self._initialised:
            return
        self._initialised = True
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl

            for name in SOUND_NAMES:
                path = resources.get_audio_path(f"{name}.wav")
                effect = QSoundEffect(self)
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(0.22)
                self._effects[name] = effect
            self.available = True
        except Exception:  # ImportError or backend failure — audio stays off
            self.available = False
            self._effects = {}

    # --- api -------------------------------------------------------------------
    def play(self, name: str) -> None:
        if not self.enabled:
            return
        if not self._initialised:
            self._ensure_initialised()
        if not self.available:
            return
        effect = self._effects.get(name)
        if effect is None:
            return
        try:
            effect.play()
        except RuntimeError:
            pass

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        QSettings("CSC200", "KlondikeSolitairePremium").setValue(_SETTINGS_KEY, self.enabled)
