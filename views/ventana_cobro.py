from __future__ import annotations

import math

from PyQt6.QtWidgets import QDialog

from models import medio_pago
from models.medio_pago import (
    MEDIOS,
    METODO_EFECTIVO,
    METODO_FIADO,
    METODO_MIXTO,
    METODO_MP,
    METODO_TRANSFERENCIA,
    descripcion_de,
)
from models.venta import Venta
from models.venta_registrada import PagoVenta
from services.excepciones import ErrorValidacion
from services.gestor_fiado import GestorFiado
from ui.estilos import ROJO_TEXTO, VERDE_TEXTO
from ui.manual.cobro_ui import Ui_CobroForm
from ui.tema import color
from utils.formato import diferencia as diferencia_montos
from utils.formato import formatear_dinero
from views.ventana_base import VentanaBase

COLOR_DETALLE = color("gris_detalle")


class VentanaCobro(QDialog, VentanaBase):
    def __init__(self, venta: Venta, fiado: GestorFiado | None = None, parent=None) -> None:
        super().__init__(parent)
        self._venta = venta
        self._total = round(venta.total, 2)
        self._fiado = fiado
        self._pagos: list[PagoVenta] = []
        self._cliente_fiado = ""
        self.ui = Ui_CobroForm()
        self.ui.setupUi(self)
        for etiqueta, codigo in MEDIOS:
            self.ui.cmbMetodo.addItem(etiqueta, codigo)
            self.ui.cmbMedioParcial.addItem(etiqueta, codigo)
        self.ui.cmbMetodo.addItem("Pago mixto", METODO_MIXTO)
        self._cargar_clientes()
        self.ui.lblTotalCobrar.mostrar(formatear_dinero(self.total_cobrar))
        self._ampliar_spinbox(self.total_cobrar)
        self.ui.spnMonto.setValue(self.total_cobrar)
        self.ui.cmbMetodo.currentIndexChanged.connect(self._elegir_metodo)
        self.ui.cmbMedioParcial.currentIndexChanged.connect(self.actualizar)
        self.ui.cmbCliente.currentIndexChanged.connect(self.actualizar)
        self.ui.spnMonto.valueChanged.connect(self.actualizar)
        self.ui.btnCobrar.clicked.connect(self.aceptar)
        self.ui.btnCancelar.clicked.connect(self.reject)
        self.ui.btnAgregar.clicked.connect(self.agregar_pago)
        self.ui.btnQuitar.clicked.connect(self.quitar_pago)
        self.ui.btnCobrar.setDefault(True)
        self.ui.btnCancelar.setAutoDefault(False)
        self.actualizar()

    @property
    def metodo(self) -> str:
        return self.ui.cmbMetodo.currentData()

    @property
    def metodo_parcial(self) -> str:
        return self.ui.cmbMedioParcial.currentData()

    @property
    def monto(self) -> float:
        return self.ui.spnMonto.value()

    @property
    def datos(self) -> str:
        return self.ui.txtDatos.text().strip()

    @property
    def cliente(self) -> str:
        if self._medio_activo() != METODO_FIADO:
            return ""
        codigo = self.ui.cmbCliente.currentData()
        return str(codigo or "").strip()

    @property
    def total_cobrar(self) -> float:
        return self._total

    @property
    def pagos(self) -> tuple[PagoVenta, ...]:
        return tuple(self._pagos)

    @property
    def cliente_fiado(self) -> str:
        return self._cliente_fiado

    @property
    def pendiente(self) -> float:
        return round(self.total_cobrar - sum(
            pago.importe for pago in self._pagos), 2)

    @property
    def vuelto(self) -> float:
        return float(diferencia_montos(self.monto, self.pendiente))

    @property
    def faltante(self) -> float:
        return max(0.0, float(diferencia_montos(self.pendiente, self.monto)))

    @property
    def resultado(self) -> tuple[str, float, str, str]:
        return self.metodo, self.monto, self.datos, self.cliente

    def _medio_activo(self) -> str:
        if self.metodo == METODO_MIXTO:
            return self.metodo_parcial
        return self.metodo

    def _ampliar_spinbox(self, monto: float) -> None:
        if not math.isfinite(monto):
            return
        self.ui.spnMonto.setMaximum(
            max(self.ui.spnMonto.maximum(), math.ceil(monto)))

    def _cargar_clientes(self) -> None:
        self.ui.cmbCliente.clear()
        if self._fiado is None:
            return
        for cliente in self._fiado.listar_clientes():
            deuda = self._fiado.saldo(cliente.identificador)
            texto = f"{cliente.nombre} — debe {formatear_dinero(deuda)}"
            if cliente.limite > 0:
                texto += f" (tope {formatear_dinero(cliente.limite)})"
            self.ui.cmbCliente.addItem(texto, cliente.identificador)

    def _mostrar_detalle(self) -> None:
        partes = []
        if self._venta.recargo:
            partes.append(f"Recargo {self._venta.recargo:g} %")
        if self._venta.descuento_global:
            partes.append(f"Descuento {self._venta.descuento_global:g} %")
        if not partes:
            self.ui.lblDetalle.setText("")
            self.ui.lblDetalle.setVisible(False)
            return
        self.ui.lblDetalle.setText(" · ".join(partes))
        self.ui.lblDetalle.setStyleSheet(f"color: {COLOR_DETALLE};")
        self.ui.lblDetalle.setVisible(True)

    def actualizar(self) -> None:
        mixto = self.metodo == METODO_MIXTO
        activo = self._medio_activo()
        es_fiado = activo == METODO_FIADO
        efectivo = activo == METODO_EFECTIVO
        self._mostrar_detalle()
        if not efectivo:
            self._ampliar_spinbox(self.pendiente)
            self.ui.spnMonto.setValue(self.pendiente)
        self.ui.spnMonto.setEnabled(efectivo)
        self.ui.lblMedioParcial.setVisible(mixto)
        self.ui.cmbMedioParcial.setVisible(mixto)
        self.ui.btnAgregar.setVisible(mixto)
        self.ui.btnQuitar.setVisible(mixto)
        self.ui.lblCliente.setVisible(es_fiado)
        self.ui.cmbCliente.setVisible(es_fiado)
        self.ui.lblSaldo.setVisible(es_fiado)
        if es_fiado:
            self._mostrar_saldo()

        self.ui.lblTotalCobrar.mostrar(formatear_dinero(self.total_cobrar))

        vuelto = self.vuelto
        if vuelto < 0:
            self.ui.lblVuelto.mostrar(f"Falta: {formatear_dinero(-vuelto)}")
            self.ui.lblVuelto.setStyleSheet(f"color: {ROJO_TEXTO};")
        else:
            self.ui.lblVuelto.mostrar(f"Vuelto: {formatear_dinero(vuelto)}")
            self.ui.lblVuelto.setStyleSheet(f"color: {VERDE_TEXTO};")

        self._mostrar_pagos()

        texto, pedir = medio_pago.pedir_datos(activo)
        self.ui.lblDatos.setText(texto)
        self.ui.lblDatos.setVisible(pedir)
        self.ui.txtDatos.setVisible(pedir)
        if not pedir:
            self.ui.txtDatos.clear()

    def _elegir_metodo(self) -> None:
        if self._pagos and self.metodo != METODO_MIXTO:
            self.mostrar_advertencia(
                "Pago mixto",
                "Ya registraste pagos parciales: quedás en Pago mixto. "
                "Si querés cobrar con un único medio, quitá los parciales.")
            self.ui.cmbMetodo.setCurrentIndex(self.ui.cmbMetodo.findData(METODO_MIXTO))
            return
        self.actualizar()

    def _mostrar_pagos(self) -> None:
        pagos = self._pagos
        self.ui.btnQuitar.setEnabled(bool(pagos))
        self.ui.lblPagos.setVisible(bool(pagos) and self.metodo == METODO_MIXTO)
        if not pagos:
            return
        desglose = " + ".join(
            f"{descripcion_de(pago.medio, pago.datos)} "
            f"{formatear_dinero(pago.importe)}" for pago in pagos)
        falta = (" · completo" if self.pendiente == 0
                 else f" · falta {formatear_dinero(self.pendiente)}")
        self.ui.lblPagos.setText(f"Sumados: {desglose}{falta}")
        self.ui.lblPagos.setStyleSheet(f"color: {COLOR_DETALLE};")

    def _confirmar_medios(self, medio: str, importe: float) -> bool:
        if medio == METODO_TRANSFERENCIA:
            return self.confirmar(
                "Transferencia",
                f"¿Impactó la transferencia de {formatear_dinero(importe)}?\n\n"
                "Verificala en el homebanking antes de aceptar.")
        if medio == METODO_MP:
            return self.confirmar(
                "Mercado Pago",
                f"¿Registrás el cobro de {formatear_dinero(importe)} por Mercado Pago "
                "de forma manual?\n\n"
                "La edición libre no conecta con la API: anotá el comprobante si querés.")
        return True

    def _validar_fiado(self, importe: float) -> bool:
        if self._fiado is None or not self.cliente:
            self.mostrar_advertencia("Fiado", "Elegí el cliente para la venta fiada.")
            return False
        if any(pago.medio == METODO_FIADO for pago in self._pagos):
            self.mostrar_advertencia(
                "Fiado", "Solo se admite un pago fiado por venta.")
            return False
        try:
            self._fiado.validar_cargo(self.cliente, importe)
        except ErrorValidacion as error:
            self.mostrar_advertencia("Fiado", str(error))
            return False
        return True

    def _preparar_pago(self, pendiente: float, completa: bool) -> PagoVenta | None:
        medio = self._medio_activo()
        efectivo = medio == METODO_EFECTIVO
        monto = round(self.monto, 2)
        if efectivo:
            if monto < 0.01:
                self.mostrar_advertencia(
                    "Monto en cero", "El monto recibido tiene que ser mayor a cero.")
                return None
            if completa and monto < pendiente:
                self.mostrar_advertencia(
                    "Cobro",
                    f"El monto recibido ({formatear_dinero(monto)}) es menor que lo "
                    f"que falta cobrar ({formatear_dinero(pendiente)}).\n\n"
                    f"Faltan {formatear_dinero(round(pendiente - monto, 2))}.\n\n"
                    "La venta no se cobró: corregí el monto recibido y volvé a cobrar.")
                return None
            importe = min(monto, pendiente)
        else:
            if medio == METODO_FIADO:
                if not self._validar_fiado(pendiente):
                    return None
            elif medio in (METODO_TRANSFERENCIA, METODO_MP):
                if not self._confirmar_medios(medio, pendiente):
                    return None
            importe = pendiente
        return PagoVenta(
            medio=medio, importe=importe, datos=self.datos,
            recibido=monto if efectivo else importe)

    def agregar_pago(self) -> None:
        pendiente = self.pendiente
        if pendiente <= 0:
            return
        pago = self._preparar_pago(pendiente, completa=False)
        if pago is None:
            return
        self._paginar(pago)

    def quitar_pago(self) -> None:
        if not self._pagos:
            return
        ultimo = self._pagos.pop()
        if ultimo.medio == METODO_FIADO:
            self._cliente_fiado = ""
        self.actualizar()

    def _paginar(self, pago: PagoVenta) -> None:
        if pago.medio == METODO_FIADO:
            self._cliente_fiado = self.cliente
        self._pagos.append(pago)
        self.ui.txtDatos.clear()
        self.actualizar()

    def _mostrar_saldo(self) -> None:
        if self._fiado is None or not self.cliente:
            self.ui.lblSaldo.setText("No hay clientes cargados.")
            return
        deuda = self._fiado.saldo(self.cliente)
        self.ui.lblSaldo.setText(f"Deuda actual: {formatear_dinero(deuda)}")

    def aceptar(self) -> None:
        pendiente = self.pendiente
        if self.metodo == METODO_MIXTO and not self._pagos:
            self.mostrar_advertencia(
                "Pago mixto", "Registrá al menos un pago parcial.")
            return
        if self._pagos:
            if pendiente == 0:
                self.accept()
                return
            pago = self._preparar_pago(pendiente, completa=True)
            if pago is None:
                return
            self._paginar(pago)
            self.accept()
            return
        if self.metodo == METODO_EFECTIVO and self.monto < self.total_cobrar:
            self.mostrar_advertencia(
                "Cobro",
                f"El monto recibido ({formatear_dinero(self.monto)}) es menor que el total "
                f"a cobrar ({formatear_dinero(self.total_cobrar)}).\n\n"
                f"Faltan {formatear_dinero(self.faltante)}.\n\n"
                "La venta no se cobró: corregí el monto recibido y volvé a cobrar.")
            return
        if self.metodo == METODO_FIADO:
            if self._fiado is None or not self.cliente:
                self.mostrar_advertencia("Fiado", "Elegí el cliente para la venta fiada.")
                return
            try:
                self._fiado.validar_cargo(self.cliente, self.total_cobrar)
            except ErrorValidacion as error:
                self.mostrar_advertencia("Fiado", str(error))
                return
        self.accept()
