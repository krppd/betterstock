from __future__ import annotations

from PyQt6.QtCore import QEasingCurve

_aplicado = False


def _arreglar_scroll_del_calendario() -> None:
    from qfluentwidgets.components.date_time.calendar_view import ScrollViewBase

    def _onFirstScrollFinished(self) -> None:
        self.vScrollBar.setScrollAnimation(300, QEasingCurve.Type.OutQuad)
        self.vScrollBar.ani.finished.disconnect(self._onFirstScrollFinished)

    ScrollViewBase._onFirstScrollFinished = _onFirstScrollFinished


def aplicar_parches() -> None:
    global _aplicado
    if _aplicado:
        return
    _aplicado = True
    _arreglar_scroll_del_calendario()
