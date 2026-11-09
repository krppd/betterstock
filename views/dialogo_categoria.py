"""Diálogo para dar de alta una categoría."""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from services.excepciones import ErrorNegocio
from services.gestor_stock import GestorStock
from views.ventana_base import VentanaBase


class DialogoCategoria(QDialog, VentanaBase):
    """Pide el nombre de una categoría nueva y la guarda; se cierra aceptado solo si se guardó."""

    def __init__(self, gestor_stock: GestorStock, parent: QWidget | None = None) -> None:
        """Crea el diálogo usando el servicio recibido."""
        super().__init__(parent)
        self._gestor_stock = gestor_stock
        self._nombre = ""
        self.setWindowTitle("Nueva categoría")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(self._armar_formulario())
        layout.addStretch(1)
        layout.addLayout(self._armar_botones())
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def _armar_formulario(self) -> QFormLayout:
        formulario = QFormLayout()
        self.txtNombre = QLineEdit(self)
        formulario.addRow("Nombre:", self.txtNombre)
        return formulario

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        self.btnCancelar = QPushButton("Cancelar", self)
        self.btnGuardar = QPushButton("Guardar", self)
        self.btnCancelar.setAutoDefault(False)
        self.btnGuardar.setDefault(True)
        botones.addWidget(self.btnCancelar)
        botones.addWidget(self.btnGuardar)

        self.btnCancelar.clicked.connect(self.reject)
        self.btnGuardar.clicked.connect(self.guardar)
        return botones

    @property
    def nombre(self) -> str:
        """Nombre de la categoría guardada (vacío si todavía no se guardó ninguna)."""
        return self._nombre

    def guardar(self) -> None:
        """Valida y guarda la categoría; si todo sale bien cierra el diálogo."""
        try:
            self._nombre = self._gestor_stock.agregar_categoria(self.txtNombre.text())
        except ErrorNegocio as error:
            self.mostrar_advertencia("Error", str(error))
            self.txtNombre.setFocus()
            return

        self.accept()
