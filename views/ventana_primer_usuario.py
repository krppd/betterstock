from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    PasswordLineEdit,
    PrimaryPushButton,
    PushButton,
)

from models.usuario import Usuario
from services.autenticacion import Autenticacion
from ui.fluent import CLARO, OSCURO
from views.ventana_base import VentanaBase

LARGO_MINIMO_USUARIO = 3
LARGO_MINIMO_PASSWORD = 4

TEXTO_USUARIO = "El nombre de usuario necesita al menos 3 caracteres."
TEXTO_PASSWORD = "La contraseña necesita al menos 4 caracteres."  # NOSONAR
TEXTO_REPETICION = "Las contraseñas no coinciden."
TEXTO_MENSAJE = (
    "Primer inicio de BetterStock.\n"
    "Creá el usuario principal (administrador) para gestionar el local.")


def _tinta(nombre: str) -> tuple[QColor, QColor]:
    """Devuelve el par (claro, oscuro) de un token Fluent para labels adaptativos."""
    return QColor(CLARO[nombre]), QColor(OSCURO[nombre])


class VentanaPrimerUsuario(QDialog, VentanaBase):
    """Alta del primer usuario (administrador) en el primer arranque."""

    def __init__(self, autenticacion: Autenticacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._autenticacion = autenticacion
        self.setWindowTitle("Primer inicio — usuario principal")
        self.setObjectName("dlgPrimerUsuario")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.lblMensaje = BodyLabel(TEXTO_MENSAJE, self)
        self.lblMensaje.setWordWrap(True)
        layout.addWidget(self.lblMensaje)

        formulario = QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.setVerticalSpacing(10)
        formulario.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        formulario.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.txtUsuario = LineEdit(self)
        self.txtUsuario.setMaxLength(40)
        self.txtUsuario.setPlaceholderText("Por ejemplo: dueno")
        formulario.addRow(BodyLabel("Usuario:", self), self.txtUsuario)

        self.txtPassword = PasswordLineEdit(self)
        self.txtPassword.setMaxLength(72)
        formulario.addRow(BodyLabel("Contraseña:", self), self.txtPassword)

        self.txtRepetir = PasswordLineEdit(self)
        self.txtRepetir.setMaxLength(72)
        formulario.addRow(BodyLabel("Repetir contraseña:", self), self.txtRepetir)

        layout.addLayout(formulario)

        self.lblError = BodyLabel("", self)
        self.lblError.setWordWrap(True)
        self.lblError.setTextColor(*_tinta("error"))
        layout.addWidget(self.lblError)

        botones = QHBoxLayout()
        botones.addStretch(1)

        self.btnCancelar = PushButton("Cancelar", self)
        self.btnCancelar.setAutoDefault(False)
        self.btnCancelar.clicked.connect(self.reject)
        botones.addWidget(self.btnCancelar)

        self.btnCrear = PrimaryPushButton("Crear usuario", self)
        self.btnCrear.setDefault(True)
        self.btnCrear.clicked.connect(self.crear)
        botones.addWidget(self.btnCrear)

        layout.addLayout(botones)

        self.txtUsuario.returnPressed.connect(self.txtPassword.setFocus)
        self.txtPassword.returnPressed.connect(self.txtRepetir.setFocus)
        self.txtRepetir.returnPressed.connect(self.crear)
        self.txtUsuario.setFocus()

    def crear(self) -> None:
        nombre = self.txtUsuario.text().strip().lower()
        password = self.txtPassword.text()
        if len(nombre) < LARGO_MINIMO_USUARIO:
            self.lblError.setText(TEXTO_USUARIO)
            self.txtUsuario.setFocus()
            return
        if len(password) < LARGO_MINIMO_PASSWORD:
            self.lblError.setText(TEXTO_PASSWORD)
            self.txtPassword.setFocus()
            return
        if password != self.txtRepetir.text():
            self.lblError.setText(TEXTO_REPETICION)
            self.txtRepetir.setFocus()
            return
        try:
            self._autenticacion.crear_usuario(nombre, password, Usuario.PERMISO_ADMIN)
        except ValueError as error:
            self.lblError.setText(str(error))
            self.txtUsuario.setFocus()
            return
        self.accept()
