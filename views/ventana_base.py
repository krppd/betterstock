from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from PyQt6.QtCore import pyqtBoundSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (QAbstractItemView, QFileDialog, QHeaderView, QMessageBox, QTableWidget, QTableWidgetItem, QWidget)

from config import OUTPUT_DIR
from ui.estilos import TAMANO_SMALL, fuente

NUMERO = re.compile(r"^[^0-9]*-?[0-9][0-9.,]*\s*%?$")


def es_numerico(texto: str) -> bool:
    limpio = str(texto).strip()
    if not limpio:
        return False
    return bool(NUMERO.match(limpio))


class VentanaBase:
    def mostrar_advertencia(self, titulo: str, mensaje: str) -> None:
        QMessageBox.warning(self._como_widget(), titulo, mensaje)

    def mostrar_informacion(self, titulo: str, mensaje: str) -> None:
        QMessageBox.information(self._como_widget(), titulo, mensaje)

    def confirmar(self, titulo: str, pregunta: str) -> bool:
        respuesta = QMessageBox.question(
            self._como_widget(), titulo, pregunta,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return respuesta == QMessageBox.StandardButton.Yes

    def elegir(self, titulo: str, mensaje: str, opciones: Sequence[tuple[str, str, str]]) -> str:
        roles = {
            "aceptar": QMessageBox.ButtonRole.AcceptRole,
            "rechazar": QMessageBox.ButtonRole.RejectRole,
            "destructivo": QMessageBox.ButtonRole.DestructiveRole,
            "ayuda": QMessageBox.ButtonRole.HelpRole,
        }

        dialogo = QMessageBox(self._como_widget())
        dialogo.setWindowTitle(titulo)
        dialogo.setText(mensaje)
        dialogo.setIcon(QMessageBox.Icon.Warning)
        for clave, etiqueta, rol in opciones:
            dialogo.addButton(etiqueta, roles[rol])

        dialogo.exec()
        elegido = dialogo.clickedButton()
        for clave, etiqueta, _ in opciones:
            if elegido is not None and elegido.text() == etiqueta:
                return clave
        return opciones[0][0]

    @staticmethod
    def reconectar(senal: pyqtBoundSignal, receptor: Callable[[], None]) -> None:
        try:
            senal.disconnect()
        except TypeError:
            pass
        senal.connect(receptor)

    @staticmethod
    def estirar_columnas(tabla: QTableWidget) -> None:
        """Hace que las columnas de ``tabla`` se repartan todo el ancho disponible."""
        tabla.setAlternatingRowColors(True)
        encabezado = tabla.horizontalHeader()
        encabezado.setStretchLastSection(False)
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    @staticmethod
    def llenar_tabla(
        tabla: QTableWidget, filas: Sequence[Sequence[str]], colores: Sequence[str | None] | None = None
    ) -> None:
        fuente_normal = fuente(TAMANO_SMALL)
        fuente_tabular = fuente(TAMANO_SMALL, tabular=True)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setUpdatesEnabled(False)
        tabla.blockSignals(True)
        try:
            tabla.setRowCount(len(filas))
            for indice_fila, valores in enumerate(filas):
                color = colores[indice_fila] if colores else None
                for indice_columna, valor in enumerate(valores):
                    item = QTableWidgetItem(valor)
                    item.setFont(fuente_tabular if es_numerico(valor) else fuente_normal)
                    if color:
                        item.setForeground(QBrush(QColor(color)))
                    tabla.setItem(indice_fila, indice_columna, item)
        finally:
            tabla.blockSignals(False)
            tabla.setUpdatesEnabled(True)

    def _como_widget(self) -> QWidget:
        assert isinstance(self, QWidget), "VentanaBase debe combinarse con una clase de Qt"
        return self
