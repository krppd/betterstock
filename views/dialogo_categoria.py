"""Diálogo para dar de alta una categoría."""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLayout, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, LineEdit, PrimaryPushButton, PushButton

from services.excepciones import ErrorNegocio
from services.gestor_stock import GestorStock
from ui.fluent import color
from views.ventana_base import VentanaBase


class DialogoCategoria(QDialog, VentanaBase):
    """Pide el nombre de una categoría nueva y la guarda; se cierra aceptado solo si se guardó."""

    def __init__(self, gestor_stock: GestorStock, parent: QWidget | None = None) -> None:
        """Crea el diálogo usando el servicio recibido."""
        super().__init__(parent)
        self._gestor_stock = gestor_stock
        self._nombre = ""
        self.setWindowTitle("Nueva categoría")
        self.setObjectName("dlgNuevaCategoria")
        self._aplicar_tema()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addLayout(self._armar_formulario())
        layout.addStretch(1)
        layout.addLayout(self._armar_botones())
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema claro/oscuro."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}"
        )

    def _armar_formulario(self) -> QFormLayout:
        formulario = QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.setVerticalSpacing(10)
        self.txtNombre = LineEdit(self)
        self.txtNombre.setObjectName("txtNombreCategoria")
        self.txtNombre.setPlaceholderText("Nombre de la categoría")
        formulario.addRow(BodyLabel("Nombre:", self), self.txtNombre)
        return formulario

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnGuardar = PrimaryPushButton("Guardar", self)
        self.btnCancelar.setAutoDefault(False)
        self.btnGuardar.setDefault(True)
        botones.addStretch(1)
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
