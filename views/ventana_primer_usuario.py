from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from models.usuario import Usuario
from ui.estilos import ROJO_TEXTO, TAMANO_BODY, fuente
from services.autenticacion import Autenticacion
from views.ventana_base import VentanaBase

LARGO_MINIMO_USUARIO = 3
LARGO_MINIMO_PASSWORD = 4

TEXTO_USUARIO = "El nombre de usuario necesita al menos 3 caracteres."
TEXTO_PASSWORD = "La contraseña necesita al menos 4 caracteres."
TEXTO_REPETICION = "Las contraseñas no coinciden."
TEXTO_MENSAJE = (
    "Primer inicio de BetterStock.\n"
    "Creá el usuario principal (administrador) para gestionar el local.")


class VentanaPrimerUsuario(QDialog, VentanaBase):
    """Alta del primer usuario (administrador) en el primer arranque."""

    def __init__(self, autenticacion: Autenticacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._autenticacion = autenticacion
        self.setWindowTitle("Primer inicio — usuario principal")

        self.lblMensaje = QLabel(TEXTO_MENSAJE, self)
        self.lblMensaje.setFont(fuente(TAMANO_BODY))
        self.lblMensaje.setWordWrap(True)

        self.txtUsuario = QLineEdit(self)
        self.txtUsuario.setFont(fuente(TAMANO_BODY, tabular=True))
        self.txtUsuario.setMaxLength(40)

        self.txtPassword = QLineEdit(self)
        self.txtPassword.setFont(fuente(TAMANO_BODY, tabular=True))
        self.txtPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.txtPassword.setMaxLength(72)

        self.txtRepetir = QLineEdit(self)
        self.txtRepetir.setFont(fuente(TAMANO_BODY, tabular=True))
        self.txtRepetir.setEchoMode(QLineEdit.EchoMode.Password)
        self.txtRepetir.setMaxLength(72)

        formulario = QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.setVerticalSpacing(10)
        formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        formulario.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        formulario.addRow("Usuario:", self.txtUsuario)
        formulario.addRow("Contraseña:", self.txtPassword)
        formulario.addRow("Repetir contraseña:", self.txtRepetir)

        self.lblError = QLabel("", self)
        self.lblError.setStyleSheet(f"color: {ROJO_TEXTO};")
        self.lblError.setFont(fuente(TAMANO_BODY))

        self.botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self)
        btn_crear = self.botones.button(QDialogButtonBox.StandardButton.Ok)
        btn_crear.setText("Crear usuario")
        btn_crear.setDefault(True)
        self.botones.accepted.connect(self.crear)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(self.lblMensaje)
        layout.addLayout(formulario)
        layout.addWidget(self.lblError)
        layout.addWidget(self.botones)

        self.setFixedWidth(460)
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
