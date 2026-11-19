from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import date

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QInputDialog,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

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
from qfluentwidgets import BodyLabel, LineEdit, PrimaryPushButton, PushButton, TableWidget
from ui.estilos import (
    AMBAR_TEXTO,
    TAMANO_BODY,
    TAMANO_DISPLAY,
    TAMANO_SMALL,
    VERDE_TEXTO,
    escala,
    fuente,
)
from ui.tema import medida
from ui.widgets.etiqueta_rodante import EtiquetaRodante
from ui.widgets.notificacion import Notificacion
from ui.widgets.trabajo_impresion import TrabajoImpresion
from utils.formato import formatear_cantidad, formatear_dinero
from views.dialogo_comodin import DialogoComodin
from views.dialogo_ticket import DialogoTicket
from views.ventana_base import VentanaBase
from views.ventana_cobro import VentanaCobro
from views.ventana_detalle_venta import VentanaDetalleVenta

COLOR_COMODIN = AMBAR_TEXTO


class _BarraAcciones(QWidget):
    """Barra nativa de acciones de venta (reemplaza el QQuickWidget QML)."""

    descuentoPedido = pyqtSignal()
    recargoPedido = pyqtSignal()
    comprobantePedido = pyqtSignal()
    cobrarPedido = pyqtSignal()

    SEPARACION = 8
    ACCIONES = (
        ("accionDescuento", "Desc. total", "Alt+D", "descuentoPedido"),
        ("accionRecargo", "Recargo", "Alt+R", "recargoPedido"),
        ("accionComprobante", "Último comprobante", "Alt+E", "comprobantePedido"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._alto_accion = round(medida("alto_boton") * escala())
        self._alto_cobrar = round(medida("alto_cobrar") * escala())
        self._animaciones: dict[str, QPropertyAnimation] = {}
        self._textos: dict[str, tuple[str, str]] = {}
        self._botones: dict[str, PushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.SEPARACION)

        self._scroll = QScrollArea(self)
        self._scroll.setObjectName("accionesScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._contenedor = QWidget()
        self._fila = QHBoxLayout(self._contenedor)
        self._fila.setContentsMargins(0, 0, 0, 0)
        self._fila.setSpacing(self.SEPARACION)
        for nombre, texto, atajo, senal in self.ACCIONES:
            boton = PushButton(texto, self._contenedor)
            boton.setObjectName(nombre)
            boton.setFont(fuente(TAMANO_SMALL))
            boton.setFixedHeight(self._alto_accion)
            boton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            boton.setToolTip(f"{texto} ({atajo})")
            boton.clicked.connect(
                lambda _=False, n=nombre, s=senal: self._al_clicar(n, s))
            self._fila.addWidget(boton, 1)
            self._botones[nombre] = boton
            self._textos[nombre] = (texto, atajo)
        minimo = max(boton.sizeHint().width() for boton in self._botones.values())
        for boton in self._botones.values():
            boton.setMinimumWidth(minimo)
        self._contenedor.setMinimumWidth(
            minimo * len(self._botones) + self.SEPARACION * (len(self._botones) - 1))
        self._scroll.setWidget(self._contenedor)
        self._alto_scroll = self._alto_accion + max(
            12, self._scroll.horizontalScrollBar().sizeHint().height()) + 2
        self._scroll.setFixedHeight(self._alto_scroll)
        layout.addWidget(self._scroll)

        self.cobrar = PrimaryPushButton("Cobrar Venta   ↵ Enter", self)
        self.cobrar.setObjectName("accionCobrar")
        self.cobrar.setFont(fuente(TAMANO_BODY, negrita=True))
        self.cobrar.setFixedHeight(self._alto_cobrar)
        self.cobrar.setToolTip("Cobrar venta (Ctrl+Enter)")
        self.cobrar.clicked.connect(self._al_cobrar)
        layout.addWidget(self.cobrar)
        self._ajustar_atajos()

    def _al_clicar(self, nombre: str, senal: str) -> None:
        self.pulsar(nombre)
        getattr(self, senal).emit()

    def _al_cobrar(self) -> None:
        self.pulsar("accionCobrar")
        self.cobrarPedido.emit()

    def _ajustar_atajos(self) -> None:
        contenido = max(self._scroll.viewport().width(),
                        self._contenedor.minimumWidth())
        ancho = (contenido - self.SEPARACION * (len(self._botones) - 1)) / len(self._botones)
        if ancho <= 0:
            return
        necesitan = [
            boton.fontMetrics().horizontalAdvance(f"{texto}   {atajo}") + 28
            for boton, (texto, atajo) in (
                (self._botones[n], self._textos[n]) for n in self._textos)
        ]
        mostrar = ancho >= max(necesitan)
        for nombre, boton in self._botones.items():
            texto, atajo = self._textos[nombre]
            boton.setText(f"{texto}   {atajo}" if mostrar else texto)

    def sizeHint(self) -> QSize:
        alto = self._alto_scroll + self.SEPARACION + self._alto_cobrar
        return QSize(super().sizeHint().width(), alto)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._ajustar_atajos()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._ajustar_atajos()

    def pulsar(self, nombre: str, destello: bool = False) -> None:
        boton = self._botones.get(nombre)
        if boton is None and nombre == "accionCobrar":
            boton = self.cobrar
        if boton is None:
            return
        anterior = self._animaciones.pop(nombre, None)
        if anterior is not None:
            anterior.stop()
            anterior.deleteLater()
        efecto = QGraphicsOpacityEffect(boton)
        boton.setGraphicsEffect(efecto)
        animacion = QPropertyAnimation(efecto, b"opacity")
        animacion.setDuration(260 if destello else 140)
        animacion.setEasingCurve(QEasingCurve.Type.OutQuad)
        animacion.setKeyValueAt(0.0, 1.0)
        animacion.setKeyValueAt(0.5, 0.4 if destello else 0.65)
        animacion.setKeyValueAt(1.0, 1.0)
        animacion.finished.connect(lambda: _quitar_efecto(boton))
        self._animaciones[nombre] = animacion
        animacion.start()


def _quitar_efecto(boton: QWidget) -> None:
    try:
        boton.setGraphicsEffect(None)
    except RuntimeError:
        pass


class _UiCompat:
    def __init__(self, owner) -> None:
        for attr in (
            "horizontalLayout", "lblCodigo", "txtCodigoBarras", "btnAgregar", "btnQuitar",
            "btnComodin", "tblVentas", "horizontalLayout_2",
            "lblTotalTxt", "lblTotal", "lyBarraAcciones",
        ):
            setattr(self, attr, getattr(owner, attr))


class VentanaVentas(QWidget, VentanaBase):

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
        self._iniciar_interfaz()
        self._aviso_texto_ambiguo = Notificacion(self)
        self.estirar_columnas(self.ui.tblVentas)
        self.setMinimumSize(700, 420)

        self.ui.btnAgregar.clicked.connect(self.agregar_producto)
        self.ui.txtCodigoBarras.returnPressed.connect(self.agregar_producto)
        self.ui.btnQuitar.clicked.connect(self.quitar)
        self.ui.btnComodin.clicked.connect(self.agregar_comodin)
        self._total_anterior = 0.0
        self._barra = _BarraAcciones(self)
        self._barra.descuentoPedido.connect(self.descuento_global)
        self._barra.recargoPedido.connect(self.recargo)
        self._barra.comprobantePedido.connect(self.ver_ultimo_comprobante)
        self._barra.cobrarPedido.connect(self.cobrar_venta)
        self.ui.lyBarraAcciones.addWidget(self._barra)
        for secuencia, metodo, nombre in (
            ("Alt+D", self.descuento_global, "accionDescuento"),
            ("Alt+R", self.recargo, "accionRecargo"),
            ("Alt+E", self.ver_ultimo_comprobante, "accionComprobante"),
        ):
            atajo = QShortcut(QKeySequence(secuencia), self)
            atajo.activated.connect(lambda m=metodo, n=nombre: self._disparar_accion(m, n))
        atajo_quitar = QShortcut(QKeySequence("Alt+C"), self)
        atajo_quitar.activated.connect(self.quitar)
        for secuencia in ("Ctrl+Return", "Ctrl+Enter"):
            atajo = QShortcut(QKeySequence(secuencia), self)
            atajo.activated.connect(lambda: self._disparar_accion(self.cobrar_venta, "accionCobrar"))
        atajo_comodin = QShortcut(QKeySequence("Alt+O"), self)
        atajo_comodin.activated.connect(self.agregar_comodin)

    def _iniciar_interfaz(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(12, 12, 12, 12)
        layout_principal.setSpacing(8)

        self.horizontalLayout = QHBoxLayout()
        self.lblCodigo = BodyLabel("Código de Barras:", self)
        self.txtCodigoBarras = LineEdit(self)
        self.txtCodigoBarras.setObjectName("txtCodigoBarras")
        self.txtCodigoBarras.setToolTip(
            "Escaneá el código o escribí 3*1001 para agregar 3 unidades")
        self.btnAgregar = PushButton("&Agregar", self)
        self.btnAgregar.setObjectName("btnAgregar")
        self.btnQuitar = PushButton("&Quitar", self)
        self.btnQuitar.setObjectName("btnQuitar")
        self.btnComodin = PushButton("Comodín", self)
        self.btnComodin.setObjectName("btnComodin")
        self.btnComodin.setToolTip("Vender algo que no está en el catálogo (Alt+O)")

        self.horizontalLayout.addWidget(self.lblCodigo)
        self.horizontalLayout.addWidget(self.txtCodigoBarras, 1)
        self.horizontalLayout.addWidget(self.btnAgregar)
        self.horizontalLayout.addWidget(self.btnQuitar)
        self.horizontalLayout.addWidget(self.btnComodin)
        layout_principal.addLayout(self.horizontalLayout)

        self.tblVentas = TableWidget(self)
        self.tblVentas.setObjectName("tblVentas")
        self.tblVentas.setColumnCount(5)
        headers = ["Código", "Nombre", "Precio Venta", "Cantidad", "Subtotal"]
        for i, header in enumerate(headers):
            item = QTableWidgetItem(header)
            self.tblVentas.setHorizontalHeaderItem(i, item)
        self.tblVentas.horizontalHeader().setDefaultSectionSize(150)
        self.tblVentas.horizontalHeader().setStretchLastSection(True)
        self.tblVentas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblVentas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tblVentas.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout_principal.addWidget(self.tblVentas, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.lblTotalTxt = BodyLabel("TOTAL:", self)
        self.lblTotalTxt.setObjectName("lblTotalTxt")
        self.lblTotal = EtiquetaRodante(parent=self)
        self.lblTotal.setFont(fuente(TAMANO_DISPLAY, negrita=True, tabular=True))
        self.lblTotal.setStyleSheet(f"color: {VERDE_TEXTO};")
        self.lblTotal.setObjectName("lblTotal")
        self.lblTotal.setText("$ 0,00")
        self.horizontalLayout_2.addWidget(self.lblTotalTxt)
        self.horizontalLayout_2.addWidget(self.lblTotal)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacer)
        layout_principal.addLayout(self.horizontalLayout_2)

        self.lyBarraAcciones = QHBoxLayout()
        self.lyBarraAcciones.setObjectName("lyBarraAcciones")
        self.lyBarraAcciones.setContentsMargins(0, 0, 0, 0)
        layout_principal.addLayout(self.lyBarraAcciones)

        self.ui = _UiCompat(self)

    def al_mostrar(self) -> None:
        self.actualizar_tabla_y_total()
        self.ui.txtCodigoBarras.setFocus()

    def _usuario_actual(self) -> str:
        return self._usuario_actual_nombre

    def _disparar_accion(self, metodo: Callable[[], None], nombre: str) -> None:
        metodo()
        self._barra.pulsar(nombre)

    def _destellar_cobrar(self) -> None:
        self._barra.pulsar("accionCobrar", destello=True)

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
