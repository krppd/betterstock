from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    PasswordLineEdit,
    PrimaryPushButton,
    PushButton,
    qconfig,
)

from services.autenticacion import Autenticacion
from ui.fluent import CLARO, OSCURO, color
from views.ventana_base import VentanaBase


def _tinta(nombre: str) -> tuple[QColor, QColor]:
    """Devuelve el par (claro, oscuro) de un token Fluent para labels adaptativos."""
    return QColor(CLARO[nombre]), QColor(OSCURO[nombre])


class DialogoCambiarPassword(QDialog, VentanaBase):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._datos: tuple[str, str] = ("", "")
        self.setWindowTitle("Cambiar contraseña")
        self.setObjectName("dlgCambiarPassword")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addLayout(self._armar_formulario())
        layout.addStretch(1)
        layout.addLayout(self._armar_botones())
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self._aplicar_tema()
        qconfig.themeChanged.connect(self._aplicar_tema)

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema Fluent."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}")

    def _armar_formulario(self) -> QFormLayout:
        formulario = QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.setVerticalSpacing(10)
        formulario.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        formulario.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.txtActual = PasswordLineEdit(self)
        self.txtActual.setObjectName("txtActual")
        formulario.addRow(BodyLabel("Contraseña actual:", self), self.txtActual)

        self.txtPassword = PasswordLineEdit(self)
        self.txtPassword.setObjectName("txtPassword")
        formulario.addRow(BodyLabel("Contraseña nueva:", self), self.txtPassword)

        self.txtRepetir = PasswordLineEdit(self)
        self.txtRepetir.setObjectName("txtRepetir")
        formulario.addRow(BodyLabel("Repetir contraseña:", self), self.txtRepetir)
        return formulario

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnGuardar = PrimaryPushButton("Cambiar", self)
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
