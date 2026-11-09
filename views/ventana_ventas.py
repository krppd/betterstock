from __future__ import annotations

import copy
import sys
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from PyQt6.QtGui import QKeySequence, QPalette, QShortcut
from PyQt6.QtWidgets import QApplication, QInputDialog, QWidget
from PyQt6.QtCore import QMetaObject, QObject, Qt, QUrl, pyqtSignal
from PyQt6.QtQuickWidgets import QQuickWidget

from models.medio_pago import METODO_MP, METODO_TRANSFERENCIA
from models.venta_registrada import PagoVenta
from services.excepciones import (
    ErrorNegocio,
    ErrorValidacion,
    LimiteStockError,
    ProductoNoEncontradoError,
    SinStockError,
)
from services.gestor_comercio import GestorComercio
from services.gestor_fiado import GestorFiado
from services.gestor_ventas import GestorVentas
from services.impresion import imprimir_ticket
from ui.estilos import AMBAR_TEXTO, escala
from ui.manual.ventas_ui import Ui_VentasForm
from ui.tema import puente_tema
from ui.widgets.notificacion import Notificacion
from ui.widgets.trabajo_impresion import TrabajoImpresion
from utils.formato import formatear_cantidad, formatear_dinero
from views.dialogo_comodin import DialogoComodin
from views.dialogo_ticket import DialogoTicket
from views.ventana_base import VentanaBase
from views.ventana_cobro import VentanaCobro
from views.ventana_detalle_venta import VentanaDetalleVenta

COLOR_COMODIN = AMBAR_TEXTO


def _ruta_qml(nombre: str) -> Path:
    raiz = getattr(sys, "_MEIPASS", None)
    if raiz is not None:
        return Path(raiz) / "ui" / "qml" / nombre
    return Path(__file__).resolve().parent.parent / "ui" / "qml" / nombre


class VentanaVentas(QWidget, VentanaBase):
    ir_a_clientes = pyqtSignal()

    def __init__(
        self,
        gestor_ventas: GestorVentas,
        gestor_comercio: GestorComercio,
        usuario_actual: str = "",
        fiado: GestorFiado | None = None,
    ) -> None:
        super().__init__()
        self._gestor_ventas = gestor_ventas
        self._gestor_comercio = gestor_comercio
        self._usuario_actual_nombre = usuario_actual
        self._fiado = fiado
        self._monto_recibido = 0.0
        self._vuelto = 0.0
        self._ultimo_comprobante = None
        self._avisados_texto_ambiguo: set[str] = set()
        self._trabajos: list[TrabajoImpresion] = []
        self.ui = Ui_VentasForm()
        self.ui.setupUi(self)
        self._aviso_texto_ambiguo = Notificacion(self)
        self.estirar_columnas(self.ui.tblVentas)
        self.setMinimumSize(700, 420)

        self.ui.btnAgregar.clicked.connect(self.agregar_producto)
        self.ui.txtCodigoBarras.returnPressed.connect(self.agregar_producto)
        self.ui.btnQuitar.clicked.connect(self.quitar)
        self.ui.btnComodin.clicked.connect(self.agregar_comodin)
        self._total_anterior = 0.0
        self._raiz_qml = None
        self._botones_qml = {}
        self._qml_conectado = False
        self._quick_acciones = QQuickWidget(self)
        self._quick_acciones.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._quick_acciones.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self._quick_acciones.setClearColor(self.palette().color(QPalette.ColorRole.Window))
        self._quick_acciones.setFixedHeight(round(114 * escala()))
        self._quick_acciones.statusChanged.connect(self._conectar_barra_qml)
        self._tema = puente_tema(self._quick_acciones)
        self._quick_acciones.rootContext().setContextProperty("Tema", self._tema)
        self._quick_acciones.setSource(QUrl.fromLocalFile(str(_ruta_qml("components/BarraAccionesVentas.qml"))))
        self.ui.lyBarraAcciones.addWidget(self._quick_acciones)
        self._conectar_barra_qml()
        for secuencia, metodo, objeto in (
            ("Alt+D", self.descuento_global, "accionDescuento"),
            ("Alt+R", self.recargo, "accionRecargo"),
            ("Alt+E", self.ver_ultimo_comprobante, "accionComprobante"),
            ("Alt+C", self.ir_a_clientes.emit, "accionCuentas"),
        ):
            atajo = QShortcut(QKeySequence(secuencia), self)
            atajo.activated.connect(lambda metodo=metodo, objeto=objeto: self._disparar_accion(metodo, objeto))
        for secuencia in ("Ctrl+Return", "Ctrl+Enter"):
            atajo = QShortcut(QKeySequence(secuencia), self)
            atajo.activated.connect(lambda: self._disparar_accion(self.cobrar_venta, "accionCobrar"))
        atajo_comodin = QShortcut(QKeySequence(Qt.Key.Key_F8), self)
        atajo_comodin.activated.connect(self.agregar_comodin)

    def al_mostrar(self) -> None:
        self.actualizar_tabla_y_total()
        self.ui.txtCodigoBarras.setFocus()

    def _usuario_actual(self) -> str:
        return self._usuario_actual_nombre

    def _conectar_barra_qml(self) -> None:
        if self._qml_conectado:
            return
        if self._quick_acciones.status() != QQuickWidget.Status.Ready:
            return
        raiz = self._quick_acciones.rootObject()
        if raiz is None:
            return
        self._qml_conectado = True
        self._raiz_qml = raiz
        raiz.setProperty("escala", escala())
        raiz.descuentoPedido.connect(self.descuento_global)
        raiz.recargoPedido.connect(self.recargo)
        raiz.comprobantePedido.connect(self.ver_ultimo_comprobante)
        raiz.cuentasPedido.connect(self.ir_a_clientes.emit)
        raiz.cobrarPedido.connect(self.cobrar_venta)
        for objeto in ("accionDescuento", "accionRecargo",
                       "accionComprobante", "accionCuentas", "accionCobrar"):
            boton = raiz.findChild(QObject, objeto)
            if boton is not None:
                self._botones_qml[objeto] = boton

    def _disparar_accion(self, metodo: Callable[[], None], objeto: str) -> None:
        metodo()
        boton = self._botones_qml.get(objeto)
        if boton is not None:
            QMetaObject.invokeMethod(boton, "triggerVisualPulse")

    def _destellar_cobrar(self) -> None:
        if self._raiz_qml is not None:
            QMetaObject.invokeMethod(self._raiz_qml, "destellar")

    def ver_ultimo_comprobante(self) -> None:
        if self._ultimo_comprobante is None:
            self.mostrar_advertencia(
                "Comprobante", "Todavía no cobraste ninguna venta en esta sesión.")
            return
        VentanaDetalleVenta(self._ultimo_comprobante, self).exec()

    def agregar_producto(self) -> None:
        texto = self.ui.txtCodigoBarras.text().strip()
        if not texto:
            if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
                return
            self.cobrar_venta()
            return

        codigo, cantidad = self._gestor_ventas.interpretar_codigo(texto)
        try:
            item = self._gestor_ventas.agregar_producto(codigo, cantidad)
        except LimiteStockError as error:
            self.mostrar_advertencia("Límite de Stock", str(error))
            return
        except (ProductoNoEncontradoError, SinStockError) as error:
            titulo = "Error" if isinstance(error, ProductoNoEncontradoError) else "Sin Stock"
            self.mostrar_advertencia(titulo, str(error))
            self.ui.txtCodigoBarras.clear()
            return
        except ErrorValidacion as error:
            self.mostrar_advertencia("Error", str(error))
            return

        self._avisar_texto_ambiguo(item)
        self.actualizar_tabla_y_total()
        self.ui.txtCodigoBarras.clear()

    def _avisar_texto_ambiguo(self, item) -> None:
        if not item.texto_ambiguo or item.codigo in self._avisados_texto_ambiguo:
            return
        self._avisados_texto_ambiguo.add(item.codigo)
        self._aviso_texto_ambiguo.mostrar(
            "Nombre con separadores",
            f"«{item.nombre}» tiene ';' o '|' en el nombre. Se guarda igual en la "
            "venta, pero conviene renombrarlo en el catálogo.",
        )

    def agregar_comodin(self) -> None:
        dialogo = DialogoComodin(self)
        if dialogo.exec() != dialogo.DialogCode.Accepted:
            return
        descripcion, cantidad, precio = dialogo.resultado
        try:
            self._gestor_ventas.agregar_comodin(descripcion, cantidad, precio)
        except ValueError as error:
            self.mostrar_advertencia("Comodín", str(error))
            return
        self.actualizar_tabla_y_total()
        self.ui.txtCodigoBarras.setFocus()

    def actualizar_tabla_y_total(self) -> None:
        venta = self._gestor_ventas.venta
        filas = []
        colores: list[str | None] = []
        for i in venta.items:
            nombre = i.nombre
            if i.es_comodin:
                nombre += " (COMODÍN)"
            if i.en_oferta:
                nombre += " (OFERTA)"
            if i.descuento:
                nombre += f" (-{i.descuento:g}%)"
            filas.append([i.codigo, nombre, formatear_dinero(i.precio_unitario),
                          formatear_cantidad(i.cantidad), formatear_dinero(i.subtotal)])
            colores.append(COLOR_COMODIN if i.es_comodin else None)
        self.llenar_tabla(self.ui.tblVentas, filas, colores)
        total = formatear_dinero(venta.total)
        if venta.descuento_global or venta.recargo:
            total += f"  (subtotal {formatear_dinero(venta.subtotal)})"
        self.ui.lblTotal.mostrar(total)
        if self._total_anterior <= 0 < venta.total:
            self._destellar_cobrar()
        self._total_anterior = venta.total

    def _pedir_porcentaje(self, titulo: str, texto: str, valor: float = 0.0) -> float | None:
        porcentaje, aceptado = QInputDialog.getDouble(
            self, titulo, texto, value=valor, min=0.0, max=100.0, decimals=2)
        return porcentaje if aceptado else None

    def _codigos_seleccionados(self) -> list[str]:
        filas = sorted({indice.row() for indice in self.ui.tblVentas.selectedIndexes()})
        items = self._gestor_ventas.venta.items
        return [items[f].codigo for f in filas if f < len(items)]

    def quitar(self) -> None:
        codigos = self._codigos_seleccionados()
        if not codigos:
            self.mostrar_advertencia("Quitar", "Seleccioná al menos una fila de la tabla.")
            return
        eleccion = self.elegir(
            "Quitar",
            "¿Qué querés quitar de la venta?",
            [
                ("nada", "Cancelar", "rechazar"),
                ("unidad", "Una unidad", "aceptar"),
                ("linea", "Toda la línea", "destructivo"),
            ],
        )
        if eleccion == "nada":
            return
        try:
            for codigo in codigos:
                self._gestor_ventas.venta.quitar(codigo, toda_linea=(eleccion == "linea"))
        except ValueError as error:
            self.mostrar_advertencia("Error", str(error))
            return
        self.actualizar_tabla_y_total()

    def descuento_global(self) -> None:
        porcentaje = self._pedir_porcentaje(
            "Descuento global", "Descuento sobre el total %:",
            self._gestor_ventas.venta.descuento_global)
        if porcentaje is None:
            return
        try:
            self._gestor_ventas.venta.descuento_global = porcentaje
        except ValueError as error:
            self.mostrar_advertencia("Error", str(error))
            return
        self.actualizar_tabla_y_total()

    def recargo(self) -> None:
        porcentaje = self._pedir_porcentaje(
            "Recargo", "Recargo sobre el total %:",
            self._gestor_ventas.venta.recargo)
        if porcentaje is None:
            return
        try:
            self._gestor_ventas.venta.recargo = porcentaje
        except ValueError as error:
            self.mostrar_advertencia("Error", str(error))
            return
        self.actualizar_tabla_y_total()

    def cobrar_venta(self) -> None:
        venta = self._gestor_ventas.venta
        if venta.esta_vacia():
            self.mostrar_advertencia("Error", "No hay productos en la lista de venta.")
            return

        cobro = self._pedir_cobro(venta)
        if cobro is None:
            return
        if cobro.pagos:
            if not self._registrar_cobro("", 0.0, "", cliente=cobro.cliente_fiado,
                                         pagos=cobro.pagos):
                return
        else:
            metodo, monto, datos, cliente = cobro.resultado
            datos = self._confirmar_medio(metodo, datos, cobro.total_cobrar)
            if datos is None:
                return
            if not self._registrar_cobro(metodo, monto, datos, cliente):
                return

        self._resolver_impresion()
        self._iniciar_venta_nueva()

    def _pedir_cobro(self, venta) -> VentanaCobro | None:
        cobro = VentanaCobro(venta, self._fiado, self)
        if cobro.exec() != cobro.DialogCode.Accepted:
            return None
        return cobro

    def _confirmar_medio(self, metodo: str, datos: str, total: float) -> str | None:
        if metodo == METODO_TRANSFERENCIA and not self.confirmar(
            "Transferencia",
            f"¿Impactó la transferencia de {formatear_dinero(total)}?\n\n"
            "Verificala en el homebanking antes de aceptar.",
        ):
            return None

        if metodo == METODO_MP:
            return self.confirmar(
                "Mercado Pago",
                f"¿Registrás el cobro de {formatear_dinero(total)} por Mercado Pago "
                "de forma manual?\n\n"
                "La edición libre no conecta con la API: anotá el comprobante si querés.")
        return datos

    def _registrar_cobro(self, metodo: str, monto: float, datos: str, cliente: str = "",
                         pagos: tuple[PagoVenta, ...] = ()) -> bool:
        try:
            if pagos:
                comprobante = self._gestor_ventas.cobrar(
                    date.today(), pagos=pagos,
                    usuario=self._usuario_actual(), cliente=cliente)
            else:
                comprobante = self._gestor_ventas.cobrar(
                    date.today(), monto_recibido=monto, medio_pago=metodo,
                    datos_pago=datos, usuario=self._usuario_actual(), cliente=cliente)
        except ErrorNegocio as error:
            self.mostrar_advertencia("Error", str(error))
            return False
        self._monto_recibido = comprobante.monto_recibido
        self._vuelto = comprobante.vuelto
        self._ultimo_comprobante = comprobante
        return True

    def _iniciar_venta_nueva(self) -> None:
        self._gestor_ventas.nueva_venta()
        self.actualizar_tabla_y_total()
        self.ui.txtCodigoBarras.clear()

    def _resolver_impresion(self) -> None:
        identificador, medio = self._datos_del_comprobante()
        venta = copy.deepcopy(self._gestor_ventas.venta)
        comercio = self._gestor_comercio.comercio
        monto_recibido = self._monto_recibido
        vuelto = self._vuelto
        dialogo = DialogoTicket(venta.total, medio, monto_recibido, vuelto,
                                identificador, self)
        dialogo.imprimir_pedido.connect(
            lambda: self._imprimir_ticket(venta, comercio, monto_recibido, vuelto,
                                          identificador, medio, dialogo))
        dialogo.exec()

    def _imprimir_ticket(self, venta, comercio, monto_recibido: float, vuelto: float,
                         identificador: str, medio: str, dialogo) -> None:
        trabajo = TrabajoImpresion(lambda: imprimir_ticket(
            venta, comercio, monto_recibido, vuelto,
            identificador=identificador, medio_pago=medio))
        trabajo.terminado.connect(
            lambda error: self._al_terminar_impresion(error, dialogo))
        trabajo.finished.connect(lambda: self._al_terminar_trabajo(trabajo))
        self._trabajos.append(trabajo)
        trabajo.start()

    def _al_terminar_impresion(self, error: str, dialogo) -> None:
        if error:
            dialogo.mostrar_error(error)
            return
        dialogo.terminar_impresion()

    def _al_terminar_trabajo(self, trabajo) -> None:
        if trabajo in self._trabajos:
            self._trabajos.remove(trabajo)
        trabajo.deleteLater()

    def _datos_del_comprobante(self) -> tuple[str, str]:
        comprobante = self._ultimo_comprobante
        if comprobante is None:
            return "", ""
        return comprobante.identificador, comprobante.medio_pago_texto

