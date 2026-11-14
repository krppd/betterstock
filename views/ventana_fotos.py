from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    FluentIcon as FIF,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    ToolButton,
    qconfig,
)

from services.fotos import (
    MAX_RESULTADOS,
    Candidata,
    ErrorFoto,
    ProveedorFotos,
    ProveedorOpenFoodFacts,
    descargar_bytes,
    guardar_bytes,
)
from services.preferencias import fotos_en_linea
from ui.fluent import color
from views.ventana_base import VentanaBase

MENSAJE_BUSQUEDA_APAGADA = (
    "La búsqueda de fotos en internet está apagada. Activala en Ajustes "
    "si querés que BetterStock consulte Open Food Facts."
)


class _BotonFoto(ToolButton):
    """Botón de la grilla que muestra la miniatura de una foto candidata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("botonFoto")
        self.setFixedSize(110, 110)
        self.setIconSize(QSize(96, 96))
        self.setEnabled(False)


class _UiFotos:
    """Interfaz Fluent del buscador de fotos.

    Conserva los nombres de widget heredados (``btnFotos``, ``lblVista``…) para
    no romper el código que los consulta.
    """

    def __init__(self, ventana: QDialog) -> None:
        self.txtBuscar = SearchLineEdit(ventana)
        self.txtBuscar.setObjectName("txtBuscar")
        self.txtBuscar.setPlaceholderText("Nombre o código del producto")

        self.btnBuscar = PrimaryPushButton(FIF.SEARCH, "Buscar", ventana)
        self.btnBuscar.setObjectName("btnBuscar")

        self.lblEstado = BodyLabel("", ventana)
        self.lblEstado.setObjectName("lblEstado")
        self.lblEstado.setWordWrap(True)

        self.grdFotos = QGridLayout()
        self.grdFotos.setObjectName("grdFotos")
        self.grdFotos.setSpacing(8)
        self.btnFotos: list[_BotonFoto] = []
        for indice in range(6):
            boton = _BotonFoto(ventana)
            boton.setObjectName(f"btnFoto{indice}")
            self.grdFotos.addWidget(boton, indice // 2, indice % 2)
            self.btnFotos.append(boton)

        self.lblVista = QLabel(ventana)
        self.lblVista.setObjectName("lblVista")
        self.lblVista.setMinimumSize(250, 250)
        self.lblVista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblVista.setText("Sin vista previa")

        self.lblTitulo = BodyLabel("", ventana)
        self.lblTitulo.setObjectName("lblTitulo")
        self.lblTitulo.setWordWrap(True)

        self.txtUrl = LineEdit(ventana)
        self.txtUrl.setObjectName("txtUrl")
        self.txtUrl.setPlaceholderText("…o pegá la URL de una imagen")

        self.btnUrl = PushButton(FIF.LINK, "Usar URL", ventana)
        self.btnUrl.setObjectName("btnUrl")

        self.btnGuardar = PrimaryPushButton(FIF.SAVE, "Guardar foto", ventana)
        self.btnGuardar.setObjectName("btnGuardar")
        self.btnGuardar.setEnabled(False)

        self.btnCancelar = PushButton(FIF.CANCEL, "Cancelar", ventana)
        self.btnCancelar.setObjectName("btnCancelar")

        self.verticalLayout = QVBoxLayout(ventana)
        self.verticalLayout.setContentsMargins(16, 16, 16, 16)
        self.verticalLayout.setSpacing(10)

        self.hlyBuscar = QHBoxLayout()
        self.hlyBuscar.addWidget(self.txtBuscar, 1)
        self.hlyBuscar.addWidget(self.btnBuscar)

        self.hlyMedio = QHBoxLayout()
        self.hlyMedio.setSpacing(12)
        self.hlyMedio.addLayout(self.grdFotos)

        self.vlyVista = QVBoxLayout()
        self.vlyVista.setSpacing(6)
        self.vlyVista.addWidget(self.lblVista)
        self.vlyVista.addWidget(self.lblTitulo)
        self.vlyVista.addStretch(1)
        self.hlyMedio.addLayout(self.vlyVista, 1)

        self.hlyUrl = QHBoxLayout()
        self.hlyUrl.addWidget(self.txtUrl, 1)
        self.hlyUrl.addWidget(self.btnUrl)

        self.hlyBotones = QHBoxLayout()
        self.hlyBotones.addStretch(1)
        self.hlyBotones.addWidget(self.btnGuardar)
        self.hlyBotones.addWidget(self.btnCancelar)

        self.verticalLayout.addLayout(self.hlyBuscar)
        self.verticalLayout.addWidget(self.lblEstado)
        self.verticalLayout.addLayout(self.hlyMedio, 1)
        self.verticalLayout.addLayout(self.hlyUrl)
        self.verticalLayout.addLayout(self.hlyBotones)

        self._aplicar_temas()

    def _aplicar_temas(self) -> None:
        """Pinta el marco de la vista previa con los colores del tema activo."""
        self.lblVista.setStyleSheet(
            f"border: 1px solid {color('borde')};"
            f" background-color: {color('fondo_suave')};"
            f" color: {color('texto_suave')};"
            " border-radius: 8px;")


class VentanaFotos(QDialog, VentanaBase):
    """Buscador de fotos por nombre o código, con carga por URL."""

    def __init__(self, codigo: str, nombre: str = "",
                 proveedor: ProveedorFotos | None = None,
                 destino: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self._codigo = codigo
        self._proveedor = proveedor if proveedor is not None else ProveedorOpenFoodFacts()
        self._destino = destino
        self._candidatas: list[Candidata] = []
        self._bytes: dict[str, bytes] = {}
        self._elegida: str | None = None
        self.ruta_guardada = None
        self.ui = _UiFotos(self)
        self.setWindowTitle("Buscar Foto")
        self.setMinimumSize(640, 600)
        self.ui.txtBuscar.setText(nombre or codigo)
        self.ui.btnBuscar.clicked.connect(self.buscar)
        self.ui.txtBuscar.returnPressed.connect(self.buscar)
        self.ui.btnUrl.clicked.connect(self.usar_url)
        self.ui.txtUrl.returnPressed.connect(self.usar_url)
        self.ui.btnGuardar.clicked.connect(self.guardar)
        self.ui.btnCancelar.clicked.connect(self.reject)
        for indice, boton in enumerate(self.ui.btnFotos):
            boton.clicked.connect(lambda _=False, i=indice: self._elegir(i))
        qconfig.themeChanged.connect(self.ui._aplicar_temas)
        self._aplicar_busqueda_en_linea()

    def _aplicar_busqueda_en_linea(self) -> None:
        if fotos_en_linea():
            return
        self.ui.txtBuscar.setEnabled(False)
        self.ui.btnBuscar.setEnabled(False)
        self.ui.lblEstado.setText(MENSAJE_BUSQUEDA_APAGADA)

    def buscar(self) -> None:
        texto = self.ui.txtBuscar.text().strip()
        if not texto:
            self.ui.lblEstado.setText("Escribí un nombre o código para buscar.")
            return
        if not fotos_en_linea():
            self.ui.lblEstado.setText(MENSAJE_BUSQUEDA_APAGADA)
            return
        self.ui.lblEstado.setText("Buscando...")
        self._limpiar_vista()
        try:
            self._candidatas = self._proveedor.buscar(texto)[:MAX_RESULTADOS]
        except ErrorFoto as error:
            self.ui.lblEstado.setText(str(error))
            self._candidatas = []
            self._pintar_grilla()
            return

        if not self._candidatas:
            self.ui.lblEstado.setText("Sin resultados: pegá la URL de una imagen.")
        else:
            self.ui.lblEstado.setText("Tocá una foto para verla en grande.")
        self._pintar_grilla()

    def usar_url(self) -> None:
        url = self.ui.txtUrl.text().strip()
        if not url:
            return
        if not url.lower().startswith(("http://", "https://")):
            self.mostrar_advertencia("Foto", "Solo se admiten enlaces web que empiecen con http:// o https://.")
            return
        try:
            datos = descargar_bytes(url)
        except ErrorFoto as error:
            self.mostrar_advertencia("Foto", str(error))
            return
        self._bytes[url] = datos
        self._mostrar_previa(url, "Imagen pegada")
        self.ui.lblEstado.setText("Revisá la vista previa y guardá si es la correcta.")

    def guardar(self) -> None:
        if self._elegida is None or self._elegida not in self._bytes:
            self.mostrar_advertencia("Foto", "Elegí una foto antes de guardar.")
            return
        try:
            self.ruta_guardada = guardar_bytes(
                self._bytes[self._elegida], self._codigo, self._destino)
        except ErrorFoto as error:
            self.mostrar_advertencia("Foto", str(error))
            return
        self.accept()

    def _pintar_grilla(self) -> None:
        for indice, boton in enumerate(self.ui.btnFotos):
            if indice >= len(self._candidatas):
                boton.setText("")
                boton.setIcon(QIcon())
                boton.setEnabled(False)
                continue
            candidata = self._candidatas[indice]
            miniatura = self._miniatura_de(candidata)
            if miniatura is None:
                boton.setText("X")
                boton.setIcon(QIcon())
                boton.setEnabled(False)
                continue
            boton.setText("")
            boton.setIcon(QIcon(self._con_marco(miniatura, indice == self._indice_elegido())))
            boton.setEnabled(True)

    def _indice_elegido(self) -> int:
        if self._elegida is None:
            return -1
        for indice, candidata in enumerate(self._candidatas):
            if candidata.url_completa == self._elegida:
                return indice
        return -1

    def _con_marco(self, miniatura: QPixmap, seleccionado: bool) -> QPixmap:
        """Devuelve la miniatura con un marco de acento si está seleccionada."""
        if not seleccionado:
            return miniatura
        marcada = QPixmap(miniatura)
        painter = QPainter(marcada)
        painter.setPen(QPen(QColor(color("acento")), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(marcada.rect().adjusted(2, 2, -2, -2), 8, 8)
        painter.end()
        return marcada

    def _miniatura_de(self, candidata: Candidata) -> QPixmap | None:
        for url in (candidata.url_miniatura, candidata.url_completa):
            if not url:
                continue
            try:
                datos = self._bytes_de(url)
            except ErrorFoto:
                continue
            retrato = QPixmap()
            if retrato.loadFromData(datos):
                return retrato
        return None

    def _bytes_de(self, url: str) -> bytes:
        if url not in self._bytes:
            self._bytes[url] = descargar_bytes(url)
        return self._bytes[url]

    def _elegir(self, indice: int) -> None:
        if not 0 <= indice < len(self._candidatas):
            return
        candidata = self._candidatas[indice]
        try:
            self._bytes_de(candidata.url_completa)
        except ErrorFoto as error:
            self.mostrar_advertencia("Foto", str(error))
            return
        self._mostrar_previa(candidata.url_completa, candidata.titulo)

    def _mostrar_previa(self, url: str, titulo: str) -> None:
        retrato = QPixmap()
        retrato.loadFromData(self._bytes[url])
        self.ui.lblVista.setPixmap(retrato.scaled(
            250, 250, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self.ui.lblTitulo.setText(titulo)
        self._elegida = url
        self.ui.btnGuardar.setEnabled(True)
        self._pintar_grilla()

    def _limpiar_vista(self) -> None:
        self.ui.lblVista.setPixmap(QPixmap())
        self.ui.lblVista.setText("Sin vista previa")
        self.ui.lblTitulo.setText("")
        self._pintar_grilla()
