from __future__ import annotations

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy, QWidget


class EtiquetaTexto(QLabel):
    def __init__(self, texto: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._completo = ""
        self._alto_aplicado = -1
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if texto:
            self.setText(texto)

    def setText(self, texto: str) -> None:
        self._completo = str(texto)
        super().setText(self._completo)
        self.setToolTip(self._completo)
        self._actualizar()

    def textoCompleto(self) -> str:
        return self._completo

    def _palabra_mas_larga(self) -> str:
        return max(self._completo.split(), key=len, default="")

    def _actualizar(self) -> None:
        ancho = self.width()
        if ancho <= 0 or not self._completo:
            return
        metrics = self.fontMetrics()
        palabra = self._palabra_mas_larga()
        if palabra and metrics.horizontalAdvance(palabra) > ancho:
            texto = metrics.elidedText(self._completo, Qt.TextElideMode.ElideRight, ancho)
        else:
            texto = self._completo
        cambio = texto != self.text()
        if cambio:
            super().setText(texto)
        self._ajustar_alto(ancho)
        if cambio or self._alto_aplicado != self.altoNecesario(ancho):
            self.updateGeometry()

    def _ajustar_alto(self, ancho: int) -> None:
        alto = self.altoNecesario(ancho)
        if alto > 0 and alto != self._alto_aplicado:
            self._alto_aplicado = alto
            self.setMinimumHeight(alto)

    def altoNecesario(self, ancho: int | None = None) -> int:
        if ancho is None:
            ancho = self.width()
        if ancho <= 0:
            return 0
        metrics = self.fontMetrics()
        rect = metrics.boundingRect(
            QRect(0, 0, ancho, 10000), int(Qt.TextFlag.TextWordWrap), self.text())
        return rect.height()

    def minimumSizeHint(self) -> QSize:
        base = super().minimumSizeHint()
        ancho = self.width()
        if ancho <= 0 or not self._completo:
            return base
        metrics = self.fontMetrics()
        palabra = self._palabra_mas_larga()
        if palabra and metrics.horizontalAdvance(palabra) > ancho:
            return QSize(min(base.width(), ancho), base.height())
        return base

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        alto = self.altoNecesario()
        if alto > 0:
            return QSize(base.width(), alto)
        return base

    def heightForWidth(self, ancho: int) -> int:
        alto = self.altoNecesario(ancho)
        if alto > 0:
            return alto
        return super().heightForWidth(ancho)

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._actualizar()
