from __future__ import annotations

from PyQt6.QtCore import QElapsedTimer, QRect, QSize, Qt, QTimer
from PyQt6.QtGui import QFontMetrics, QPainter, QPalette
from PyQt6.QtWidgets import QWidget

from ui.estilos import alto_linea
from ui.widgets.rollo_texto import RolloTexto


class EtiquetaRodante(QWidget):
    INTERVALO_MS = 16

    def __init__(self, texto: str = "",
                 alineacion: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
                 parent=None) -> None:
        super().__init__(parent)
        self._rollo = RolloTexto(texto)
        self._alineacion = alineacion
        self._reloj = QElapsedTimer()
        self._temporizador = QTimer(self)
        self._temporizador.setInterval(self.INTERVALO_MS)
        self._temporizador.timeout.connect(self._avanzar)
        self._fijo: QSize | None = None

    def text(self) -> str:
        return self._rollo.objetivo

    def setText(self, texto: str) -> None:
        self._rollo.fijar(texto)
        if self._temporizador.isActive():
            self._temporizador.stop()
        self._fijo = None
        self.updateGeometry()
        self.update()

    def setAlignment(self, alineacion: Qt.AlignmentFlag) -> None:
        self._alineacion = alineacion
        self.update()

    def mostrar(self, texto: str, direccion: str | None = None) -> None:
        if self._temporizador.isActive():
            if self._rollo.mostrar(texto, direccion=direccion):
                self.update()
            return
        anterior = QFontMetrics(self.font()).boundingRect(self._rollo.objetivo or " ").size()
        if self._rollo.mostrar(texto, direccion=direccion):
            self._fijo = anterior
            self._reloj.start()
            self._temporizador.start()
            self.update()

    def sizeHint(self) -> QSize:
        if self._fijo is not None and self._temporizador.isActive():
            return self._fijo
        metricas = QFontMetrics(self.font())
        return metricas.boundingRect(self._rollo.objetivo or " ").size()

    def _avanzar(self) -> None:
        if self._reloj.elapsed() >= self._rollo.duracion_total():
            self._rollo.terminar()
            self._temporizador.stop()
            self._fijo = None
            self.updateGeometry()
        self.update()

    def paintEvent(self, evento) -> None:
        pintor = QPainter(self)
        pintor.setFont(self.font())
        pintor.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        metricas = QFontMetrics(self.font())
        altura = self._alto_caja(metricas)
        base_y = (self.height() - altura) // 2 + metricas.ascent()
        ancho = self._rollo.ancho_bloque(metricas)
        x = self._x_bloque(ancho)
        pintor.setClipRect(QRect(x, base_y - metricas.ascent(), ancho, altura).intersected(self.rect()))
        if self._temporizador.isActive():
            self._rollo.dibujar(pintor, metricas, x, base_y, altura, self._reloj.elapsed())
        else:
            self._rollo.dibujar(pintor, metricas, x, base_y, altura, None)

    def _alto_caja(self, metricas: QFontMetrics) -> int:
        punto = self.font().pointSize()
        if punto <= 0:
            return metricas.height()
        return max(metricas.height(), alto_linea(punto))

    def _x_bloque(self, ancho: int) -> int:
        if self._alineacion & Qt.AlignmentFlag.AlignHCenter:
            return (self.width() - ancho) // 2
        if self._alineacion & Qt.AlignmentFlag.AlignRight:
            return self.width() - ancho
        return 0
