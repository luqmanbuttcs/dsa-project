"""Navigation between the Play Workspace and the DSA Lab."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from solitaire.ui.premium.navigation import Workspace


class NavigationController(QObject):
    """Switches the top-level workspace and forwards lab page changes."""

    workspace_changed = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._current = Workspace.PLAY

    @property
    def current(self) -> Workspace:
        return self._current

    def open_workspace(self, workspace: Workspace) -> None:
        if workspace is self._current:
            return
        self._current = workspace
        self.workspace_changed.emit(workspace.value)

    def open_play(self) -> None:
        self.open_workspace(Workspace.PLAY)

    def open_dsa_lab(self) -> None:
        self.open_workspace(Workspace.DSA_LAB)
