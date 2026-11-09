from __future__ import annotations

import math
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QWidget,
)

from models.caja_movimiento import CajaMovimiento
from models.cierre import Cierre, CierreRegistrado
from services.caja import ErrorCaja, ServicioCaja
from services.cierre_caja import ErrorCierre, ServicioCierre
from services.turnos import ServicioTurnos
from ui.estilos import ROJO_TEXTO, VERDE_TEXTO, TAMANO_MICRO, TAMANO_SMALL, escala, fuente
from ui.manual.cierre_ui import Ui_CierreForm
from ui.tema import color
from ui.widgets.notificacion import Notificacion
from utils.formato import diferencia as diferencia_montos
from utils.formato import formatear_dinero
from views.dialogo_anulacion import DialogoAnulacion
from views.dialogo_cerrar_caja import DialogoCerrarCaja
from views.dialogo_movimiento_caja import DialogoMovimientoCaja
from views.seccion_turnos import SeccionTurnos
from views.tarjeta_caja import TarjetaHistorialCierre, TarjetaMovimientoCaja
from views.ventana_base import VentanaBase


class VentanaCaja(QWidget, VentanaBase):
    ESTILO_ABIERTA = (
        "QPushButton#btnEstadoCaja {"
        "  background-color: #F6FEF9;"
        f"  color: {VERDE_TEXTO};"
        "  border: 1px solid #B8E6CB;"
        "  border-radius: 8px;"
        "  padding: 4px 12px;"
        "  font-weight: bold;"
        "  min-height: 28px;"
        "}"
        "QPushButton#btnEstadoCaja:hover {"
        "  background-color: #EDFBF2;"
        "  border-color: #8AD2A8;"
        "}"
    )
    ESTILO_CERRADA = (
        "QPushButton#btnEstadoCaja {"
        "  background-color: #FEF3F2;"
        f"  color: {ROJO_TEXTO};"
        "  border: 1px solid #FECDCA;"
        "  border-radius: 8px;"
        "  padding: 4px 12px;"
        "  font-weight: bold;"
        "  min-height: 28px;"
        "}"
        "QPushButton#btnEstadoCaja:hover {"
        "  background-color: #FEE4E2;"
        "  border-color: #FDA29B;"
        "}"
    )

    ESTILO_GLOBAL = (
        "QFrame#frmHeaderCaja, QFrame#frmArqueoCaja, QFrame#frmDeclaradoCaja, "
        "QFrame#frmMovimientosCaja, QFrame#frmHistorialCaja {"
        "  background-color: #FFFFFF;"
        "  border: 1px solid #E5E7EB;"
        "  border-radius: 8px;"
        "}"
        "QPushButton#btnCerrarCaja {"
        "  background-color: #1E8149;"
        "  color: #FFFFFF;"
        "  border: 1px solid #1E8149;"
        "  border-radius: 8px;"
        "  font-weight: bold;"
        "}"
        "QPushButton#btnCerrarCaja:hover {"
        "  background-color: #176B3C;"
        "}"
        "QPushButton#btnCerrarCaja:disabled {"
        "  background-color: #E5E7EB;"
        "  color: #9CA3AF;"
        "  border-color: #E5E7EB;"
        "}"
        "QPushButton#btnEgresoCaja, QPushButton#btnIngresoCaja {"
        "  background-color: #F9FAFB;"
        "  color: #111827;"
        "  border: 1px solid #D1D5DB;"
        "  border-radius: 8px;"
        "  font-weight: bold;"
        "}"
        "QPushButton#btnEgresoCaja:hover, QPushButton#btnIngresoCaja:hover {"
        "  background-color: #F3F4F6;"
        "  border-color: #9CA3AF;"
        "}"
        "QPushButton#btnEgresoCaja:disabled, QPushButton#btnIngresoCaja:disabled {"
        "  background-color: #F9FAFB;"
        "  color: #9CA3AF;"
        "  border-color: #E5E7EB;"
        "}"
        "QPushButton#btnToggleMedios {"
        "  background-color: #F9FAFB;"
        "  color: #374151;"
        "  border: 1px solid #D1D5DB;"
        "  border-radius: 6px;"
        "  padding: 4px 10px;"
        "  font-weight: 600;"
        "}"
        "QPushButton#btnToggleMedios:hover {"
        "  background-color: #F3F4F6;"
        "  border-color: #9CA3AF;"
        "}"
    )

    def __init__(self, servicio: ServicioCierre, usuario: str = "",
                 permiso: str = "", turnos: ServicioTurnos | None = None,
                 caja: ServicioCaja | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Caja")
        self._servicio = servicio
        self._turnos = turnos
        self._caja = caja if caja is not None else getattr(servicio, "caja", None)
        self._usuario = usuario
        self._estado_previo: bool | None = None
        self._medios_colapsados: bool = False
        self._movimientos_cache: list[CajaMovimiento] = []

        self.ui = Ui_CierreForm()
        self.ui.setupUi(self)
        self.setStyleSheet(self.ESTILO_GLOBAL)

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
        self.ui.btnHoy.clicked.connect(self.ir_a_hoy)
        self.ui.btnRefrescar.clicked.connect(self.recalcular)
        self.ui.btnEstado.clicked.connect(self.recalcular)
        for columna, ancho in enumerate((115, 95, 70, 140, 110)):
            self.ui.tblHistorial.setColumnWidth(columna, round(ancho * escala()))
        self.ui.spnEfectivo.valueChanged.connect(self.actualizar_diferencia)
        self.ui.btnCerrarCaja.clicked.connect(self.cerrar_caja)
        self.recalcular()

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
        self._cargar_medios(arqueo)
        self._mostrar_esperado(arqueo)
        self._mostrar_estado_del_dia(ya_cerrado, turno_abierto)
        self._proponer_efectivo(arqueo.esperado_por_medio.efectivo)
        self.actualizar_diferencia()
        self.cargar_historial()
        self._cargar_movimientos()
        self._ajustar_alturas_paneles()

    def _ajustar_alturas_paneles(self) -> None:
        """Ajusta las dos scrolls según la cantidad de tarjetas (sin huecos fijos)."""
        movs = len(getattr(self, "_movimientos_cache", []) or [])
        alto_mov = 70 if movs == 0 else min(86 + (movs - 1) * 66, 300)

        n_hist = len(getattr(self, "_tarjetas_historial", []) or [])
        filas_hist = max((n_hist + 1) // 2, 1)
        alto_hist = 70 if n_hist == 0 else min(88 + (filas_hist - 1) * 82, 300)

        self.ui.scrollMovimientos.setMinimumHeight(alto_mov)
        self.ui.scrollHistorial.setMinimumHeight(alto_hist)
        self.ui.scrollMovimientos.updateGeometry()
        self.ui.scrollHistorial.updateGeometry()

    def _toggle_medios(self) -> None:
        self._medios_colapsados = not self._medios_colapsados
        self.ui.tblMedios.setVisible(not self._medios_colapsados)
        self.ui.btnToggleMedios.setText("Medios de pago ▾" if self._medios_colapsados else "Ocultar medios ▴")

    def _cargar_medios(self, arqueo: Cierre) -> None:
        ciego = getattr(self, "_ciego", False)
        self.ui.btnToggleMedios.setVisible(not ciego)
        if ciego:
            self.ui.tblMedios.setVisible(False)
            return
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
            lbl_medio.setFont(fuente(TAMANO_MICRO, negrita=True, tabular=True))
            lbl_medio.setStyleSheet(
                f"background-color: {color('fondo_insignia')}; color: {color('gris_linea')}; "
                f"border: 1px solid {color('borde_suave')}; border-radius: 6px; padding: 3px 8px;"
            )
            self.ui.hlyMedios.addWidget(lbl_medio)
        self.ui.hlyMedios.addStretch(1)

    def _mostrar_esperado(self, arqueo: Cierre) -> None:
        self.ui.lblEsperado.setText(
            f"Ventas efectivo: {formatear_dinero(arqueo.ventas_efectivo)} + "
            f"Cobros fiado: {formatear_dinero(arqueo.cobros_fiado_efectivo)} − "
            f"Egresos: {formatear_dinero(arqueo.egresos)} + "
            f"Ingresos: {formatear_dinero(arqueo.ingresos)} = "
            f"Esperado en el cajón: {formatear_dinero(arqueo.esperado_por_medio.efectivo)}"
        )

    def _mostrar_estado_del_dia(self, ya_cerrado: bool, turno_abierto: bool = False) -> None:
        if ya_cerrado:
            self.ui.btnEstado.setText("● Caja cerrada")
            self.ui.btnEstado.setStyleSheet(self.ESTILO_CERRADA)
            self.ui.btnCerrarCaja.setEnabled(False)
            self.btnEgreso.setEnabled(False)
            self.btnIngreso.setEnabled(False)
            self.btnAnularMovimiento.setEnabled(False)
        else:
            self.ui.btnEstado.setText("● Caja abierta")
            self.ui.btnEstado.setStyleSheet(self.ESTILO_ABIERTA)
            self.ui.btnCerrarCaja.setEnabled(True)
            self.btnEgreso.setEnabled(True)
            self.btnIngreso.setEnabled(True)
            self.btnAnularMovimiento.setEnabled(True)
        self._estado_previo = ya_cerrado

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
            self.ui.lblDiferencia.setStyleSheet(f"color: {VERDE_TEXTO};")
            return
        if diferencia > 0:
            self.ui.lblDiferencia.setText(f"Sobrante: {formatear_dinero(diferencia)}")
            self.ui.lblDiferencia.setStyleSheet(f"color: {VERDE_TEXTO};")
        else:
            self.ui.lblDiferencia.setText(f"Faltante: {formatear_dinero(-diferencia)}")
            self.ui.lblDiferencia.setStyleSheet(f"color: {ROJO_TEXTO};")

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
            lbl_vacio = QLabel("Servicio de caja no disponible", self.ui.contenedorMovimientos)
            lbl_vacio.setFont(fuente(TAMANO_SMALL))
            lbl_vacio.setStyleSheet(f"color: {color('gris_apagado')}; padding: 12px 0px; background: transparent;")
            lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.vlyTarjetasMovimientos.addWidget(lbl_vacio)
            return

        self._movimientos_cache = self._caja.listar_del_dia(self.dia)
        movimientos_ordenados = list(reversed(self._movimientos_cache))
        if not movimientos_ordenados:
            lbl_vacio = QLabel("Sin movimientos en el día", self.ui.contenedorMovimientos)
            lbl_vacio.setFont(fuente(TAMANO_SMALL))
            lbl_vacio.setStyleSheet(f"color: {color('gris_apagado')}; padding: 12px 0px; background: transparent;")
            lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.vlyTarjetasMovimientos.addWidget(lbl_vacio)
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

    def cerrar_caja(self) -> None:
        if self._servicio.ya_cerrado(self.dia):
            self.mostrar_advertencia("Cerrar caja", "Este día ya fue cerrado.")
            return

        declarado = self.ui.spnEfectivo.value()
        arqueo = self._servicio.arqueo(self.dia)
        dialogo = DialogoCerrarCaja(
            declarado=declarado,
            esperado=arqueo.esperado_por_medio.efectivo,
            ciego=getattr(self, "_ciego", False),
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
            lbl_vacio = QLabel("Sin cierres registrados", self.ui.contenedorHistorial)
            lbl_vacio.setFont(fuente(TAMANO_SMALL))
            lbl_vacio.setStyleSheet(f"color: {color('gris_apagado')}; padding: 12px 0px; background: transparent;")
            lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.gridHistorial.addWidget(lbl_vacio, 0, 0, 1, 2)
            return

        for idx, cierre in enumerate(cierres[:4]):
            fila = idx // 2
            col = idx % 2
            tarjeta = TarjetaHistorialCierre(cierre, ciego=getattr(self, "_ciego", False), parent=self.ui.contenedorHistorial)
            self.ui.gridHistorial.addWidget(tarjeta, fila, col)
            self._tarjetas_historial.append(tarjeta)


VentanaCierre = VentanaCaja
