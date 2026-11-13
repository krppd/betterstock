from __future__ import annotations

from PyQt6.QtCore import QElapsedTimer, QRect, QSize, Qt, QTimer
from PyQt6.QtGui import QFontMetrics, QPalette
from PyQt6.QtWidgets import QPushButton, QStyle, QStyleOptionButton, QStylePainter

from ui.estilos import alto_linea
from ui.widgets.rollo_texto import RolloTexto


class BotonRodante(QPushButton):
    INTERVALO_MS = 16

    TIEMPO_CARACTER_MS = 220

    ESCALON_MS = 30

    def __init__(self, texto: str = "", parent=None, direccion: str = "down",
                 escalon: int = ESCALON_MS) -> None:
        super().__init__(texto, parent)
        self._rollo = RolloTexto(texto, tiempo_caracter=self.TIEMPO_CARACTER_MS,
                                 escalon=escalon, rodar_todo=True,
                                 direccion=direccion)
        self._generacion = 0
        self._centrado = False
        self._reloj = QElapsedTimer()
        self._temporizador = QTimer(self)
        self._temporizador.setInterval(self.INTERVALO_MS)
        self._temporizador.timeout.connect(self._avanzar)

    def setCentrado(self, centrado: bool = True) -> None:
        self._centrado = centrado
        self.update()

    @property
    def direccion(self) -> str:
        return self._rollo.direccion

    @direccion.setter
    def direccion(self, valor: str) -> None:
        self._rollo.direccion = valor

    def setText(self, texto: str) -> None:
        self._generacion += 1
        super().setText(texto)
        self._rollo.fijar(texto)
        if self._temporizador.isActive():
            self._temporizador.stop()
        self.update()

    def mostrar(self, texto: str, direccion: str | None = None) -> None:
        self._generacion += 1
        if self._rollo.mostrar(texto, direccion=direccion):
            super().setText(texto)
            if not self._temporizador.isActive():
                self._reloj.start()
                self._temporizador.start()
            self.update()

    def repetir(self, direccion: str | None = None) -> None:
        if direccion is not None:
            self._rollo.direccion = direccion
        if not self._temporizador.isActive():
            self._reloj.start()
            self._temporizador.start()
            self.update()

    def _volver(self, previo: str, texto: str, marca: int, direccion: str | None = None) -> None:
        if marca == self._generacion and self._rollo.objetivo == texto:
            self.mostrar(previo, direccion=direccion)

    def _avanzar(self) -> None:
        if self._reloj.elapsed() >= self._rollo.duracion_total():
            self._rollo.terminar()
            self._temporizador.stop()
        self.update()

    def paintEvent(self, evento) -> None:
        opcion = QStyleOptionButton()
        self.initStyleOption(opcion)
        opcion.text = ""
        pintor = QStylePainter(self)
        pintor.drawControl(QStyle.ControlElement.CE_PushButton, opcion)
        rectangulo = self.style().subElementRect(
            QStyle.SubElement.SE_PushButtonContents, opcion, self)
        pintor.setClipRect(rectangulo)
        pintor.setFont(self.font())
        pintor.setPen(self.palette().color(QPalette.ColorRole.ButtonText))
        metricas = QFontMetrics(self.font())
        altura = self._alto_caja(metricas)
        ancho = self._rollo.ancho_bloque(metricas)
        zona_icono = 0
        if not self.icon().isNull():
            zona_icono = self.iconSize().width() + 4
        disponible = rectangulo.width() - zona_icono
        if self._centrado or self.property("centrado"):
            x = rectangulo.x() + zona_icono + max(0, (disponible - ancho) // 2)
        else:
            x = rectangulo.x() + zona_icono + 8
        base_y = rectangulo.y() + (rectangulo.height() - altura) // 2 + metricas.ascent()
        celda = QRect(x, base_y - metricas.ascent(), ancho, altura)
        pintor.setClipRect(celda.intersected(rectangulo))
        if self._temporizador.isActive():
            self._rollo.dibujar(pintor, metricas, x, base_y, altura, self._reloj.elapsed())
        else:
            self._rollo.dibujar(pintor, metricas, x, base_y, altura, None)

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        metricas = QFontMetrics(self.font())
        ancho = self._rollo.ancho_bloque(metricas)
        zona_icono = (self.iconSize().width() + 4) if not self.icon().isNull() else 0
        return QSize(max(base.width(), ancho + zona_icono + 28), max(base.height(), metricas.height() + 10))

    def _alto_caja(self, metricas: QFontMetrics) -> int:
        punto = self.font().pointSize()
        if punto <= 0:
            return metricas.height()
        return max(metricas.height(), alto_linea(punto))
