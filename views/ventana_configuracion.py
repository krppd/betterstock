from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from models.usuario import Usuario
from models.validacion_identificador import (
    es_cuit_valido,
    normalizar_cuit,
    tipo_de_identificador,
)
from services.autenticacion import Autenticacion
from services.backup import ErrorBackup, ServicioBackup, tamano_legible
from services.gestor_anulaciones import MENSAJE_SIN_SERVICIO, GestorAnulaciones
from services.gestor_comercio import GestorComercio
from services.impresion import imprimir_codigo_anulacion
from config import RECURSOS_DIR
from services.plan_motor import CONTACTO, texto_limites
from services.preferencias import (
    guardar_posicion_menu,
    posicion_menu,
)
from ui.estilos import (
    AMBAR_TEXTO,
    GRIS_TEXTO,
    TAMANO_MICRO,
    VERDE_TEXTO,
    fuente,
)
from ui.manual.configuracion_ui import TITULO_EDICION, TITULO_INICIAL, Ui_ConfiguracionForm
from ui.widgets.notificacion import Notificacion
from ui.widgets.trabajo_impresion import TrabajoImpresion
from views.dialogo_password import DialogoCambiarPassword
from views.ventana_base import VentanaBase

MENSAJE_CONFIRMAR = "Esto reemplaza todos los datos actuales. ¿Continuar?"
SIN_CODIGO = "Todavía no generaste un código."
FUENTE_MONOESPACADA = "Monospace"
TAMANO_CODIGO = 26


class VentanaConfiguracion(QDialog, VentanaBase):
    def __init__(self, gestor_comercio: GestorComercio, backup: ServicioBackup | None = None,
                 anulaciones: GestorAnulaciones | None = None, permiso: str = "",
                 autenticacion: Autenticacion | None = None) -> None:
        super().__init__()
        self._gestor_comercio = gestor_comercio
        self._backup = backup if backup is not None else ServicioBackup()
        self._anulaciones = anulaciones
        self._permiso = permiso
        self._autenticacion = autenticacion
        self._codigo_generado = ""
        self._etiqueta_generada = ""
        self._trabajos: list[TrabajoImpresion] = []
        self._copias: list = []
        self._comercio = getattr(gestor_comercio, "comercio", None)
        self._edicion = self._comercio is not None
        self.ui = Ui_ConfiguracionForm()
        self.ui.setupUi(self)
        self.ui.btnGuardar.clicked.connect(self.guardar)
        self.ui.lblError.setText("")
        self.ui.lblCuit.setToolTip(
            "CUIT de una sociedad (30-…) o CUIL de un monotributista (20-…, 23-…, 24-…)."
        )
        self._armar_scroll()
        self.ui.aplicar_modo(self._edicion)
        self.setWindowTitle(TITULO_EDICION if self._edicion else TITULO_INICIAL)
        self._cargar_comercio()
        self.ui.txtCuit.textChanged.connect(self.validar_cuit)
        self.ui.txtNombre.setFocus()
        self._armar_seccion_backups()
        self.cargar_backups()
        self._armar_seccion_interfaz()
        self._armar_seccion_fiado()
        self._armar_seccion_cuenta()
        self._armar_seccion_plan()
        self._armar_seccion_codigos()

    def _cargar_comercio(self) -> None:
        if self._comercio is None:
            return
        self.ui.txtNombre.setText(self._comercio.nombre)
        self.ui.txtDireccion.setText(self._comercio.direccion)
        self.ui.txtCuit.setText(self._comercio.cuit)
        self.ui.txtTelefono.setText(self._comercio.telefono)

    def _armar_scroll(self) -> None:
        area = QScrollArea(self)
        area.setObjectName("sbrConfig")
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        contenido = QWidget(area)
        area.setWidget(contenido)
        contenido.setLayout(self.ui.verticalLayout)

        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)
        exterior.setSpacing(0)
        exterior.addWidget(area)

        self.setMinimumSize(560, 540)
        self.setMaximumSize(1600, 1400)
        self.resize(560, 900)

    def _armar_seccion_backups(self) -> None:
        grupo = QGroupBox("Copias de seguridad", self)
        grupo.setObjectName("grpBackups")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblRutaBackups = QLabel(grupo)
        self.lblRutaBackups.setObjectName("lblRutaBackups")
        self.lblRutaBackups.setWordWrap(True)
        self.lblRutaBackups.setText(f"Se guardan en: {self._backup.directorio_backups()}")
        disposicion.addWidget(self.lblRutaBackups)

        self.tblBackups = QTableWidget(grupo)
        self.tblBackups.setObjectName("tblBackups")
        self.tblBackups.setColumnCount(3)
        self.tblBackups.setHorizontalHeaderLabels(["Copia", "Fecha y hora", "Tamaño"])
        self.tblBackups.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tblBackups.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tblBackups.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblBackups.setMinimumHeight(140)
        encabezado = self.tblBackups.horizontalHeader()
        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        disposicion.addWidget(self.tblBackups)

        self.lblSinBackups = QLabel(grupo)
        self.lblSinBackups.setObjectName("lblSinBackups")
        self.lblSinBackups.setWordWrap(True)
        disposicion.addWidget(self.lblSinBackups)

        botones = QHBoxLayout()
        self.btnCopiarAhora = QPushButton("Hacer copia ahora", grupo)
        self.btnCopiarAhora.setObjectName("btnCopiarAhora")
        self.btnCopiarAhora.setMinimumHeight(32)
        self.btnCopiarAhora.clicked.connect(self.hacer_copia)
        botones.addWidget(self.btnCopiarAhora)
        self.btnRestaurar = QPushButton("Restaurar", grupo)
        self.btnRestaurar.setObjectName("btnRestaurar")
        self.btnRestaurar.setMinimumHeight(32)
        self.btnRestaurar.clicked.connect(self.restaurar)
        botones.addWidget(self.btnRestaurar)
        disposicion.addLayout(botones)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_interfaz(self) -> None:
        grupo = QGroupBox("Barra lateral y módulos", self)
        grupo.setObjectName("grpInterfaz")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        fila = QHBoxLayout()
        lbl = QLabel("Ubicación del menú:", grupo)
        self.cmbPosicionMenu = QComboBox(grupo)
        self.cmbPosicionMenu.addItem("Izquierda", "izquierda")
        self.cmbPosicionMenu.addItem("Derecha", "derecha")
        pos_actual = posicion_menu()
        idx = self.cmbPosicionMenu.findData(pos_actual)
        if idx >= 0:
            self.cmbPosicionMenu.setCurrentIndex(idx)
        fila.addWidget(lbl)
        fila.addWidget(self.cmbPosicionMenu, 1)
        disposicion.addLayout(fila)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_fiado(self) -> None:
        # Edición libre: el recargo por atraso es función de la edición paga.
        return

    def _armar_seccion_cuenta(self) -> None:
        if not self._edicion or self._autenticacion is None:
            return
        usuario = self._autenticacion.usuario_actual
        if usuario is None:
            return
        grupo = QGroupBox("Cuenta", self)
        grupo.setObjectName("grpCuenta")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        ayuda = QLabel(
            f"Conectado como {usuario.nombre}. Podés cambiar tu contraseña, "
            "los usuarios adicionales son una función del plan de pago.",
            grupo)
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet(f"color: {GRIS_TEXTO};")
        disposicion.addWidget(ayuda)

        self.btnCambiarPassword = QPushButton("Cambiar contraseña", grupo)
        self.btnCambiarPassword.setObjectName("btnCambiarPassword")
        self.btnCambiarPassword.setMinimumHeight(32)
        self.btnCambiarPassword.clicked.connect(self._cambiar_password)
        disposicion.addWidget(self.btnCambiarPassword)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _cambiar_password(self) -> None:
        dialogo = DialogoCambiarPassword(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        actual, nueva = dialogo.datos
        try:
            self._autenticacion.cambiar_password(actual, nueva)
        except ValueError as error:
            self.mostrar_advertencia("Cuenta", str(error))
            return
        self.mostrar_informacion("Cuenta", "La contraseña se actualizó.")

    def _armar_seccion_plan(self) -> None:
        grupo = QGroupBox("Plan y límites", self)
        grupo.setObjectName("grpPlan")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblPlan = QLabel(grupo)
        self.lblPlan.setObjectName("lblPlan")
        disposicion.addWidget(self.lblPlan)

        self.lblLimites = QLabel(grupo)
        self.lblLimites.setObjectName("lblLimites")
        self.lblLimites.setWordWrap(True)
        disposicion.addWidget(self.lblLimites)

        self.btnVerPlanes = QPushButton("Conocé BetterStock Pro", grupo)
        self.btnVerPlanes.setObjectName("btnVerPlanes")
        self.btnVerPlanes.setMinimumHeight(32)
        self.btnVerPlanes.clicked.connect(self._ver_planes)
        disposicion.addWidget(self.btnVerPlanes)

        # Edición libre: no hay activación de licencia ni módulos premium.
        # (Los planes pagos se gestionan desde BetterStock Pro.)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_interfaz(self) -> None:
        grupo = QGroupBox("Barra lateral y módulos", self)
        grupo.setObjectName("grpInterfaz")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        fila = QHBoxLayout()
        lbl = QLabel("Ubicación del menú:", grupo)
        self.cmbPosicionMenu = QComboBox(grupo)
        self.cmbPosicionMenu.addItem("Izquierda", "izquierda")
        self.cmbPosicionMenu.addItem("Derecha", "derecha")
        pos_actual = posicion_menu()
        idx = self.cmbPosicionMenu.findData(pos_actual)
        if idx >= 0:
            self.cmbPosicionMenu.setCurrentIndex(idx)
        fila.addWidget(lbl)
        fila.addWidget(self.cmbPosicionMenu, 1)
        disposicion.addLayout(fila)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_fiado(self) -> None:
        # Edición libre: el recargo por atraso es función de la edición paga.
        return

    def _armar_seccion_cuenta(self) -> None:
        if not self._edicion or self._autenticacion is None:
            return
        usuario = self._autenticacion.usuario_actual
        if usuario is None:
            return
        grupo = QGroupBox("Cuenta", self)
        grupo.setObjectName("grpCuenta")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        ayuda = QLabel(
            f"Conectado como {usuario.nombre}. Podés cambiar tu contraseña, "
            "los usuarios adicionales son una función del plan de pago.",
            grupo)
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet(f"color: {GRIS_TEXTO};")
        disposicion.addWidget(ayuda)

        self.btnCambiarPassword = QPushButton("Cambiar contraseña", grupo)
        self.btnCambiarPassword.setObjectName("btnCambiarPassword")
        self.btnCambiarPassword.setMinimumHeight(32)
        self.btnCambiarPassword.clicked.connect(self._cambiar_password)
        disposicion.addWidget(self.btnCambiarPassword)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _cambiar_password(self) -> None:
        dialogo = DialogoCambiarPassword(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        actual, nueva = dialogo.datos
        try:
            self._autenticacion.cambiar_password(actual, nueva)
        except ValueError as error:
            self.mostrar_advertencia("Cuenta", str(error))
            return
        self.mostrar_informacion("Cuenta", "La contraseña se actualizó.")

    def _armar_seccion_plan(self) -> None:
        grupo = QGroupBox("Plan y límites", self)
        grupo.setObjectName("grpPlan")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblPlan = QLabel(grupo)
        self.lblPlan.setObjectName("lblPlan")
        disposicion.addWidget(self.lblPlan)

        self.lblLimites = QLabel(grupo)
        self.lblLimites.setObjectName("lblLimites")
        self.lblLimites.setWordWrap(True)
        disposicion.addWidget(self.lblLimites)

        self.btnVerPlanes = QPushButton("Conocé BetterStock Pro", grupo)
        self.btnVerPlanes.setObjectName("btnVerPlanes")
        self.btnVerPlanes.setMinimumHeight(32)
        self.btnVerPlanes.clicked.connect(self._ver_planes)
        disposicion.addWidget(self.btnVerPlanes)

        # Edición libre: no hay activación de licencia ni módulos premium.
        # (La edición paga se gestiona desde BetterStock Pro.)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_interfaz(self) -> None:
        grupo = QGroupBox("Barra lateral y módulos", self)
        grupo.setObjectName("grpInterfaz")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        fila = QHBoxLayout()
        lbl = QLabel("Ubicación del menú:", grupo)
        self.cmbPosicionMenu = QComboBox(grupo)
        self.cmbPosicionMenu.addItem("Izquierda", "izquierda")
        self.cmbPosicionMenu.addItem("Derecha", "derecha")
        pos_actual = posicion_menu()
        idx = self.cmbPosicionMenu.findData(pos_actual)
        if idx >= 0:
            self.cmbPosicionMenu.setCurrentIndex(idx)
        fila.addWidget(lbl)
        fila.addWidget(self.cmbPosicionMenu, 1)
        disposicion.addLayout(fila)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_fiado(self) -> None:
        # Edición libre: el recargo por atraso es función de la edición paga.
        return

    def _armar_seccion_cuenta(self) -> None:
        if not self._edicion or self._autenticacion is None:
            return
        usuario = self._autenticacion.usuario_actual
        if usuario is None:
            return
        grupo = QGroupBox("Cuenta", self)
        grupo.setObjectName("grpCuenta")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        ayuda = QLabel(
            f"Conectado como {usuario.nombre}. Podés cambiar tu contraseña, "
            "los usuarios adicionales son una función del plan de pago.",
            grupo)
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet(f"color: {GRIS_TEXTO};")
        disposicion.addWidget(ayuda)

        self.btnCambiarPassword = QPushButton("Cambiar contraseña", grupo)
        self.btnCambiarPassword.setObjectName("btnCambiarPassword")
        self.btnCambiarPassword.setMinimumHeight(32)
        self.btnCambiarPassword.clicked.connect(self._cambiar_password)
        disposicion.addWidget(self.btnCambiarPassword)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _cambiar_password(self) -> None:
        dialogo = DialogoCambiarPassword(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        actual, nueva = dialogo.datos
        try:
            self._autenticacion.cambiar_password(actual, nueva)
        except ValueError as error:
            self.mostrar_advertencia("Cuenta", str(error))
            return
        self.mostrar_informacion("Cuenta", "La contraseña se actualizó.")

    def _armar_seccion_plan(self) -> None:
        grupo = QGroupBox("Plan y límites", self)
        grupo.setObjectName("grpPlan")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblPlan = QLabel(grupo)
        self.lblPlan.setObjectName("lblPlan")
        disposicion.addWidget(self.lblPlan)

        self.lblLimites = QLabel(grupo)
        self.lblLimites.setObjectName("lblLimites")
        self.lblLimites.setWordWrap(True)
        disposicion.addWidget(self.lblLimites)

        self.btnVerPlanes = QPushButton("Conocé BetterStock Pro", grupo)
        self.btnVerPlanes.setObjectName("btnVerPlanes")
        self.btnVerPlanes.setMinimumHeight(32)
        self.btnVerPlanes.clicked.connect(self._ver_planes)
        disposicion.addWidget(self.btnVerPlanes)

        # Edición libre: no hay activación de licencia ni módulos premium.
        # (Los planes pagos se gestionan desde BetterStock Pro.)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_interfaz(self) -> None:
        grupo = QGroupBox("Barra lateral y módulos", self)
        grupo.setObjectName("grpInterfaz")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        fila = QHBoxLayout()
        lbl = QLabel("Ubicación del menú:", grupo)
        self.cmbPosicionMenu = QComboBox(grupo)
        self.cmbPosicionMenu.addItem("Izquierda", "izquierda")
        self.cmbPosicionMenu.addItem("Derecha", "derecha")
        pos_actual = posicion_menu()
        idx = self.cmbPosicionMenu.findData(pos_actual)
        if idx >= 0:
            self.cmbPosicionMenu.setCurrentIndex(idx)
        fila.addWidget(lbl)
        fila.addWidget(self.cmbPosicionMenu, 1)
        disposicion.addLayout(fila)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_fiado(self) -> None:
        # Edición libre: el recargo por atraso es función de la edición paga.
        return

    def _armar_seccion_cuenta(self) -> None:
        if not self._edicion or self._autenticacion is None:
            return
        usuario = self._autenticacion.usuario_actual
        if usuario is None:
            return
        grupo = QGroupBox("Cuenta", self)
        grupo.setObjectName("grpCuenta")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        ayuda = QLabel(
            f"Conectado como {usuario.nombre}. Podés cambiar tu contraseña, "
            "los usuarios adicionales son una función del plan de pago.",
            grupo)
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet(f"color: {GRIS_TEXTO};")
        disposicion.addWidget(ayuda)

        self.btnCambiarPassword = QPushButton("Cambiar contraseña", grupo)
        self.btnCambiarPassword.setObjectName("btnCambiarPassword")
        self.btnCambiarPassword.setMinimumHeight(32)
        self.btnCambiarPassword.clicked.connect(self._cambiar_password)
        disposicion.addWidget(self.btnCambiarPassword)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _cambiar_password(self) -> None:
        dialogo = DialogoCambiarPassword(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        actual, nueva = dialogo.datos
        try:
            self._autenticacion.cambiar_password(actual, nueva)
        except ValueError as error:
            self.mostrar_advertencia("Cuenta", str(error))
            return
        self.mostrar_informacion("Cuenta", "La contraseña se actualizó.")

    def _armar_seccion_plan(self) -> None:
        grupo = QGroupBox("Plan y límites", self)
        grupo.setObjectName("grpPlan")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblPlan = QLabel(grupo)
        self.lblPlan.setObjectName("lblPlan")
        disposicion.addWidget(self.lblPlan)

        self.lblLimites = QLabel(grupo)
        self.lblLimites.setObjectName("lblLimites")
        self.lblLimites.setWordWrap(True)
        disposicion.addWidget(self.lblLimites)

        self.btnVerPlanes = QPushButton("Conocé BetterStock Pro", grupo)
        self.btnVerPlanes.setObjectName("btnVerPlanes")
        self.btnVerPlanes.setMinimumHeight(32)
        self.btnVerPlanes.clicked.connect(self._ver_planes)
        disposicion.addWidget(self.btnVerPlanes)

        # Edición libre: sin activación de licencia ni módulos premium.
        # (La edición paga se gestiona desde BetterStock Pro.)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_interfaz(self) -> None:
        grupo = QGroupBox("Barra lateral y módulos", self)
        grupo.setObjectName("grpInterfaz")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        fila = QHBoxLayout()
        lbl = QLabel("Ubicación del menú:", grupo)
        self.cmbPosicionMenu = QComboBox(grupo)
        self.cmbPosicionMenu.addItem("Izquierda", "izquierda")
        self.cmbPosicionMenu.addItem("Derecha", "derecha")
        pos_actual = posicion_menu()
        idx = self.cmbPosicionMenu.findData(pos_actual)
        if idx >= 0:
            self.cmbPosicionMenu.setCurrentIndex(idx)
        fila.addWidget(lbl)
        fila.addWidget(self.cmbPosicionMenu, 1)
        disposicion.addLayout(fila)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_fiado(self) -> None:
        # Edición libre: el recargo por atraso es función de la edición paga.
        return

    def _armar_seccion_cuenta(self) -> None:
        if not self._edicion or self._autenticacion is None:
            return
        usuario = self._autenticacion.usuario_actual
        if usuario is None:
            return
        grupo = QGroupBox("Cuenta", self)
        grupo.setObjectName("grpCuenta")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        ayuda = QLabel(
            f"Conectado como {usuario.nombre}. Podés cambiar tu contraseña, "
            "los usuarios adicionales son una función del plan de pago.",
            grupo)
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet(f"color: {GRIS_TEXTO};")
        disposicion.addWidget(ayuda)

        self.btnCambiarPassword = QPushButton("Cambiar contraseña", grupo)
        self.btnCambiarPassword.setObjectName("btnCambiarPassword")
        self.btnCambiarPassword.setMinimumHeight(32)
        self.btnCambiarPassword.clicked.connect(self._cambiar_password)
        disposicion.addWidget(self.btnCambiarPassword)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _cambiar_password(self) -> None:
        dialogo = DialogoCambiarPassword(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        actual, nueva = dialogo.datos
        try:
            self._autenticacion.cambiar_password(actual, nueva)
        except ValueError as error:
            self.mostrar_advertencia("Cuenta", str(error))
            return
        self.mostrar_informacion("Cuenta", "La contraseña se actualizó.")

    def _armar_seccion_plan(self) -> None:
        grupo = QGroupBox("Plan y límites", self)
        grupo.setObjectName("grpPlan")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblPlan = QLabel(grupo)
        self.lblPlan.setObjectName("lblPlan")
        disposicion.addWidget(self.lblPlan)

        self.lblLimites = QLabel(grupo)
        self.lblLimites.setObjectName("lblLimites")
        self.lblLimites.setWordWrap(True)
        disposicion.addWidget(self.lblLimites)

        self.btnVerPlanes = QPushButton("Conocé BetterStock Pro", grupo)
        self.btnVerPlanes.setObjectName("btnVerPlanes")
        self.btnVerPlanes.setMinimumHeight(32)
        self.btnVerPlanes.clicked.connect(self._ver_planes)
        disposicion.addWidget(self.btnVerPlanes)

        # Edición libre: no hay activación de licencia ni módulos premium.
        # (Los planes pagos se gestionan desde BetterStock Pro.)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_interfaz(self) -> None:
        grupo = QGroupBox("Barra lateral y módulos", self)
        grupo.setObjectName("grpInterfaz")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        fila = QHBoxLayout()
        lbl = QLabel("Ubicación del menú:", grupo)
        self.cmbPosicionMenu = QComboBox(grupo)
        self.cmbPosicionMenu.addItem("Izquierda", "izquierda")
        self.cmbPosicionMenu.addItem("Derecha", "derecha")
        pos_actual = posicion_menu()
        idx = self.cmbPosicionMenu.findData(pos_actual)
        if idx >= 0:
            self.cmbPosicionMenu.setCurrentIndex(idx)
        fila.addWidget(lbl)
        fila.addWidget(self.cmbPosicionMenu, 1)
        disposicion.addLayout(fila)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_fiado(self) -> None:
        # Edición libre: el recargo por atraso es función de la edición paga.
        return

    def _armar_seccion_cuenta(self) -> None:
        if not self._edicion or self._autenticacion is None:
            return
        usuario = self._autenticacion.usuario_actual
        if usuario is None:
            return
        grupo = QGroupBox("Cuenta", self)
        grupo.setObjectName("grpCuenta")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        ayuda = QLabel(
            f"Conectado como {usuario.nombre}. Podés cambiar tu contraseña, "
            "los usuarios adicionales son una función del plan de pago.",
            grupo)
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet(f"color: {GRIS_TEXTO};")
        disposicion.addWidget(ayuda)

        self.btnCambiarPassword = QPushButton("Cambiar contraseña", grupo)
        self.btnCambiarPassword.setObjectName("btnCambiarPassword")
        self.btnCambiarPassword.setMinimumHeight(32)
        self.btnCambiarPassword.clicked.connect(self._cambiar_password)
        disposicion.addWidget(self.btnCambiarPassword)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _cambiar_password(self) -> None:
        dialogo = DialogoCambiarPassword(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        actual, nueva = dialogo.datos
        try:
            self._autenticacion.cambiar_password(actual, nueva)
        except ValueError as error:
            self.mostrar_advertencia("Cuenta", str(error))
            return
        self.mostrar_informacion("Cuenta", "La contraseña se actualizó.")

    def _armar_seccion_plan(self) -> None:
        grupo = QGroupBox("Plan y límites", self)
        grupo.setObjectName("grpPlan")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblPlan = QLabel(grupo)
        self.lblPlan.setObjectName("lblPlan")
        disposicion.addWidget(self.lblPlan)

        self.lblLimites = QLabel(grupo)
        self.lblLimites.setObjectName("lblLimites")
        self.lblLimites.setWordWrap(True)
        disposicion.addWidget(self.lblLimites)

        self.btnVerPlanes = QPushButton("Conocé BetterStock Pro", grupo)
        self.btnVerPlanes.setObjectName("btnVerPlanes")
        self.btnVerPlanes.setMinimumHeight(32)
        self.btnVerPlanes.clicked.connect(self._ver_planes)
        disposicion.addWidget(self.btnVerPlanes)

        # Edición libre: no hay activación de licencia ni módulos premium.
        # (La edición paga se gestiona desde BetterStock Pro.)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_interfaz(self) -> None:
        grupo = QGroupBox("Barra lateral y módulos", self)
        grupo.setObjectName("grpInterfaz")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        fila = QHBoxLayout()
        lbl = QLabel("Ubicación del menú:", grupo)
        self.cmbPosicionMenu = QComboBox(grupo)
        self.cmbPosicionMenu.addItem("Izquierda", "izquierda")
        self.cmbPosicionMenu.addItem("Derecha", "derecha")
        pos_actual = posicion_menu()
        idx = self.cmbPosicionMenu.findData(pos_actual)
        if idx >= 0:
            self.cmbPosicionMenu.setCurrentIndex(idx)
        fila.addWidget(lbl)
        fila.addWidget(self.cmbPosicionMenu, 1)
        disposicion.addLayout(fila)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_fiado(self) -> None:
        # Edición libre: el recargo por atraso es función de la edición paga.
        return

    def _armar_seccion_cuenta(self) -> None:
        if not self._edicion or self._autenticacion is None:
            return
        usuario = self._autenticacion.usuario_actual
        if usuario is None:
            return
        grupo = QGroupBox("Cuenta", self)
        grupo.setObjectName("grpCuenta")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        ayuda = QLabel(
            f"Conectado como {usuario.nombre}. Podés cambiar tu contraseña, "
            "los usuarios adicionales son una función del plan de pago.",
            grupo)
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet(f"color: {GRIS_TEXTO};")
        disposicion.addWidget(ayuda)

        self.btnCambiarPassword = QPushButton("Cambiar contraseña", grupo)
        self.btnCambiarPassword.setObjectName("btnCambiarPassword")
        self.btnCambiarPassword.setMinimumHeight(32)
        self.btnCambiarPassword.clicked.connect(self._cambiar_password)
        disposicion.addWidget(self.btnCambiarPassword)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _cambiar_password(self) -> None:
        dialogo = DialogoCambiarPassword(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        actual, nueva = dialogo.datos
        try:
            self._autenticacion.cambiar_password(actual, nueva)
        except ValueError as error:
            self.mostrar_advertencia("Cuenta", str(error))
            return
        self.mostrar_informacion("Cuenta", "La contraseña se actualizó.")

    def _armar_seccion_plan(self) -> None:
        grupo = QGroupBox("Plan y límites", self)
        grupo.setObjectName("grpPlan")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblPlan = QLabel(grupo)
        self.lblPlan.setObjectName("lblPlan")
        disposicion.addWidget(self.lblPlan)

        self.lblLimites = QLabel(grupo)
        self.lblLimites.setObjectName("lblLimites")
        self.lblLimites.setWordWrap(True)
        disposicion.addWidget(self.lblLimites)

        self.btnVerPlanes = QPushButton("Conocé BetterStock Pro", grupo)
        self.btnVerPlanes.setObjectName("btnVerPlanes")
        self.btnVerPlanes.setMinimumHeight(32)
        self.btnVerPlanes.clicked.connect(self._ver_planes)
        disposicion.addWidget(self.btnVerPlanes)

        # Edición libre: no hay activación de licencia ni módulos premium.
        # (Los planes pagos se gestionan desde BetterStock Pro.)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_interfaz(self) -> None:
        grupo = QGroupBox("Barra lateral y módulos", self)
        grupo.setObjectName("grpInterfaz")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        fila = QHBoxLayout()
        lbl = QLabel("Ubicación del menú:", grupo)
        self.cmbPosicionMenu = QComboBox(grupo)
        self.cmbPosicionMenu.addItem("Izquierda", "izquierda")
        self.cmbPosicionMenu.addItem("Derecha", "derecha")
        pos_actual = posicion_menu()
        idx = self.cmbPosicionMenu.findData(pos_actual)
        if idx >= 0:
            self.cmbPosicionMenu.setCurrentIndex(idx)
        fila.addWidget(lbl)
        fila.addWidget(self.cmbPosicionMenu, 1)
        disposicion.addLayout(fila)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _armar_seccion_fiado(self) -> None:
        # Edición libre: el recargo por atraso es función de la edición paga.
        return

    def _armar_seccion_cuenta(self) -> None:
        if not self._edicion or self._autenticacion is None:
            return
        usuario = self._autenticacion.usuario_actual
        if usuario is None:
            return
        grupo = QGroupBox("Cuenta", self)
        grupo.setObjectName("grpCuenta")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        ayuda = QLabel(
            f"Conectado como {usuario.nombre}. Podés cambiar tu contraseña, "
            "los usuarios adicionales son una función del plan de pago.",
            grupo)
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet(f"color: {GRIS_TEXTO};")
        disposicion.addWidget(ayuda)

        self.btnCambiarPassword = QPushButton("Cambiar contraseña", grupo)
        self.btnCambiarPassword.setObjectName("btnCambiarPassword")
        self.btnCambiarPassword.setMinimumHeight(32)
        self.btnCambiarPassword.clicked.connect(self._cambiar_password)
        disposicion.addWidget(self.btnCambiarPassword)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)

    def _cambiar_password(self) -> None:
        dialogo = DialogoCambiarPassword(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        actual, nueva = dialogo.datos
        try:
            self._autenticacion.cambiar_password(actual, nueva)
        except ValueError as error:
            self.mostrar_advertencia("Cuenta", str(error))
            return
        self.mostrar_informacion("Cuenta", "La contraseña se actualizó.")

    def _armar_seccion_plan(self) -> None:
        grupo = QGroupBox("Plan y límites", self)
        grupo.setObjectName("grpPlan")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblPlan = QLabel(grupo)
        self.lblPlan.setObjectName("lblPlan")
        disposicion.addWidget(self.lblPlan)

        self.lblLimites = QLabel(grupo)
        self.lblLimites.setObjectName("lblLimites")
        self.lblLimites.setWordWrap(True)
        disposicion.addWidget(self.lblLimites)

        self.btnVerPlanes = QPushButton("Conocé BetterStock Pro", grupo)
        self.btnVerPlanes.setObjectName("btnVerPlanes")
        self.btnVerPlanes.setMinimumHeight(32)
        self.btnVerPlanes.clicked.connect(self._ver_planes)
        disposicion.addWidget(self.btnVerPlanes)

        # Edición libre: sin activación de licencia ni módulos premium.
        # (La edición paga se gestiona desde BetterStock Pro.)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)
        self._refrescar_plan()

    def _armar_seccion_codigos(self) -> None:
        grupo = QGroupBox("Códigos de anulación", self)
        grupo.setObjectName("grpCodigos")
        disposicion = QVBoxLayout(grupo)
        disposicion.setContentsMargins(10, 10, 10, 10)
        disposicion.setSpacing(6)

        self.lblAyudaCodigos = QLabel(grupo)
        self.lblAyudaCodigos.setObjectName("lblAyudaCodigos")
        self.lblAyudaCodigos.setWordWrap(True)
        font_ayuda = fuente(TAMANO_MICRO)
        self.lblAyudaCodigos.setFont(font_ayuda)
        self.lblAyudaCodigos.setStyleSheet(f"color: {GRIS_TEXTO};")
        self.lblAyudaCodigos.setText(
            "El código lo tiene el supervisor y sirve para anular ventas. "
            "Se muestra una sola vez, al generarlo: después queda solo el hash."
        )
        disposicion.addWidget(self.lblAyudaCodigos)

        self.lblSinCodigo = QLabel(grupo)
        self.lblSinCodigo.setObjectName("lblSinCodigo")
        self.lblSinCodigo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblSinCodigo.setStyleSheet(f"color: {GRIS_TEXTO};")
        self.lblSinCodigo.setText(SIN_CODIGO)
        disposicion.addWidget(self.lblSinCodigo)

        self.lblCodigoGenerado = QLabel(grupo)
        self.lblCodigoGenerado.setObjectName("lblCodigoGenerado")
        self.lblCodigoGenerado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fuente_codigo = QFont(FUENTE_MONOESPACADA)
        fuente_codigo.setPointSize(TAMANO_CODIGO)
        fuente_codigo.setBold(True)
        self.lblCodigoGenerado.setFont(fuente_codigo)
        self.lblCodigoGenerado.setVisible(False)
        disposicion.addWidget(self.lblCodigoGenerado)

        botones = QHBoxLayout()
        self.btnGenerarCodigo = QPushButton("Generar código", grupo)
        self.btnGenerarCodigo.setObjectName("btnGenerarCodigo")
        self.btnGenerarCodigo.setMinimumHeight(32)
        self.btnGenerarCodigo.clicked.connect(self.generar_codigo)
        botones.addWidget(self.btnGenerarCodigo)

        self.btnCopiarCodigo = QPushButton("Copiar", grupo)
        self.btnCopiarCodigo.setObjectName("btnCopiarCodigo")
        self.btnCopiarCodigo.setMinimumHeight(32)
        self.btnCopiarCodigo.setEnabled(False)
        self.btnCopiarCodigo.clicked.connect(self.copiar_codigo)
        botones.addWidget(self.btnCopiarCodigo)

        self.btnImprimirCodigo = QPushButton("Imprimir", grupo)
        self.btnImprimirCodigo.setObjectName("btnImprimirCodigo")
        self.btnImprimirCodigo.setMinimumHeight(32)
        self.btnImprimirCodigo.setEnabled(False)
        self.btnImprimirCodigo.setToolTip("Imprime el código con la impresora del sistema.")
        self.btnImprimirCodigo.clicked.connect(self.imprimir_codigo)
        botones.addWidget(self.btnImprimirCodigo)
        disposicion.addLayout(botones)

        self.tblCodigos = QTableWidget(grupo)
        self.tblCodigos.setObjectName("tblCodigos")
        self.tblCodigos.setColumnCount(3)
        self.tblCodigos.setHorizontalHeaderLabels(["Supervisor", "Fecha", "Estado"])
        self.tblCodigos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tblCodigos.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tblCodigos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblCodigos.setMinimumHeight(120)
        encabezado = self.tblCodigos.horizontalHeader()
        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        disposicion.addWidget(self.tblCodigos)

        self.btnRevocarCodigo = QPushButton("Revocar", grupo)
        self.btnRevocarCodigo.setObjectName("btnRevocarCodigo")
        self.btnRevocarCodigo.setMinimumHeight(32)
        self.btnRevocarCodigo.clicked.connect(self.revocar_codigo)
        disposicion.addWidget(self.btnRevocarCodigo)

        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, grupo)
        self.cargar_codigos()

    def cargar_codigos(self) -> None:
        if self._anulaciones is None:
            return
        codigos = self._anulaciones.listar_codigos()
        self.llenar_tabla(
            self.tblCodigos,
            [[codigo.etiqueta or "—", codigo.fecha_texto, codigo.estado_texto]
             for codigo in codigos],
        )
        self.btnRevocarCodigo.setEnabled(bool(codigos))

    def generar_codigo(self) -> None:
        if self._permiso and self._permiso != Usuario.PERMISO_ADMIN:
            self.mostrar_advertencia(
                "Acceso restringido",
                "Solo un administrador puede generar códigos de anulación.",
            )
            return
        if self._anulaciones is None:
            self.mostrar_advertencia(
                "Códigos de anulación", MENSAJE_SIN_SERVICIO)
            return
        etiqueta, aceptado = QInputDialog.getText(
            self, "Generar código", "Nombre del supervisor (opcional):")
        if not aceptado:
            return
        modelo, codigo = self._anulaciones.generar_codigo(etiqueta)
        self._codigo_generado = codigo
        self._etiqueta_generada = modelo.etiqueta
        self.lblCodigoGenerado.setText(codigo)
        self.lblCodigoGenerado.setVisible(True)
        self.lblSinCodigo.setVisible(False)
        self.btnCopiarCodigo.setEnabled(True)
        self.btnImprimirCodigo.setEnabled(True)
        self.cargar_codigos()
        Notificacion(self).mostrar(
            "Código generado",
            f"Código {codigo} para {modelo.etiqueta or 'el supervisor'}. "
            "Copiá o imprimilo ahora: después no se vuelve a mostrar.")

    def copiar_codigo(self) -> None:
        if not self._codigo_generado:
            self.mostrar_advertencia(
                "Códigos de anulación",
                "Generá un código primero: solo se copia el que acabás de generar.")
            return
        QApplication.clipboard().setText(self._codigo_generado)
        Notificacion(self).mostrar(
            "Código copiado", f"El código {self._codigo_generado} está en el portapapeles.")

    def imprimir_codigo(self) -> None:
        if not self._codigo_generado:
            self.mostrar_advertencia(
                "Códigos de anulación",
                "Generá un código primero: solo se imprime el que acabás de generar.")
            return
        codigo = self._codigo_generado
        etiqueta = self._etiqueta_generada
        trabajo = TrabajoImpresion(lambda: imprimir_codigo_anulacion(codigo, etiqueta))
        trabajo.terminado.connect(self._al_terminar_impresion_codigo)
        trabajo.finished.connect(lambda: self._cerrar_trabajo(trabajo))
        self._trabajos.append(trabajo)
        trabajo.start()

    def _al_terminar_impresion_codigo(self, error: str) -> None:
        if error:
            self.mostrar_advertencia(
                "No se pudo imprimir",
                f"No se pudo imprimir el código ({error}).\n\n"
                "Podés copiarlo y pasarlo al supervisor de otra forma.")
            return
        Notificacion(self).mostrar(
            "Código impreso", f"Se imprimió el código {self._codigo_generado}.")

    def _cerrar_trabajo(self, trabajo: TrabajoImpresion) -> None:
        if trabajo in self._trabajos:
            self._trabajos.remove(trabajo)
        trabajo.deleteLater()

    def revocar_codigo(self) -> None:
        if self._anulaciones is None:
            return
        fila = self.tblCodigos.currentRow()
        codigos = self._anulaciones.listar_codigos()
        if fila < 0 or fila >= len(codigos):
            self.mostrar_advertencia(
                "Revocar código", "Elegí un código de la lista primero.")
            return
        codigo = codigos[fila]
        if not codigo.activo:
            self.mostrar_advertencia(
                "Revocar código", "Ese código ya está revocado.")
            return
        if not self.confirmar(
            "Revocar código",
            f"¿Revocar el código de {codigo.etiqueta or 'el supervisor'}?\n\n"
            "Después no se va a poder anular ninguna venta con ese código.",
        ):
            return
        self._anulaciones.revocar_codigo(codigo.identificador)
        self.cargar_codigos()
        Notificacion(self).mostrar(
            "Código revocado", "El código ya no sirve para anular ventas.")

    def _refrescar_plan(self) -> None:
        self.lblPlan.setText("Plan actual: Gratis")
        self.lblLimites.setText(texto_limites())

    def _ver_planes(self) -> None:
        QDesktopServices.openUrl(QUrl("https://betterstock.tech"))

    def validar_cuit(self, texto: str) -> None:
        if not texto.strip():
            self.ui.lblCuit.setStyleSheet("")
            return
        if es_cuit_valido(texto):
            tipo = tipo_de_identificador(texto)
            etiqueta = "sociedad" if tipo == "sociedad" else "monotributista"
            self.ui.lblCuit.setStyleSheet(f"color: {VERDE_TEXTO};")
            self.ui.lblCuit.setText(f"{normalizar_cuit(texto)} — {etiqueta}")
            return
        self.ui.lblCuit.setStyleSheet(f"color: {AMBAR_TEXTO};")
        self.ui.lblCuit.setText("Revisá el CUIT: son 11 dígitos y el último es verificador.")

    def cargar_backups(self) -> None:
        copias = self._backup.listar()
        self._copias = copias
        self.llenar_tabla(
            self.tblBackups,
            [
                [ruta.name, datetime.fromtimestamp(ruta.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                 tamano_legible(ruta)]
                for ruta in copias
            ],
        )
        hay = bool(copias)
        for fila in range(self.tblBackups.rowCount()):
            self.tblBackups.item(fila, 0).setToolTip(str(copias[fila]))
        self.lblSinBackups.setText(
            "" if hay else "Todavía no hay copias. Se genera sola al cerrar caja."
        )
        self.btnRestaurar.setEnabled(hay)

    def _copia_seleccionada(self):
        fila = self.tblBackups.currentRow()
        if fila < 0:
            self.mostrar_advertencia("Restaurar", "Elegí una copia de la lista primero.")
            return None
        return self._copias[fila]

    def hacer_copia(self) -> None:
        try:
            nueva = self._backup.generar()
            self._backup.rotar()
        except ErrorBackup as error:
            self.mostrar_advertencia("Copias de seguridad", str(error))
            return
        self.cargar_backups()
        self._seleccionar(nueva)
        mensajes = self._backup.sacar_mensajes()
        texto = f"Copia guardada en {nueva}"
        if mensajes:
            texto += " · " + " · ".join(mensajes)
        Notificacion(self).mostrar("Copia de seguridad", texto)

    def restaurar(self) -> None:
        if self._permiso and self._permiso != Usuario.PERMISO_ADMIN:
            self.mostrar_advertencia(
                "Acceso restringido",
                "Solo un administrador puede restaurar copias de seguridad.",
            )
            return
        origen = self._copia_seleccionada()
        if origen is None:
            return
        if not self.confirmar("Restaurar copia", f"Vas a volver a la copia {origen.name}.\n\n{MENSAJE_CONFIRMAR}"):
            return
        try:
            self._backup.restaurar(origen)
        except ErrorBackup as error:
            self.mostrar_advertencia("Restaurar copia", str(error))
            return
        self.cargar_backups()
        Notificacion(self).mostrar(
            "Copia restaurada",
            f"Se restauró {origen.name}. Reiniciá la aplicación para trabajar con los datos recuperados.",
        )

    def _seleccionar(self, ruta) -> None:
        for indice, copia in enumerate(self._copias):
            if copia == ruta:
                self.tblBackups.selectRow(indice)
                return

    def guardar(self) -> None:
        self.ui.lblError.setText("")
        try:
            self._gestor_comercio.configurar(
                self.ui.txtNombre.text(),
                self.ui.txtDireccion.text(),
                self.ui.txtCuit.text(),
                self.ui.txtTelefono.text(),
            )
        except ValueError as error:
            self.ui.lblError.setText(str(error))
            return

        if hasattr(self, "cmbPosicionMenu"):
            pos = self.cmbPosicionMenu.currentData() or "izquierda"
            guardar_posicion_menu(pos)
        self.accept()