from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QThread, pyqtSignal


class TrabajoImpresion(QThread):
    terminado = pyqtSignal(str)

    def __init__(self, tarea: Callable[[], None], parent=None) -> None:
        super().__init__(parent)
        self._tarea = tarea

    def run(self) -> None:
        try:
            self._tarea()
        except Exception as error:
            self.terminado.emit(str(error) or type(error).__name__)
            return
        self.terminado.emit("")
