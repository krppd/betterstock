from __future__ import annotations

import math
from datetime import date
from typing import Any

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CalendarPicker,
    DoubleSpinBox,
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SimpleCardWidget,
    SubtitleLabel,
    TableWidget,
    TransparentPushButton,
    isDarkTheme,
    qconfig,
)

from models.caja_movimiento import CajaMovimiento
from models.cierre import Cierre, CierreRegistrado
from services.caja import ErrorCaja, ServicioCaja
from services.cierre_caja import ErrorCierre, ServicioCierre
from services.turnos import ServicioTurnos
from ui.estilos import TAMANO_SMALL, escala, fuente
from ui.fluent import CLARO, OSCURO, color
from ui.widgets.boton_rodante import BotonRodante
from ui.widgets.notificacion import Notificacion
from utils.formato import diferencia as diferencia_montos
from utils.formato import formatear_dinero
from views.dialogo_anulacion import DialogoAnulacion
from views.dialogo_cerrar_caja import DialogoCerrarCaja
from views.dialogo_movimiento_caja import DialogoMovimientoCaja
from views.seccion_turnos import SeccionTurnos
from views.tarjeta_caja import TarjetaHistorialCierre, TarjetaMovimientoCaja
from views.ventana_base import VentanaBase

MAXIMO_EFECTIVO = 1_000_000_000_000.0

_APLICACION: QApplication | None = None


def conservar_aplicacion() -> None:
    """Mantiene viva la QApplication de la sesión (ver ``_APLICACION``)."""
    global _APLICACION
    app = QApplication.instance()
    if app is not None:
        _APLICACION = app


def _tinta(nombre: str) -> tuple[QColor, QColor]:
    """Devuelve el par (claro, oscuro) de un token Fluent para labels adaptativos."""
    return QColor(CLARO[nombre]), QColor(OSCURO[nombre])


class DateCompat(QDate):
    def __call__(self) -> QDate:
        return self


class SelectorFechaCaja(CalendarPicker):
    """CalendarPicker con compatibilidad de API para date().toPyDate() y setDate()."""

    @property
    def date(self) -> DateCompat:
        d = self.getDate()
        d_val = d if d.isValid() else QDate.currentDate()
        return DateCompat(d_val.year(), d_val.month(), d_val.day())

    @date.setter
    def date(self, fecha: Any) -> None:
        self.setDate(fecha)

    def setDate(self, fecha: Any) -> None:
        if hasattr(fecha, "year") and not callable(fecha.year):
            fecha = QDate(fecha.year, fecha.month, fecha.day)
        super().setDate(fecha)


class _UiCaja:
    """Namespace con los widgets de la ventana de caja.

    Conserva la forma ``self.ui.<widget>`` que usan el resto del código
    y los tests, ahora sobre componentes Fluent.
    """


class VentanaCaja(QWidget, VentanaBase):
    """Panel de caja: arqueo del día, movimientos, turno e historial de cierres."""

    ESTILO_ESTADO = (
        "QPushButton#btnEstadoCaja {"
        "  background-color: {fondo};"
        "  color: {texto};"
        "  border: 1px solid {borde};"
        "  border-radius: 8px;"
        "  padding: 4px 12px;"
        "  font-weight: bold;"
        "  min-height: 28px;"
        "}"
        "QPushButton#btnEstadoCaja:hover {"
        "  background-color: {fondo_hover};"
        "  border-color: {borde_hover};"
        "}"
    )
    ESTILO_ABIERTA = ESTILO_ESTADO
    ESTILO_CERRADA = ESTILO_ESTADO
    ESTILO_GLOBAL = ""

    def __init__(self, servicio: ServicioCierre, usuario: str = "",
                 permiso: str = "", turnos: ServicioTurnos | None = None,
                 caja: ServicioCaja | None = None,
                 nombre_comercio: str = "") -> None:
        super().__init__()
        conservar_aplicacion()
        self.setWindowTitle("Caja")
        self._servicio = servicio
        self._turnos = turnos
        self._caja = caja if caja is not None else getattr(servicio, "caja", None)
        self._usuario = usuario
        self._nombre_comercio = nombre_comercio
        self._ciego = False
        self._estado_previo: bool | None = None
        self._medios_colapsados: bool = False
        self._movimientos_cache: list[CajaMovimiento] = []
        self._arqueo_actual: Cierre | None = None

        self.ui = _UiCaja()
        self._iniciar_interfaz()

        self.btnEgreso = self.ui.btnEgreso
        self.btnIngreso = self.ui.btnIngreso
        self.btnAnularMovimiento = self.ui.btnAnularMovimiento
        self.lblMovimientos = self.ui.lblMovimientos
        self._tarjetas_movimientos: list[TarjetaMovimientoCaja] = []
        self._tarjetas_historial: list[TarjetaHistorialCierre] = []
        self._indice_seleccionado: int | None = None

        self.btnEgreso.clicked.connect(self.registrar_egreso)
        self.btnIngreso.clicked.connect(self.registrar_ingreso)
        self.btnAnularMovimiento.clicked.connect(self.anular_movimiento)
        self.ui.btnToggleMedios.clicked.connect(self._toggle_medios)

        self.seccion_turnos: SeccionTurnos | None = None
        if turnos is not None:
            self.seccion_turnos = SeccionTurnos(turnos, usuario, permiso, self, caja=self._caja)
            self.ui.contenedorTurnos.addWidget(self.seccion_turnos)

        self.ui.dateDia.setDate(date.today())
        self.ui.dateDia.dateChanged.connect(self.recalcular)
        self.ui.btnHoy.clicked.connect(self.ir_a_hoy)
        self.ui.btnRefrescar.clicked.connect(self.recalcular)
        self.ui.btnEstado.clicked.connect(self.recalcular)
        for columna, ancho in enumerate((115, 95, 70, 140, 110)):
            self.ui.tblHistorial.setColumnWidth(columna, round(ancho * escala()))
        self.ui.spnEfectivo.valueChanged.connect(self.actualizar_diferencia)
        self.ui.btnCerrarCaja.clicked.connect(self.cerrar_caja)
        qconfig.themeChanged.connect(self._aplicar_tema)
        self.recalcular()

    def _iniciar_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        layout.addWidget(self._armar_cabecera())
        layout.addWidget(self._armar_arqueo())
        layout.addWidget(self._armar_declarado())
        layout.addLayout(self._armar_acciones())
        layout.addLayout(self._armar_paneles(), 1)

        self.setMinimumSize(760, 620)

    def _armar_cabecera(self) -> SimpleCardWidget:
        """Tarjeta superior con el día, los atajos y el estado de la caja."""
        tarjeta = SimpleCardWidget(self)
        lay = QVBoxLayout(tarjeta)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        fila = QHBoxLayout()
        fila.setSpacing(8)

        self.ui.lblDia = BodyLabel("Día:", tarjeta)
        self.ui.lblDia.setTextColor(*_tinta("texto"))

        self.ui.dateDia = SelectorFechaCaja(tarjeta)
        self.ui.dateDia.setObjectName("dateDia")

        self.ui.btnHoy = PushButton("Hoy", tarjeta)
        self.ui.btnHoy.setObjectName("btnHoy")

        self.ui.btnRefrescar = PushButton(FIF.SYNC, "Recalcular", tarjeta)
        self.ui.btnRefrescar.setObjectName("btnRefrescar")

        self.ui.btnEstado = BotonRodante(parent=tarjeta, escalon=0)
        self.ui.btnEstado.setObjectName("btnEstadoCaja")
        self.ui.btnEstado.setCentrado(True)
        self.ui.btnEstado.setMinimumSize(150, 30)
        self.ui.btnEstado.setCursor(Qt.CursorShape.PointingHandCursor)

        fila.addWidget(self.ui.lblDia)
        fila.addWidget(self.ui.dateDia)
        fila.addWidget(self.ui.btnHoy)
        fila.addWidget(self.ui.btnRefrescar)
        fila.addStretch(1)
        fila.addWidget(self.ui.btnEstado)
        lay.addLayout(fila)
        return tarjeta

    def _armar_arqueo(self) -> SimpleCardWidget:
        """Tarjeta con el turno de caja, el esperado y los medios de pago."""
        tarjeta = SimpleCardWidget(self)
        lay = QVBoxLayout(tarjeta)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        self.ui.contenedorTurnos = QHBoxLayout()
        self.ui.contenedorTurnos.setObjectName("contenedorTurnos")
        self.ui.contenedorTurnos.setSpacing(8)
        lay.addLayout(self.ui.contenedorTurnos)

        self.ui.hlyResumen = QHBoxLayout()
        self.ui.hlyResumen.setObjectName("hlyResumen")
        self.ui.hlyResumen.setSpacing(8)

        self.ui.lblEsperado = BodyLabel("", tarjeta)
        self.ui.lblEsperado.setObjectName("lblEsperado")
        self.ui.lblEsperado.setWordWrap(True)
        self.ui.lblEsperado.setTextColor(*_tinta("texto"))

        self.ui.btnToggleMedios = TransparentPushButton("Medios de pago ▾", tarjeta)
        self.ui.btnToggleMedios.setObjectName("btnToggleMedios")

        self.ui.hlyResumen.addWidget(self.ui.lblEsperado, 1)
        self.ui.hlyResumen.addWidget(self.ui.btnToggleMedios)
        lay.addLayout(self.ui.hlyResumen)

        self.ui.tblMedios = QFrame(tarjeta)
        self.ui.tblMedios.setObjectName("tblMedios")
        self.ui.hlyMedios = QHBoxLayout(self.ui.tblMedios)
        self.ui.hlyMedios.setContentsMargins(0, 0, 0, 0)
        self.ui.hlyMedios.setSpacing(8)
        lay.addWidget(self.ui.tblMedios)
        return tarjeta

    def _armar_declarado(self) -> SimpleCardWidget:
        """Tarjeta con el efectivo contado y la diferencia respecto del esperado."""
        tarjeta = SimpleCardWidget(self)
        lay = QHBoxLayout(tarjeta)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        self.ui.lblDeclarado = BodyLabel("Efectivo contado en el cajón:", tarjeta)
        self.ui.lblDeclarado.setTextColor(*_tinta("texto"))

        self.ui.spnEfectivo = DoubleSpinBox(tarjeta)
        self.ui.spnEfectivo.setObjectName("spnEfectivo")
        self.ui.spnEfectivo.setDecimals(2)
        self.ui.spnEfectivo.setMinimum(0.0)
        self.ui.spnEfectivo.setMaximum(MAXIMO_EFECTIVO)
        self.ui.spnEfectivo.setMinimumWidth(160)

        self.ui.lblDiferencia = BodyLabel("", tarjeta)
        self.ui.lblDiferencia.setObjectName("lblDiferencia")
        self.ui.lblDiferencia.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(self.ui.lblDeclarado)
        lay.addWidget(self.ui.spnEfectivo)
        lay.addWidget(self.ui.lblDiferencia, 1)
        return tarjeta

    def _armar_acciones(self) -> QHBoxLayout:
        """Fila con los ingresos, egresos y el cierre del día."""
        fila = QHBoxLayout()
        fila.setSpacing(10)

        self.ui.btnEgreso = PushButton(FIF.REMOVE, "Egreso de caja", self)
        self.ui.btnEgreso.setObjectName("btnEgresoCaja")

        self.ui.btnIngreso = PushButton(FIF.ADD, "Ingreso de caja", self)
        self.ui.btnIngreso.setObjectName("btnIngresoCaja")

        self.ui.btnCerrarCaja = PrimaryPushButton(FIF.ACCEPT_MEDIUM, "Cerrar caja", self)
        self.ui.btnCerrarCaja.setObjectName("btnCerrarCaja")

        fila.addWidget(self.ui.btnEgreso)
        fila.addWidget(self.ui.btnIngreso)
        fila.addWidget(self.ui.btnCerrarCaja)
        return fila

    def _armar_paneles(self) -> QHBoxLayout:
        """Paneles lado a lado: movimientos del día e historial de cierres."""
        paneles = QHBoxLayout()
        paneles.setObjectName("hlyPanelesCaja")
        paneles.setSpacing(14)
        self.ui.hlyPaneles = paneles

        tarjeta_mov = SimpleCardWidget(self)
        lay_mov = QVBoxLayout(tarjeta_mov)
        lay_mov.setContentsMargins(16, 12, 16, 12)
        lay_mov.setSpacing(8)

        cabecera_mov = QHBoxLayout()
        cabecera_mov.setSpacing(8)
        self.ui.lblMovimientos = SubtitleLabel("Movimientos del día", tarjeta_mov)
        self.ui.lblMovimientos.setObjectName("lblMovimientosCaja")
        self.ui.lblMovimientos.setTextColor(*_tinta("texto"))
        self.ui.btnAnularMovimiento = PushButton(
            FIF.DELETE, "Anular movimiento", tarjeta_mov)
        self.ui.btnAnularMovimiento.setObjectName("btnAnularMovimientoCierre")
        cabecera_mov.addWidget(self.ui.lblMovimientos)
        cabecera_mov.addStretch(1)
        cabecera_mov.addWidget(self.ui.btnAnularMovimiento)
        lay_mov.addLayout(cabecera_mov)

        self.ui.scrollMovimientos = ScrollArea(tarjeta_mov)
        self.ui.scrollMovimientos.setObjectName("scrollMovimientosCaja")
        self.ui.scrollMovimientos.setWidgetResizable(True)
        self.ui.scrollMovimientos.setMaximumHeight(300)
        self.ui.scrollMovimientos.setFrameShape(QFrame.Shape.NoFrame)
        self.ui.scrollMovimientos.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.ui.contenedorMovimientos = QWidget()
        self.ui.contenedorMovimientos.setObjectName("contenedorMovimientosCaja")
        self.ui.vlyTarjetasMovimientos = QVBoxLayout(self.ui.contenedorMovimientos)
        self.ui.vlyTarjetasMovimientos.setContentsMargins(0, 0, 0, 0)
        self.ui.vlyTarjetasMovimientos.setSpacing(6)
        self.ui.scrollMovimientos.setWidget(self.ui.contenedorMovimientos)
        self._scroll_transparente(self.ui.scrollMovimientos)
        lay_mov.addWidget(self.ui.scrollMovimientos, 1)
        paneles.addWidget(tarjeta_mov, 1)

        tarjeta_hist = SimpleCardWidget(self)
        lay_hist = QVBoxLayout(tarjeta_hist)
        lay_hist.setContentsMargins(16, 12, 16, 12)
        lay_hist.setSpacing(8)

        self.ui.hlyHistHeader = QHBoxLayout()
        self.ui.hlyHistHeader.setSpacing(8)
        self.ui.lblHistorial = SubtitleLabel("Historial de cierres", tarjeta_hist)
        self.ui.lblHistorial.setObjectName("lblHistorial")
        self.ui.lblHistorial.setTextColor(*_tinta("texto"))
        self.ui.hlyHistHeader.addWidget(self.ui.lblHistorial)
        self.ui.hlyHistHeader.addStretch(1)
        lay_hist.addLayout(self.ui.hlyHistHeader)

        self.ui.tblHistorial = TableWidget(tarjeta_hist)
        self.ui.tblHistorial.setObjectName("tblHistorial")
        self.ui.tblHistorial.setColumnCount(6)
        self.ui.tblHistorial.setHorizontalHeaderLabels(
            ["Fecha", "Hora", "Ventas", "Esperado", "Diferencia", "Usuario"])
        self.ui.tblHistorial.setBorderVisible(True)
        self.ui.tblHistorial.setBorderRadius(8)
        self.ui.tblHistorial.setVisible(False)

        self.ui.scrollHistorial = ScrollArea(tarjeta_hist)
        self.ui.scrollHistorial.setObjectName("scrollHistorialCaja")
        self.ui.scrollHistorial.setWidgetResizable(True)
        self.ui.scrollHistorial.setMaximumHeight(300)
        self.ui.scrollHistorial.setFrameShape(QFrame.Shape.NoFrame)
        self.ui.scrollHistorial.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.ui.contenedorHistorial = QWidget()
        self.ui.contenedorHistorial.setObjectName("contenedorHistorialCaja")
        self.ui.gridHistorial = QGridLayout(self.ui.contenedorHistorial)
        self.ui.gridHistorial.setContentsMargins(0, 0, 0, 0)
        self.ui.gridHistorial.setSpacing(8)
        self.ui.scrollHistorial.setWidget(self.ui.contenedorHistorial)
        self._scroll_transparente(self.ui.scrollHistorial)
        lay_hist.addWidget(self.ui.scrollHistorial, 1)
        paneles.addWidget(tarjeta_hist, 1)

        return paneles

    @staticmethod
    def _scroll_transparente(scroll: ScrollArea) -> None:
        """Deja el área de scroll sin marco y con el fondo transparente."""
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        viewport = scroll.viewport()
        viewport.setAutoFillBackground(False)
        viewport.setStyleSheet(
            "QWidget#qt_scrollarea_viewport { background: transparent; border: none; }")
        scroll.widget().setAutoFillBackground(False)

    def al_mostrar(self) -> None:
        self.recalcular()

    @property
    def dia(self) -> date:
        return self.ui.dateDia.date().toPyDate()

    def ir_a_hoy(self) -> None:
        self.ui.dateDia.setDate(date.today())
        self.recalcular()

    def recalcular(self) -> None:
        if self._caja is None:
            self._caja = getattr(self._servicio, "caja", None)
            if self.seccion_turnos is not None and self.seccion_turnos.caja is None:
                self.seccion_turnos.caja = self._caja

        turno_abierto = False
        if self._turnos is not None:
            turno = self._turnos.abierto()
            turno_abierto = (turno is not None)

        ya_cerrado = self._servicio.ya_cerrado(self.dia)
        if turno_abierto:
            ya_cerrado = False

        if self.seccion_turnos is not None:
            self.seccion_turnos.actualizar(dia_cerrado=ya_cerrado)

        arqueo = self._servicio.arqueo(self.dia)
        self._arqueo_actual = arqueo
        self._cargar_medios(arqueo)
        self._mostrar_esperado(arqueo)
        self._mostrar_estado_del_dia(ya_cerrado, turno_abierto)
        self._proponer_efectivo(arqueo.esperado_por_medio.efectivo)
        self.actualizar_diferencia()
        self.cargar_historial()
        self._cargar_movimientos()
        self._ajustar_alturas_paneles()

    def _aplicar_tema(self) -> None:
        """Reaplica los colores dependientes del tema (claro/oscuro)."""
        try:
            if self._estado_previo is not None:
                self._mostrar_estado_del_dia(self._estado_previo)
            if self._arqueo_actual is not None:
                self._cargar_medios(self._arqueo_actual)
            self.actualizar_diferencia()
        except Exception:
            pass

    def _ajustar_alturas_paneles(self) -> None:
        """Ajusta las dos scrolls según la cantidad de tarjetas (sin huecos fijos)."""
        movs = len(getattr(self, "_movimientos_cache", []) or [])
        alto_mov = 70 if movs == 0 else min(86 + (movs - 1) * 66, 300)

        n_hist = len(getattr(self, "_tarjetas_historial", []) or [])
        alto_hist = 70 if n_hist == 0 else min(74 + (n_hist - 1) * 74, 300)

        self.ui.scrollMovimientos.setMinimumHeight(alto_mov)
        self.ui.scrollMovimientos.setMaximumHeight(300)
        self.ui.scrollHistorial.setMinimumHeight(alto_hist)
        self.ui.scrollHistorial.setMaximumHeight(300)
        self.ui.scrollMovimientos.updateGeometry()
        self.ui.scrollHistorial.updateGeometry()

    def _toggle_medios(self) -> None:
        self._medios_colapsados = not self._medios_colapsados
        self.ui.tblMedios.setVisible(not self._medios_colapsados)
        self.ui.btnToggleMedios.setText("Medios de pago ▾" if self._medios_colapsados else "Ocultar medios ▴")

    def _cargar_medios(self, arqueo: Cierre) -> None:
        self.ui.btnToggleMedios.setVisible(True)
        self.ui.tblMedios.setVisible(not self._medios_colapsados)
        self.ui.btnToggleMedios.setText("Medios de pago ▾" if self._medios_colapsados else "Ocultar medios ▴")
        if not hasattr(self.ui, "hlyMedios"):
            return
        while self.ui.hlyMedios.count() > 0:
            item = self.ui.hlyMedios.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        filas = [[etiqueta, formatear_dinero(importe)] for etiqueta, _, importe in arqueo.esperado_por_medio.filas()]
        if not filas:
            filas = [["Sin ventas cobradas", formatear_dinero(0.0)]]
        for etiqueta, importe_str in filas:
            lbl_medio = QLabel(f"{etiqueta}: {importe_str}", self.ui.tblMedios)
            lbl_medio.setFont(fuente(TAMANO_SMALL, negrita=True, tabular=True))
            lbl_medio.setStyleSheet(
                f"background-color: {color('fondo_suave')}; color: {color('gris_medio')}; "
                f"border: 1px solid {color('borde_suave')}; border-radius: 6px; padding: 3px 8px;"
            )
            self.ui.hlyMedios.addWidget(lbl_medio)
        self.ui.hlyMedios.addStretch(1)

    def _mostrar_esperado(self, arqueo: Cierre) -> None:
        v_efec = formatear_dinero(arqueo.ventas_efectivo)
        c_fiad = formatear_dinero(arqueo.cobros_fiado_efectivo)
        e_egr = formatear_dinero(arqueo.egresos)
        i_ing = formatear_dinero(arqueo.ingresos)
        t_esp = formatear_dinero(arqueo.esperado_por_medio.efectivo)

        self.ui.lblEsperado.setText(
            f"<b>Esperado en el cajón: <span style='color: {color('exito')}; font-size: 15px;'>{t_esp}</span></b>"
            f"<br>"
            f"<span style='color: {color('gris_medio')}; font-size: 12px;'>"
            f"Ventas efectivo: {v_efec} &nbsp;·&nbsp; "
            f"Cobros fiado: {c_fiad} &nbsp;·&nbsp; "
            f"Ingresos: +{i_ing} &nbsp;·&nbsp; "
            f"Egresos: −{e_egr}"
            f"</span>"
        )

    def _cargar_movimientos(self) -> None:
        self._movimientos_cache = []
        self._tarjetas_movimientos = []
        self._indice_seleccionado = None

        while self.ui.vlyTarjetasMovimientos.count() > 0:
            item = self.ui.vlyTarjetasMovimientos.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if self._caja is None:
            lbl_vacio = BodyLabel("Servicio de caja no disponible", self.ui.contenedorMovimientos)
            lbl_vacio.setFont(fuente(TAMANO_SMALL))
            lbl_vacio.setTextColor(*_tinta("gris_apagado"))
            lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.vlyTarjetasMovimientos.addWidget(lbl_vacio)
            return

        self._movimientos_cache = self._caja.listar_del_dia(self.dia)
        movimientos_ordenados = list(reversed(self._movimientos_cache))
        if not movimientos_ordenados:
            lbl_vacio = BodyLabel("Sin movimientos en el día", self.ui.contenedorMovimientos)
            lbl_vacio.setFont(fuente(TAMANO_SMALL))
            lbl_vacio.setTextColor(*_tinta("gris_apagado"))
            lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.vlyTarjetasMovimientos.addWidget(lbl_vacio)
            self.ui.vlyTarjetasMovimientos.addStretch(1)
            return

        for idx, m in enumerate(movimientos_ordenados):
            tarjeta = TarjetaMovimientoCaja(
                movimiento=m,
                indice=idx,
                on_click=self.seleccionar_movimiento,
                parent=self.ui.contenedorMovimientos,
            )
            self.ui.vlyTarjetasMovimientos.addWidget(tarjeta)
            self._tarjetas_movimientos.append(tarjeta)

        self.ui.vlyTarjetasMovimientos.addStretch(1)

    def seleccionar_movimiento(self, indice: int) -> None:
        self._indice_seleccionado = indice
        for tarjeta in self._tarjetas_movimientos:
            tarjeta.set_seleccionada(tarjeta.indice == indice)

    def registrar_egreso(self) -> None:
        if self._servicio.ya_cerrado(self.dia):
            self.mostrar_advertencia(
                "Caja cerrada", "No se pueden registrar movimientos en un día cerrado.")
            return
        if self._caja is None:
            self.mostrar_advertencia(
                "Caja", "El servicio de caja no está disponible.")
            return

        dialogo = DialogoMovimientoCaja(self, tipo_defecto=CajaMovimiento.TIPO_EGRESO)
        if dialogo.exec() != QDialog.DialogCode.Accepted or dialogo.datos is None:
            return

        tipo, concepto, categoria, importe = dialogo.datos
        try:
            self._caja.registrar(
                tipo=tipo,
                concepto=concepto,
                importe=importe,
                categoria=categoria,
                usuario=self._usuario,
                fecha=self.dia,
            )
        except ErrorCaja as error:
            self.mostrar_advertencia("Movimiento de caja", str(error))
            return

        self.recalcular()

    def registrar_ingreso(self) -> None:
        if self._servicio.ya_cerrado(self.dia):
            self.mostrar_advertencia(
                "Caja cerrada", "No se pueden registrar movimientos en un día cerrado.")
            return
        if self._caja is None:
            self.mostrar_advertencia(
                "Caja", "El servicio de caja no está disponible.")
            return

        dialogo = DialogoMovimientoCaja(self, tipo_defecto=CajaMovimiento.TIPO_INGRESO)
        if dialogo.exec() != QDialog.DialogCode.Accepted or dialogo.datos is None:
            return

        tipo, concepto, categoria, importe = dialogo.datos
        try:
            self._caja.registrar(
                tipo=tipo,
                concepto=concepto,
                importe=importe,
                categoria=categoria,
                usuario=self._usuario,
                fecha=self.dia,
            )
        except ErrorCaja as error:
            self.mostrar_advertencia("Movimiento de caja", str(error))
            return

        self.recalcular()

    def anular_movimiento(self) -> None:
        if (self._indice_seleccionado is None
                or self._indice_seleccionado < 0
                or self._indice_seleccionado >= len(self._tarjetas_movimientos)):
            self.mostrar_advertencia(
                "Anular movimiento", "Seleccioná un movimiento de la lista para anular.")
            return

        tarjeta = self._tarjetas_movimientos[self._indice_seleccionado]
        movimiento = tarjeta.movimiento
        if movimiento.anulado:
            self.mostrar_advertencia(
                "Anular movimiento", "Este movimiento ya está anulado.")
            return

        if self._servicio.ya_cerrado(movimiento.fecha):
            self.mostrar_advertencia(
                "Caja cerrada", "No se puede anular un movimiento de un día cerrado.")
            return

        validador = None
        if self._caja is not None and getattr(self._caja, "_codigos", None) is not None:
            validador = lambda c: bool(self._caja._codigos.buscar_activo_por_codigo(c))
        elif self._caja is not None and getattr(self._caja, "_gestor_anulaciones", None) is not None:
            validador = self._caja._gestor_anulaciones.codigo_valido

        dialogo = DialogoAnulacion(
            self,
            f"{movimiento.tipo.capitalize()} por {formatear_dinero(movimiento.importe)} - {movimiento.concepto}",
            validar_codigo=validador,
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        codigo, motivo = dialogo.resultado
        try:
            self._caja.anular(
                movimiento.id_movimiento, codigo, motivo,
                anulado_por=self._usuario)
        except ErrorCaja as error:
            self.mostrar_advertencia("Anular movimiento", str(error))
            return

        self.recalcular()

    def _mostrar_estado_del_dia(self, ya_cerrado: bool, turno_abierto: bool = False) -> None:
        if ya_cerrado:
            self.ui.btnEstado.setText("● Caja cerrada")
            self.ui.btnEstado.setStyleSheet(self._estilo_estado(False))
            self.ui.btnCerrarCaja.setEnabled(False)
            self.btnEgreso.setEnabled(False)
            self.btnIngreso.setEnabled(False)
            self.btnAnularMovimiento.setEnabled(False)
        else:
            self.ui.btnEstado.setText("● Caja abierta")
            self.ui.btnEstado.setStyleSheet(self._estilo_estado(True))
            self.ui.btnCerrarCaja.setEnabled(True)
            self.btnEgreso.setEnabled(True)
            self.btnIngreso.setEnabled(True)
            self.btnAnularMovimiento.setEnabled(True)
        self._estado_previo = ya_cerrado

    def _estilo_estado(self, abierto: bool) -> str:
        """QSS del indicador de estado con los colores del tema activo."""
        if abierto:
            tokens = {
                "fondo": color("pastilla_positiva"),
                "fondo_hover": color("pastilla_positiva"),
                "texto": color("acento") if isDarkTheme() else color("exito"),
                "borde": color("borde"),
                "borde_hover": color("acento"),
            }
        else:
            tokens = {
                "fondo": color("pastilla_negativa"),
                "fondo_hover": color("pastilla_negativa"),
                "texto": color("error"),
                "borde": color("borde"),
                "borde_hover": color("error"),
            }
        estilo = self.ESTILO_ESTADO
        for clave, valor in tokens.items():
            estilo = estilo.replace("{" + clave + "}", valor)
        return estilo

    def _proponer_efectivo(self, efectivo: float) -> None:
        if math.isfinite(efectivo):
            self.ui.spnEfectivo.setMaximum(
                max(self.ui.spnEfectivo.maximum(), math.ceil(efectivo)))
        self.ui.spnEfectivo.blockSignals(True)
        self.ui.spnEfectivo.setValue(max(efectivo, 0.0))
        self.ui.spnEfectivo.blockSignals(False)

    def actualizar_diferencia(self) -> None:
        arqueo = self._servicio.arqueo(self.dia)
        diferencia = float(diferencia_montos(
            self.ui.spnEfectivo.value(), arqueo.esperado_por_medio.efectivo))
        if abs(diferencia) < 0.01:
            self.ui.lblDiferencia.setText("Cuadra")
            self.ui.lblDiferencia.setTextColor(*_tinta("exito"))
            return
        if diferencia > 0:
            self.ui.lblDiferencia.setText(f"Sobrante: {formatear_dinero(diferencia)}")
            self.ui.lblDiferencia.setTextColor(*_tinta("exito"))
        else:
            self.ui.lblDiferencia.setText(f"Faltante: {formatear_dinero(-diferencia)}")
            self.ui.lblDiferencia.setTextColor(*_tinta("error"))

    def cerrar_caja(self) -> None:
        if self._servicio.ya_cerrado(self.dia):
            self.mostrar_advertencia("Cerrar caja", "Este día ya fue cerrado.")
            return

        declarado = self.ui.spnEfectivo.value()
        arqueo = self._servicio.arqueo(self.dia)
        dialogo = DialogoCerrarCaja(
            declarado=declarado,
            esperado=arqueo.esperado_por_medio.efectivo,
            ciego=False,
            devoluciones_total=getattr(arqueo, "devoluciones_total", 0.0),
            parent=self,
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            registro = self._servicio.cerrar(
                self.dia, declarado, dialogo.notas,
                self._usuario)
        except ErrorCierre as error:
            self.mostrar_advertencia("Cierre", str(error))
            return

        self.mostrar_informacion("Cierre de caja", self._mensaje_de_cierre(registro))
        self._avisar_backup()
        self.recalcular()

    def _avisar_backup(self) -> None:
        backup = self._servicio.ultimo_backup
        if backup is None:
            Notificacion(self).mostrar(
                "Copia de seguridad",
                "El cierre se guardó, pero no se pudo generar la copia de seguridad de la base.",
            )
            return
        total = self._servicio.total_backups()
        Notificacion(self).mostrar(
            "Copia de seguridad",
            f"Copia guardada: {backup.name}. Hay {total} copia(s) guardada(s).",
        )

    def _confirmar_diferencia(self, declarado: float, esperado: float) -> bool:
        diferencia = float(diferencia_montos(declarado, esperado))
        if abs(diferencia) < 0.01:
            return True
        return self.confirmar(
            "Cerrar con diferencia",
            f"El efectivo declarado no coincide con el esperado.\n\n"
            f"Esperado: {formatear_dinero(esperado)}\n"
            f"Declarado: {formatear_dinero(declarado)}\n"
            f"Diferencia: {formatear_dinero(diferencia)}\n\n"
            "¿Cerrar igual?",
        )

    def _mensaje_de_cierre(self, registro: CierreRegistrado) -> str:
        if registro.cuadra:
            return f"El cierre del {registro.fecha_texto} quedó guardado y cuadra."
        return (
            f"El cierre del {registro.fecha_texto} quedó guardado con una diferencia de "
            f"{formatear_dinero(abs(registro.diferencia))}"
            f"{' de sobra' if registro.sobrante > 0 else ' de menos'}.")

    def cargar_historial(self) -> None:
        self.ui.tblHistorial.setColumnHidden(3, False)
        self.ui.tblHistorial.setColumnHidden(4, False)
        self.ui.tblHistorial.setColumnHidden(5, False)
        filas = []
        colores = []
        cierres = list(reversed(self._servicio.historial()))
        for cierre in cierres:
            filas.append([
                cierre.fecha_texto,
                cierre.hora,
                str(cierre.cantidad_ventas),
                formatear_dinero(cierre.total_esperado),
                formatear_dinero(cierre.diferencia) if not cierre.cuadra else "cuadra",
                cierre.usuario or "—",
            ])
            colores.append(None if cierre.cuadra else "red")
        self.llenar_tabla(self.ui.tblHistorial, filas, colores)

        self._tarjetas_historial = []
        while self.ui.gridHistorial.count() > 0:
            item = self.ui.gridHistorial.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not cierres:
            lbl_vacio = BodyLabel("Sin cierres registrados", self.ui.contenedorHistorial)
            lbl_vacio.setFont(fuente(TAMANO_SMALL))
            lbl_vacio.setTextColor(*_tinta("gris_apagado"))
            lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.gridHistorial.addWidget(lbl_vacio, 0, 0)
            self.ui.gridHistorial.setRowStretch(1, 1)
            return

        for idx, cierre in enumerate(cierres[:4]):
            tarjeta = TarjetaHistorialCierre(cierre, ciego=False, parent=self.ui.contenedorHistorial)
            self.ui.gridHistorial.addWidget(tarjeta, idx, 0)
            self._tarjetas_historial.append(tarjeta)

        self.ui.gridHistorial.setColumnStretch(0, 1)
        self.ui.gridHistorial.setRowStretch(min(len(cierres), 4), 1)


VentanaCierre = VentanaCaja
