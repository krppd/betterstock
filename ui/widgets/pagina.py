from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.estilos import TAMANO_BODY, TAMANO_MICRO, TAMANO_TITLE, escala, fuente


def _px(valor: int) -> int:
    return round(valor * escala())


class CabeceraPagina(QWidget):
    def __init__(self, titulo: str, subtitulo: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("encabezadoPagina")
        fila = QHBoxLayout(self)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(_px(12))

        textos = QVBoxLayout()
        textos.setContentsMargins(0, 0, 0, 0)
        textos.setSpacing(_px(2))
        self.titulo = QLabel(titulo, self)
        self.titulo.setObjectName("tituloPagina")
        self.titulo.setFont(fuente(TAMANO_TITLE, negrita=True))
        self.subtitulo = QLabel(subtitulo, self)
        self.subtitulo.setObjectName("subtituloPagina")
        self.subtitulo.setFont(fuente(TAMANO_BODY))
        self.subtitulo.setVisible(bool(subtitulo))
        textos.addWidget(self.titulo)
        textos.addWidget(self.subtitulo)

        self.acciones = QHBoxLayout()
        self.acciones.setContentsMargins(0, 0, 0, 0)
        self.acciones.setSpacing(_px(8))

        fila.addLayout(textos)
        fila.addStretch(1)
        fila.addLayout(self.acciones)


class Tarjeta(QFrame):
    def __init__(self, titulo: str = "", subtitulo: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.cuerpo = QVBoxLayout(self)
        self.cuerpo.setContentsMargins(_px(16), _px(14), _px(16), _px(14))
        self.cuerpo.setSpacing(_px(10))
        self.acciones = QHBoxLayout()
        self.acciones.setContentsMargins(0, 0, 0, 0)
        self.acciones.setSpacing(_px(8))
        if titulo:
            cabecera = QHBoxLayout()
            cabecera.setContentsMargins(0, 0, 0, 0)
            cabecera.setSpacing(_px(8))
            textos = QVBoxLayout()
            textos.setContentsMargins(0, 0, 0, 0)
            textos.setSpacing(_px(1))
            etiqueta = QLabel(titulo, self)
            etiqueta.setObjectName("tituloTarjeta")
            etiqueta.setFont(fuente(TAMANO_BODY, negrita=True))
            textos.addWidget(etiqueta)
            if subtitulo:
                detalle = QLabel(subtitulo, self)
                detalle.setObjectName("subtituloTarjeta")
                detalle.setFont(fuente(TAMANO_MICRO))
                textos.addWidget(detalle)
            cabecera.addLayout(textos)
            cabecera.addStretch(1)
            cabecera.addLayout(self.acciones)
            self.cuerpo.addLayout(cabecera)

    def agregar(self, widget: QWidget, estirar: int = 0) -> None:
        self.cuerpo.addWidget(widget, estirar)


class Segmentado(QFrame):
    cambiado = pyqtSignal(int)

    def __init__(self, opciones: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("segmentado")
        fila = QHBoxLayout(self)
        fila.setContentsMargins(_px(3), _px(3), _px(3), _px(3))
        fila.setSpacing(_px(2))
        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        self._botones: list[QPushButton] = []
        for indice, texto in enumerate(opciones):
            boton = QPushButton(texto, self)
            boton.setObjectName("segmento")
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setMinimumHeight(_px(32))
            boton.setFont(fuente(TAMANO_MICRO, negrita=True))
            self._grupo.addButton(boton, indice)
            fila.addWidget(boton)
            self._botones.append(boton)
        self._grupo.idClicked.connect(self.cambiado.emit)
        if self._botones:
            self._botones[0].setChecked(True)

    @property
    def botones(self) -> list[QPushButton]:
        return list(self._botones)

    def set_opciones(self, opciones: list[str]) -> None:
        self._grupo.blockSignals(True)
        for boton in self._botones:
            self._grupo.removeButton(boton)
            self.layout().removeWidget(boton)
            boton.setParent(None)
            boton.deleteLater()
        self._botones.clear()
        for indice, texto in enumerate(opciones):
            boton = QPushButton(texto, self)
            boton.setObjectName("segmento")
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setMinimumHeight(_px(32))
            boton.setFont(fuente(TAMANO_MICRO, negrita=True))
            self._grupo.addButton(boton, indice)
            self.layout().addWidget(boton)
            self._botones.append(boton)
        self._grupo.blockSignals(False)
        if self._botones:
            self._botones[0].setChecked(True)

    def marcar(self, indice: int) -> None:
        if 0 <= indice < len(self._botones):
            self._botones[indice].setChecked(True)
