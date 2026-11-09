from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog

from services.fotos import (
    MAX_RESULTADOS,
    Candidata,
    ErrorFoto,
    ProveedorFotos,
    ProveedorOpenFoodFacts,
    descargar_bytes,
    guardar_bytes,
)
from ui.manual.fotos_ui import Ui_FotosForm
from views.ventana_base import VentanaBase


class VentanaFotos(QDialog, VentanaBase):
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
        self.ui = Ui_FotosForm()
        self.ui.setupUi(self)
        self.ui.txtBuscar.setText(nombre or codigo)
        self.ui.btnBuscar.clicked.connect(self.buscar)
        self.ui.txtBuscar.returnPressed.connect(self.buscar)
        self.ui.btnUrl.clicked.connect(self.usar_url)
        self.ui.btnGuardar.clicked.connect(self.guardar)
        self.ui.btnCancelar.clicked.connect(self.reject)
        for indice, boton in enumerate(self.ui.btnFotos):
            boton.clicked.connect(lambda _=False, i=indice: self._elegir(i))

    def buscar(self) -> None:
        texto = self.ui.txtBuscar.text().strip()
        self._candidatas = []
        self._elegida = None
        self.ui.btnGuardar.setEnabled(False)
        self._limpiar_vista()
        if not texto:
            self.ui.lblEstado.setText("Escribí un nombre o código para buscar.")
            return
        self.ui.lblEstado.setText("Buscando...")
        try:
            self._candidatas = self._proveedor.buscar(texto)[:MAX_RESULTADOS]
        except ErrorFoto as error:
            self.ui.lblEstado.setText(str(error))
            self._pintar_grilla()
            return
        self._pintar_grilla()
        if not self._candidatas:
            self.ui.lblEstado.setText("Sin resultados: pegá la URL de una imagen.")
        else:
            self.ui.lblEstado.setText("Tocá una foto para verla en grande.")

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
        self._mostrar(url, "Imagen pegada")
        self.ui.lblEstado.setText("Revisá la vista previa y guardá si es la correcta.")

    def guardar(self) -> None:
        if self._elegida is None or self._elegida not in self._bytes:
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
                boton.setIcon(QIcon())
                boton.setText("")
                boton.setEnabled(False)
                continue
            candidata = self._candidatas[indice]
            miniatura = self._miniatura_de(candidata)
            if miniatura is None:
                boton.setIcon(QIcon())
                boton.setText("X")
                boton.setEnabled(False)
                continue
            boton.setText("")
            boton.setIcon(QIcon(miniatura))
            boton.setEnabled(True)

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
        self._mostrar(candidata.url_completa, candidata.titulo)

    def _mostrar(self, url: str, titulo: str) -> None:
        retrato = QPixmap()
        retrato.loadFromData(self._bytes[url])
        self.ui.lblVista.setPixmap(retrato.scaled(
            250, 250, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self.ui.lblTitulo.setText(titulo)
        self._elegida = url
        self.ui.btnGuardar.setEnabled(True)
        for indice, boton in enumerate(self.ui.btnFotos):
            boton.setFlat(boton.isEnabled() and self._es_elegido(indice, url))

    def _es_elegido(self, indice: int, url: str) -> bool:
        return indice < len(self._candidatas) and self._candidatas[indice].url_completa == url

    def _limpiar_vista(self) -> None:
        self.ui.lblVista.setPixmap(QPixmap())
        self.ui.lblVista.setText("Sin vista previa")
        self.ui.lblTitulo.setText("")
        for boton in self.ui.btnFotos:
            boton.setFlat(False)
