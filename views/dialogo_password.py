from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.autenticacion import Autenticacion
from views.ventana_base import VentanaBase


class DialogoCambiarPassword(QDialog, VentanaBase):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._datos: tuple[str, str] = ("", "")
        self.setWindowTitle("Cambiar contraseña")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(self._armar_formulario())
        layout.addStretch(1)
        layout.addLayout(self._armar_botones())
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def _armar_formulario(self) -> QFormLayout:
        formulario = QFormLayout()
        self.txtActual = QLineEdit(self)
        self.txtActual.setEchoMode(QLineEdit.EchoMode.Password)
        formulario.addRow("Contraseña actual:", self.txtActual)

        self.txtPassword = QLineEdit(self)
        self.txtPassword.setEchoMode(QLineEdit.EchoMode.Password)
        formulario.addRow("Contraseña nueva:", self.txtPassword)

        self.txtRepetir = QLineEdit(self)
        self.txtRepetir.setEchoMode(QLineEdit.EchoMode.Password)
        formulario.addRow("Repetir contraseña:", self.txtRepetir)
        return formulario

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        self.btnCancelar = QPushButton("Cancelar", self)
        self.btnGuardar = QPushButton("Cambiar", self)
        self.btnCancelar.setAutoDefault(False)
        self.btnGuardar.setDefault(True)
        botones.addWidget(self.btnCancelar)
        botones.addStretch(1)
        botones.addWidget(self.btnGuardar)
        self.btnCancelar.clicked.connect(self.reject)
        self.btnGuardar.clicked.connect(self.guardar)
        return botones

    @property
    def datos(self) -> tuple[str, str]:
        return self._datos

    def guardar(self) -> None:
        actual = self.txtActual.text()
        nueva = self.txtPassword.text()
        repetir = self.txtRepetir.text()
        if not actual:
            self.mostrar_advertencia(
                "Cambiar contraseña", "Ingresá la contraseña actual.")
            self.txtActual.setFocus()
            return
        if len(nueva) < Autenticacion.LARGO_MINIMO_PASSWORD:
            self.mostrar_advertencia(
                "Cambiar contraseña",
                "La contraseña debe tener al menos "
                f"{Autenticacion.LARGO_MINIMO_PASSWORD} caracteres.")
            self.txtPassword.setFocus()
            return
        if nueva != repetir:
            self.mostrar_advertencia(
                "Cambiar contraseña", "Las contraseñas no coinciden.")
            self.txtRepetir.setFocus()
            return
        self._datos = (actual, nueva)
        self.accept()
