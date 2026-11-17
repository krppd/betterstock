from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QDialog
from qfluentwidgets import BodyLabel, CheckBox, qconfig

from config import RECURSOS_DIR
from services import preferencias
from services.autenticacion import Autenticacion
from ui.fluent import CLARO, OSCURO, color
from ui.generated.login_ui import Ui_Dialog as Ui_LoginForm
from views.ventana_base import VentanaBase


def _tinta(nombre: str) -> tuple[QColor, QColor]:
    """Devuelve el par (claro, oscuro) de un token Fluent para labels adaptativos."""
    return QColor(CLARO[nombre]), QColor(OSCURO[nombre])


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
    ALTO_MINIMO = 440
    MARGEN_VERTICAL = 20
    TEXTO_MODO_TACTIL = "Modo táctil"

    def __init__(self, autenticacion: Autenticacion) -> None:
        super().__init__()
        self._autenticacion = autenticacion
        self.ui = Ui_LoginForm()
        self.ui.setupUi(self)
        self._tira_logo: QPixmap | None = QPixmap(str(RECURSOS_DIR / "anim_logo_tira.png"))
        self._cuadros_logo = [self._crear_cuadro_logo(0)]
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
        self.ui.lblError.setTextColor(*_tinta("error"))
        self.ui.lblError.setText("")
        self._armar_modo_tactil()
        self._ingresando = False
        self._aplicar_tema()
        qconfig.themeChanged.connect(self._aplicar_tema)

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema Fluent."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}")

    def _armar_modo_tactil(self) -> None:
        self.chkModoTactil = CheckBox(self.TEXTO_MODO_TACTIL, self.ui.layoutWidget)
        self.chkModoTactil.setObjectName("chkModoTactil")
        self.chkModoTactil.setChecked(preferencias.modo_tactil())
        self.chkModoTactil.toggled.connect(self._cambiar_modo_tactil)
        self.ui.gridLayout.addWidget(self.chkModoTactil, 7, 0, 1, 1)
        self.ui.gridLayout.activate()
        alto = self.ui.gridLayout.sizeHint().height()
        self.ui.layoutWidget.setGeometry(26, self.MARGEN_VERTICAL, 361, alto)
        alto_ventana = self.MARGEN_VERTICAL + alto + self.MARGEN_VERTICAL
        self.setFixedSize(
            self.ANCHO_FIJO, max(alto_ventana, self.ALTO_MINIMO))
        self.setTabOrder(self.ui.btnIngresar, self.chkModoTactil)

    def _cambiar_modo_tactil(self, activo: bool) -> None:
        preferencias.guardar_modo_tactil(activo)

    def _crear_cuadro_logo(self, numero: int) -> QPixmap:
        tira = self._tira_logo
        if tira is None:
            return QPixmap()
        return tira.copy(
            (numero % self.COLUMNAS_TIRA) * self.ANCHO_CUADRO,
            (numero // self.COLUMNAS_TIRA) * self.ALTO_CUADRO,
            self.ANCHO_CUADRO, self.ALTO_CUADRO,
        ).scaled(
            self.ANCHO_LOGO, self.ALTO_LOGO,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _avanzar_logo(self) -> None:
        if self._cuadro_logo >= self.CUADROS_TIRA - 1:
            self._temporizador_logo.stop()
            self._tira_logo = None
            return
        self._cuadro_logo += 1
        self._cuadros_logo.append(self._crear_cuadro_logo(self._cuadro_logo))
        self.ui.lblLogo.setPixmap(self._cuadros_logo[self._cuadro_logo])
        if self._cuadro_logo == self.CUADROS_TIRA - 1:
            self._tira_logo = None

    def validar_login(self) -> None:
        if self._ingresando:
            return
        usuario = self.ui.txtUsuario.text().strip()
        password = self.ui.txtPassword.text().strip()

        if self._autenticacion.iniciar_sesion(usuario, password):
            self._ingresando = True
            self.ui.btnIngresar.setText("Ingresando…")
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
