from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    FluentIcon as FIF,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SubtitleLabel,
    SwitchButton,
    TableWidget,
    Theme,
    qconfig,
    setTheme,
)

from models.usuario import Usuario
from models.validacion_identificador import (
    es_cuit_valido,
    normalizar_cuit,
    tipo_de_identificador,
)
from services.backup import ErrorBackup, ServicioBackup, tamano_legible
from services.autenticacion import Autenticacion
from services.gestor_anulaciones import MENSAJE_SIN_SERVICIO, GestorAnulaciones
from services.gestor_comercio import GestorComercio
from services.impresion import imprimir_codigo_anulacion
from services.plan_motor import CONTACTO
from services.preferencias import (
    guardar_modo_oscuro,
    guardar_mostrar_reloj,
    guardar_posicion_menu,
    modo_oscuro,
    mostrar_reloj,
    posicion_menu,
)
from ui.fluent import CLARO, OSCURO, color
from ui.manual.configuracion_ui import (
    BUTTON_EDICION,
    BUTTON_INICIAL,
    TEXTO_EDICION,
    TEXTO_INICIAL,
    TITULO_EDICION,
    TITULO_INICIAL,
)
from ui.widgets.notificacion import Notificacion
from ui.widgets.trabajo_impresion import TrabajoImpresion
from views.dialogo_password import DialogoCambiarPassword
from views.ventana_base import VentanaBase

MENSAJE_CONFIRMAR = "Esto reemplaza todos los datos actuales. ¿Continuar?"
SIN_CODIGO = "Todavía no generaste un código."
FUENTE_MONOESPACADA = "Monospace"
TAMANO_CODIGO = 26
ESTILO_SCROLL = (
    "QScrollArea { border: none; background: transparent; }"
    "QScrollArea > QWidget { background: transparent; }"
    "QScrollArea > QWidget > QWidget { background: transparent; }"
)
ANCHO_CONTENIDO = 480


def _envuelto(etiqueta: BodyLabel, ancho: int = ANCHO_CONTENIDO) -> None:
    """Fija el alto mínimo de una etiqueta con texto envuelto.

    Qt no recalcula el alto de una etiqueta con ``word wrap`` cuando cambia el
    ancho disponible, así que el alto se calcula a mano para que no queden
    líneas cortadas.
    """
    etiqueta.setMinimumHeight(max(0, etiqueta.heightForWidth(ancho)))


def _tinta(nombre: str) -> tuple[QColor, QColor]:
    """Devuelve el par (claro, oscuro) de un token Fluent para labels adaptativos."""
    return QColor(CLARO[nombre]), QColor(OSCURO[nombre])


class _UiConfiguracion:
    """Interfaz Fluent de la configuración.

    Conserva los nombres de widget heredados (``txtNombre``, ``lblError``…) para
    no romper el código ni los tests que los consultan.
    """

    def __init__(self, ventana: QWidget) -> None:
        self.contenido = QWidget(ventana)
        self.contenido.setObjectName("contenidoConfig")

        self.lblTitulo = SubtitleLabel("", ventana)
        self.lblTitulo.setObjectName("lblTitulo")
        self.lblTitulo.setWordWrap(True)

        self.lblNombre = BodyLabel("Nombre de tu comercio/emprendimiento *", ventana)
        self.lblNombre.setObjectName("lblNombre")
        self.txtNombre = LineEdit(ventana)
        self.txtNombre.setObjectName("txtNombre")
        self.txtNombre.setPlaceholderText("Ej: verdulería de barrio")

        self.lblDireccion = BodyLabel("Dirección", ventana)
        self.lblDireccion.setObjectName("lblDireccion")
        self.txtDireccion = LineEdit(ventana)
        self.txtDireccion.setObjectName("txtDireccion")
        self.txtDireccion.setPlaceholderText("Ej: artube 1232")

        self.lblCampoCuit = BodyLabel("CUIT", ventana)
        self.lblCampoCuit.setObjectName("lblCampoCuit")
        self.txtCuit = LineEdit(ventana)
        self.txtCuit.setObjectName("txtCuit")
        self.txtCuit.setPlaceholderText("Ej: 30-12345678-9")
        self.lblCuit = BodyLabel("", ventana)
        self.lblCuit.setObjectName("lblCuit")
        self.lblCuit.setTextColor(*_tinta("texto_secundario"))
        self.lblCuit.setWordWrap(True)

        self.lblTelefono = BodyLabel("Teléfono", ventana)
        self.lblTelefono.setObjectName("lblTelefono")
        self.txtTelefono = LineEdit(ventana)
        self.txtTelefono.setObjectName("txtTelefono")
        self.txtTelefono.setPlaceholderText("Ej: 1166666666")

        self.lblError = BodyLabel("", ventana)
        self.lblError.setObjectName("lblError")
        self.lblError.setTextColor(*_tinta("error"))
        self.lblError.setWordWrap(True)

        self.btnGuardar = PrimaryPushButton(BUTTON_INICIAL, ventana)
        self.btnGuardar.setObjectName("btnGuardar")
        self.btnGuardar.setAutoDefault(False)

        self.verticalLayout = QVBoxLayout(self.contenido)
        self.verticalLayout.setContentsMargins(16, 16, 16, 16)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.addWidget(self.lblTitulo)
        self.verticalLayout.addWidget(self._tarjeta_datos())
        self.verticalLayout.addStretch(1)

    def _tarjeta_datos(self) -> CardWidget:
        tarjeta = CardWidget(self.contenido)
        tarjeta.setObjectName("grpDatos")
        tarjeta.setBorderRadius(8)
        disposicion = QVBoxLayout(tarjeta)
        disposicion.setContentsMargins(16, 14, 16, 14)
        disposicion.setSpacing(8)
        disposicion.addWidget(SubtitleLabel("Datos del comercio", tarjeta))
        disposicion.addWidget(self.lblNombre)
        disposicion.addWidget(self.txtNombre)
        disposicion.addWidget(self.lblDireccion)
        disposicion.addWidget(self.txtDireccion)
        disposicion.addWidget(self.lblCampoCuit)
        disposicion.addWidget(self.txtCuit)
        disposicion.addWidget(self.lblCuit)
        disposicion.addWidget(self.lblTelefono)
        disposicion.addWidget(self.txtTelefono)
        disposicion.addWidget(self.lblError)
        return tarjeta

    def aplicar_modo(self, edicion: bool) -> None:
        """Ajusta el título y el botón según sea el alta inicial o la edición."""
        self.lblTitulo.setText(TEXTO_EDICION if edicion else TEXTO_INICIAL)
        self.btnGuardar.setText(BUTTON_EDICION if edicion else BUTTON_INICIAL)


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
        self.setObjectName("dlgConfiguracion")
        self.ui = _UiConfiguracion(self)
        self.ui.btnGuardar.clicked.connect(self.guardar)
        self.ui.lblError.setText("")
        self.ui.lblCampoCuit.setToolTip(
            "CUIT de una sociedad (30-…) o CUIL de un monotributista (20-…, 23-…, 24-…).")
        self.ui.lblCuit.setToolTip(
            "CUIT de una sociedad (30-…) o CUIL de un monotributista (20-…, 23-…, 24-…).")
        self._armar_scroll()
        self.ui.aplicar_modo(self._edicion)
        self.setWindowTitle(TITULO_EDICION if self._edicion else TITULO_INICIAL)
        self._cargar_comercio()
        self.ui.txtCuit.textChanged.connect(self.validar_cuit)
        self.ui.txtNombre.setFocus()
        self._armar_seccion_interfaz()
        self._armar_seccion_backups()
        self.cargar_backups()
        self._armar_seccion_fiado()
        self._armar_seccion_cuenta()
        self._armar_seccion_plan()
        self._armar_seccion_codigos()

        self._aplicar_tema()
        if hasattr(qconfig, "themeChanged"):
            qconfig.themeChanged.connect(self._aplicar_tema)

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema Fluent."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo_suave')}; }}")

    def _cargar_comercio(self) -> None:
        if self._comercio is None:
            return
        self.ui.txtNombre.setText(self._comercio.nombre)
        self.ui.txtDireccion.setText(self._comercio.direccion)
        self.ui.txtCuit.setText(self._comercio.cuit)
        self.ui.txtTelefono.setText(self._comercio.telefono)

    def _tarjeta(self, titulo: str) -> tuple[CardWidget, QVBoxLayout]:
        """Crea una tarjeta Fluent con su título y devuelve el layout del contenido."""
        tarjeta = CardWidget(self.ui.contenido)
        tarjeta.setBorderRadius(8)
        disposicion = QVBoxLayout(tarjeta)
        disposicion.setContentsMargins(16, 14, 16, 14)
        disposicion.setSpacing(8)
        disposicion.addWidget(SubtitleLabel(titulo, tarjeta))
        return tarjeta, disposicion

    def _agregar_seccion(self, tarjeta: CardWidget) -> None:
        """Coloca la tarjeta al final del contenido desplazable."""
        layout = self.ui.verticalLayout
        layout.insertWidget(layout.count() - 1, tarjeta)

    def _armar_scroll(self) -> None:
        area = ScrollArea(self)
        area.setObjectName("sbrConfig")
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setStyleSheet(ESTILO_SCROLL)
        self.ui.contenido.setAutoFillBackground(False)
        area.setWidget(self.ui.contenido)

        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)
        exterior.setSpacing(0)
        exterior.addWidget(area)

        pie = QWidget(self)
        layout_pie = QHBoxLayout(pie)
        layout_pie.setContentsMargins(16, 8, 16, 16)
        layout_pie.addStretch(1)
        layout_pie.addWidget(self.ui.btnGuardar)
        exterior.addWidget(pie)

        self.setMinimumSize(560, 540)
        self.setMaximumSize(1600, 1400)
        self.resize(560, 900)

    def _armar_seccion_interfaz(self) -> None:
        grupo, disposicion = self._tarjeta("Interfaz")
        grupo.setObjectName("grpInterfaz")

        fila = QHBoxLayout()
        fila.setSpacing(12)
        lbl = BodyLabel("Mostrar fecha y hora en la barra superior", grupo)
        lbl.setTextColor(*_tinta("texto_secundario"))
        fila.addWidget(lbl)
        fila.addStretch(1)

        self.swMostrarReloj = SwitchButton(grupo)
        self.swMostrarReloj.setObjectName("swMostrarReloj")
        self.swMostrarReloj.setOnText("Visible")
        self.swMostrarReloj.setOffText("Oculto")
        self.swMostrarReloj.setChecked(mostrar_reloj())
        fila.addWidget(self.swMostrarReloj)
        disposicion.addLayout(fila)

        self._agregar_seccion(grupo)

    def _armar_seccion_backups(self) -> None:
        grupo, disposicion = self._tarjeta("Copias de seguridad")
        grupo.setObjectName("grpBackups")

        self.lblRutaBackups = BodyLabel(grupo)
        self.lblRutaBackups.setObjectName("lblRutaBackups")
        self.lblRutaBackups.setWordWrap(True)
        self.lblRutaBackups.setTextColor(*_tinta("texto_secundario"))
        self.lblRutaBackups.setText(f"Se guardan en: {self._backup.directorio_backups()}")
        _envuelto(self.lblRutaBackups)
        disposicion.addWidget(self.lblRutaBackups)

        self.tblBackups = TableWidget(grupo)
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

        self.lblSinBackups = BodyLabel(grupo)
        self.lblSinBackups.setObjectName("lblSinBackups")
        self.lblSinBackups.setWordWrap(True)
        self.lblSinBackups.setTextColor(*_tinta("texto_secundario"))
        disposicion.addWidget(self.lblSinBackups)

        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnCopiarAhora = PushButton(FIF.SAVE, "Hacer copia ahora", grupo)
        self.btnCopiarAhora.setObjectName("btnCopiarAhora")
        self.btnCopiarAhora.clicked.connect(self.hacer_copia)
        botones.addWidget(self.btnCopiarAhora)
        self.btnRestaurar = PushButton(FIF.UPDATE, "Restaurar", grupo)
        self.btnRestaurar.setObjectName("btnRestaurar")
        self.btnRestaurar.clicked.connect(self.restaurar)
        botones.addWidget(self.btnRestaurar)
        botones.addStretch(1)
        disposicion.addLayout(botones)

        self._agregar_seccion(grupo)

    def _armar_seccion_fiado(self) -> None:
        return

    def _armar_seccion_cuenta(self) -> None:
        if not self._edicion or self._autenticacion is None:
            return
        usuario = self._autenticacion.usuario_actual
        if usuario is None:
            return
        grupo, disposicion = self._tarjeta("Cuenta")
        grupo.setObjectName("grpCuenta")

        ayuda = BodyLabel(
            f"Conectado como {usuario.nombre}. Podés cambiar tu contraseña.",
            grupo)
        ayuda.setWordWrap(True)
        ayuda.setTextColor(*_tinta("texto_secundario"))
        _envuelto(ayuda)
        disposicion.addWidget(ayuda)

        self.btnCambiarPassword = PushButton(
            FIF.PIN, "Cambiar contraseña", grupo)
        self.btnCambiarPassword.setObjectName("btnCambiarPassword")
        self.btnCambiarPassword.clicked.connect(self._cambiar_password)
        disposicion.addWidget(self.btnCambiarPassword)

        self._agregar_seccion(grupo)

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
        grupo, disposicion = self._tarjeta("Edición y funciones")
        grupo.setObjectName("grpPlan")

        self.lblPlan = BodyLabel(grupo)
        self.lblPlan.setObjectName("lblPlan")
        disposicion.addWidget(self.lblPlan)

        self.lblLimites = BodyLabel(grupo)
        self.lblLimites.setObjectName("lblLimites")
        self.lblLimites.setWordWrap(True)
        disposicion.addWidget(self.lblLimites)

        self.btnVerPlanes = PushButton(FIF.INFO, "Conocé más funciones en la web", grupo)
        self.btnVerPlanes.setObjectName("btnVerPlanes")
        self.btnVerPlanes.clicked.connect(self._ver_planes)
        disposicion.addWidget(self.btnVerPlanes)

        self._agregar_seccion(grupo)
        self._refrescar_plan()

    def _armar_seccion_codigos(self) -> None:
        grupo, disposicion = self._tarjeta("Códigos de anulación")
        grupo.setObjectName("grpCodigos")

        self.lblAyudaCodigos = BodyLabel(grupo)
        self.lblAyudaCodigos.setObjectName("lblAyudaCodigos")
        self.lblAyudaCodigos.setWordWrap(True)
        self.lblAyudaCodigos.setTextColor(*_tinta("texto_secundario"))
        self.lblAyudaCodigos.setText(
            "El código lo tiene el supervisor y sirve para anular ventas. "
            "Se muestra una sola vez, al generarlo: después queda solo el hash.")
        _envuelto(self.lblAyudaCodigos)
        disposicion.addWidget(self.lblAyudaCodigos)

        self.lblSinCodigo = BodyLabel(grupo)
        self.lblSinCodigo.setObjectName("lblSinCodigo")
        self.lblSinCodigo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblSinCodigo.setTextColor(*_tinta("texto_secundario"))
        self.lblSinCodigo.setText(SIN_CODIGO)
        disposicion.addWidget(self.lblSinCodigo)

        self.lblCodigoGenerado = BodyLabel(grupo)
        self.lblCodigoGenerado.setObjectName("lblCodigoGenerado")
        self.lblCodigoGenerado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fuente_codigo = QFont(FUENTE_MONOESPACADA)
        fuente_codigo.setPointSize(TAMANO_CODIGO)
        fuente_codigo.setBold(True)
        self.lblCodigoGenerado.setFont(fuente_codigo)
        self.lblCodigoGenerado.setVisible(False)
        disposicion.addWidget(self.lblCodigoGenerado)

        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnGenerarCodigo = PushButton(
            FIF.ADD, "Generar código", grupo)
        self.btnGenerarCodigo.setObjectName("btnGenerarCodigo")
        self.btnGenerarCodigo.clicked.connect(self.generar_codigo)
        botones.addWidget(self.btnGenerarCodigo)

        self.btnCopiarCodigo = PushButton(FIF.COPY, "Copiar", grupo)
        self.btnCopiarCodigo.setObjectName("btnCopiarCodigo")
        self.btnCopiarCodigo.setEnabled(False)
        self.btnCopiarCodigo.clicked.connect(self.copiar_codigo)
        botones.addWidget(self.btnCopiarCodigo)

        self.btnImprimirCodigo = PushButton(FIF.PRINT, "Imprimir", grupo)
        self.btnImprimirCodigo.setObjectName("btnImprimirCodigo")
        self.btnImprimirCodigo.setEnabled(False)
        self.btnImprimirCodigo.setToolTip("Imprime el código con la impresora del sistema.")
        self.btnImprimirCodigo.clicked.connect(self.imprimir_codigo)
        botones.addWidget(self.btnImprimirCodigo)
        botones.addStretch(1)
        disposicion.addLayout(botones)

        self.tblCodigos = TableWidget(grupo)
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

        self.btnRevocarCodigo = PushButton(FIF.REMOVE, "Revocar", grupo)
        self.btnRevocarCodigo.setObjectName("btnRevocarCodigo")
        self.btnRevocarCodigo.clicked.connect(self.revocar_codigo)
        disposicion.addWidget(self.btnRevocarCodigo)

        self._agregar_seccion(grupo)
        self.cargar_codigos()

    def cargar_codigos(self) -> None:
        if self._anulaciones is None:
            self.btnRevocarCodigo.setEnabled(False)
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
            self.mostrar_advertencia("Revocar código", "Ese código ya está revocado.")
            return
        if not self.confirmar(
            "Revocar código",
            f"¿Revocar el código de {codigo.etiqueta or 'el supervisor'}?\n\n"
            "Después no se va a poder anular ninguna venta con ese código.",
        ):
            return
        self._anulaciones.revocar_codigo(codigo.identificador)
        self.cargar_codigos()
        Notificacion(self).mostrar("Código revocado", "El código ya no sirve para anular ventas.")

    def _refrescar_plan(self) -> None:
        self.lblPlan.setText("BetterStock — Edición Libre")
        self.lblLimites.setText("Para conocer más funciones avanzadas, visitá la web oficial de BetterStock Pro.")
        _envuelto(self.lblLimites)

    def _ver_planes(self) -> None:
        QDesktopServices.openUrl(QUrl("https://betterstock.tech"))

    def validar_cuit(self, texto: str) -> None:
        if not texto.strip():
            self.ui.lblCuit.setTextColor(*_tinta("texto_secundario"))
            self.ui.lblCuit.setText("")
            return
        if es_cuit_valido(texto):
            tipo = tipo_de_identificador(texto)
            etiqueta = "sociedad" if tipo == "sociedad" else "monotributista"
            self.ui.lblCuit.setTextColor(*_tinta("exito"))
            self.ui.lblCuit.setText(f"{normalizar_cuit(texto)} — {etiqueta}")
            _envuelto(self.ui.lblCuit)
            return
        self.ui.lblCuit.setTextColor(*_tinta("alerta"))
        self.ui.lblCuit.setText("Revisá el CUIT: son 11 dígitos y el último es verificador.")
        _envuelto(self.ui.lblCuit)

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
        _envuelto(self.lblSinBackups)
        self.btnRestaurar.setEnabled(hay)

    def _copia_seleccionada(self):
        fila = self.tblBackups.currentRow()
        if fila < 0 and self.tblBackups.selectedItems():
            fila = self.tblBackups.selectedItems()[0].row()
        if fila < 0 or fila >= len(self._copias):
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
            _envuelto(self.ui.lblError)
            return

        if hasattr(self, "cmbPosicionMenu"):
            pos = self.cmbPosicionMenu.currentData() or "izquierda"
            guardar_posicion_menu(pos)
        if hasattr(self, "chkModoOscuro"):
            guardar_modo_oscuro(self.chkModoOscuro.isChecked())
        if hasattr(self, "swMostrarReloj"):
            guardar_mostrar_reloj(self.swMostrarReloj.isChecked())
        self.accept()
