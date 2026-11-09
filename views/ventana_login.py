from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QCheckBox, QDialog

from config import RECURSOS_DIR
from services import preferencias
from services.autenticacion import Autenticacion
from ui.estilos import ROJO_TEXTO, VERDE
from ui.generated.login_ui import Ui_Dialog as Ui_LoginForm
from views.ventana_base import VentanaBase


class VentanaLogin(QDialog, VentanaBase):
    ANCHO_LOGO = 300
    ALTO_LOGO = 150
    ANCHO_CUADRO = 574
    ALTO_CUADRO = 287
    COLUMNAS_TIRA = 8
    CUADROS_TIRA = 60
    INTERVALO_LOGO_MS = 30
    ESPERA_INGRESO_MS = 1300
    ANCHO_FIJO = 400
    MARGEN_VERTICAL = 20
    TEXTO_MODO_TACTIL = "Modo táctil"

    def __init__(self, autenticacion: Autenticacion) -> None:
        super().__init__()
        self._autenticacion = autenticacion
        self.ui = Ui_LoginForm()
        self.ui.setupUi(self)
        tira = QPixmap(str(RECURSOS_DIR / "anim_logo_tira.png"))
        self._cuadros_logo = [
            tira.copy(
                (numero % self.COLUMNAS_TIRA) * self.ANCHO_CUADRO,
                (numero // self.COLUMNAS_TIRA) * self.ALTO_CUADRO,
                self.ANCHO_CUADRO, self.ALTO_CUADRO,
            ).scaled(
                self.ANCHO_LOGO, self.ALTO_LOGO,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            for numero in range(self.CUADROS_TIRA)
        ]
        self._cuadro_logo = 0
        self.ui.lblLogo.setPixmap(self._cuadros_logo[0])
        self._temporizador_logo = QTimer(self)
        self._temporizador_logo.setInterval(self.INTERVALO_LOGO_MS)
        self._temporizador_logo.timeout.connect(self._avanzar_logo)
        self._temporizador_logo.start()
        self.ui.btnIngresar.clicked.connect(self.validar_login)
        self.ui.btnIngresar.setAutoDefault(False)
        self.ui.btnIngresar.setDefault(False)
        self.ui.txtUsuario.returnPressed.connect(self.ui.txtPassword.setFocus)
        self.ui.txtPassword.returnPressed.connect(self.validar_login)
        self.setTabOrder(self.ui.txtUsuario, self.ui.txtPassword)
        self.setTabOrder(self.ui.txtPassword, self.ui.btnIngresar)
        self.ui.lblError.setStyleSheet(f"color: {ROJO_TEXTO};")
        self.ui.lblError.setText("")
        self._armar_modo_tactil()
        self._ingresando = False

    def _armar_modo_tactil(self) -> None:
        self.chkModoTactil = QCheckBox(self.TEXTO_MODO_TACTIL, self.ui.layoutWidget)
        self.chkModoTactil.setObjectName("chkModoTactil")
        self.chkModoTactil.setStyleSheet(
            "QCheckBox::indicator {"
            "  width: 18px; height: 18px;"
            "  border: 1px solid #CFCFCF; border-radius: 4px;"
            "  background: #FFFFFF;"
            "}"
            "QCheckBox::indicator:checked {"
            "  background: #FFFFFF;"
            f"  border: 1px solid {VERDE};"
            f"  image: url(\"{(RECURSOS_DIR / 'check_verde.png').as_posix()}\");"
            "}")
        self.chkModoTactil.setChecked(preferencias.modo_tactil())
        self.chkModoTactil.toggled.connect(self._cambiar_modo_tactil)
        self.ui.gridLayout.addWidget(self.chkModoTactil, 7, 0, 1, 1)
        self.ui.gridLayout.activate()
        alto = self.ui.gridLayout.sizeHint().height()
        self.ui.layoutWidget.setGeometry(26, self.MARGEN_VERTICAL, 361, alto)
        self.setFixedSize(self.ANCHO_FIJO, self.MARGEN_VERTICAL + alto + self.MARGEN_VERTICAL)
        self.setTabOrder(self.ui.btnIngresar, self.chkModoTactil)

    def _cambiar_modo_tactil(self, activo: bool) -> None:
        preferencias.guardar_modo_tactil(activo)

    def _avanzar_logo(self) -> None:
        if self._cuadro_logo >= len(self._cuadros_logo) - 1:
            self._temporizador_logo.stop()
            return
        self._cuadro_logo += 1
        self.ui.lblLogo.setPixmap(self._cuadros_logo[self._cuadro_logo])

    def validar_login(self) -> None:
        if self._ingresando:
            return
        usuario = self.ui.txtUsuario.text().strip()
        password = self.ui.txtPassword.text().strip()

        if self._autenticacion.iniciar_sesion(usuario, password):
            self._ingresando = True
            self.ui.btnIngresar.flash("Ingresando", self.ESPERA_INGRESO_MS)
            self.ui.btnIngresar.setEnabled(False)
            self.ui.txtUsuario.setEnabled(False)
            self.ui.txtPassword.setEnabled(False)
            QTimer.singleShot(self.ESPERA_INGRESO_MS, self._entrar_si_sigue_abierto)
        else:
            self.ui.lblError.setText("Usuario o contraseña incorrectos")
            self.ui.txtPassword.clear()

    def _entrar_si_sigue_abierto(self) -> None:
        if self.isVisible():
            self.accept()
