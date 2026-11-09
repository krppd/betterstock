
from __future__ import annotations

import logging
from datetime import date, datetime

from models.movimiento import MovimientoEntrada, MovimientoSalida
from models.venta import ItemVenta, Venta, candidatos_de_cantidad, es_codigo_comodin
from models.venta_registrada import PagoVenta, VentaRegistrada
from models.medio_pago import METODO_FIADO
from services.estadisticas_ventas import EstadisticasVentas
from services.excepciones import (
    ErrorValidacion,
    LimiteStockError,
    ProductoNoEncontradoError,
    SinStockError,
)
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from services.plazo_anulacion import ConsultaCierres, PlazoAnulacion
from utils.formato import redondear_cantidad

logger = logging.getLogger(__name__)


class GestorVentas:

    MOTIVO_VENTA = "Venta en Caja"

    def __init__(self, gestor_stock: GestorStock, estadisticas: EstadisticasVentas,
                 fiado: GestorFiado | None = None,
                 cierres: ConsultaCierres | None = None) -> None:
        self._gestor_stock = gestor_stock
        self._estadisticas = estadisticas
        self._fiado = fiado
        self._plazo = PlazoAnulacion(cierres)
        self._venta = Venta()

    @property
    def venta(self) -> Venta:
        return self._venta

    def agregar_producto(self, codigo: str, cantidad: float = 1.0) -> ItemVenta:
        producto = self._gestor_stock.buscar_producto(codigo)
        if producto is None:
            raise ProductoNoEncontradoError(codigo)
        if not producto.tiene_stock():
            raise SinStockError(producto.nombre)
        cantidad = redondear_cantidad(cantidad)
        if cantidad <= 0:
            raise ErrorValidacion("La cantidad debe ser mayor a 0.")
        en_venta = redondear_cantidad(self._venta.cantidad_de(codigo))
        if redondear_cantidad(en_venta + cantidad) > redondear_cantidad(producto.stock_actual):
            raise LimiteStockError()
        item = self._venta.agregar_cantidad(producto, cantidad)
        if item.texto_ambiguo:
            logger.warning(
                "El producto %s tiene ';' o '|' en el código o el nombre: la venta se "
                "guarda igual en el detalle nuevo, pero conviene renombrarlo en el catálogo.",
                producto.codigo,
            )
        return item

    def interpretar_codigo(self, texto: str) -> tuple[str, float]:
        candidatos = candidatos_de_cantidad(texto)
        if len(candidatos) == 1:
            return candidatos[0]
        existentes = [
            candidato for candidato in candidatos
            if self._gestor_stock.buscar_producto(candidato[0]) is not None
        ]
        if not existentes:
            return candidatos[0]
        existentes.sort(key=lambda candidato: len(candidato[0]), reverse=True)
        return existentes[0]

    def agregar_comodin(self, descripcion: str, cantidad: float,
                        precio_unitario: float) -> ItemVenta:
        return self._venta.agregar_comodin(descripcion, cantidad, precio_unitario)

    def cobrar(self, fecha: date, monto_recibido: float = 0.0, medio_pago: str = "",
             datos_pago: str = "", usuario: str = "", cliente: str = "",
             pagos: tuple[PagoVenta, ...] = ()) -> VentaRegistrada:
        if self._venta.esta_vacia():
            raise ErrorValidacion("No hay productos en la lista de venta.")
        total_cobrar = round(self._venta.total, 2)
        fiado = self._validar_pagos(tuple(pagos), total_cobrar, cliente)
        if pagos:
            if fiado is None:
                cliente = ""
            monto_recibido = 0.0
            medio_pago = ""
            datos_pago = ""
        elif monto_recibido and monto_recibido < total_cobrar:
            raise ErrorValidacion("El monto recibido es menor al total.")
        monto = monto_recibido or total_cobrar
        es_fiado = fiado is not None or medio_pago == METODO_FIADO
        if es_fiado and fiado is None:
            if self._fiado is None:
                raise ErrorValidacion("El fiado no está disponible.")
            self._fiado.validar_cargo(cliente, total_cobrar)
        for item in self._venta.items:
            if item.es_comodin:
                continue
            self._gestor_stock.registrar_movimiento(
                MovimientoSalida.TIPO, item.codigo, item.cantidad, fecha, self.MOTIVO_VENTA
            )

        comprobante = VentaRegistrada.desde_venta(
            self._venta, fecha, datetime.now(), monto_recibido=monto,
            medio_pago=medio_pago, datos_pago=datos_pago, usuario=usuario,
            cliente=cliente if es_fiado else "", pagos=tuple(pagos))
        if es_fiado:
            assert self._fiado is not None
            importe_fiado = fiado.importe if fiado is not None else comprobante.total
            self._fiado.registrar_cargo(
                cliente, importe_fiado, fecha,
                f"Venta {comprobante.identificador}", usuario)
        self._estadisticas.registrar(comprobante)
        return comprobante

    def _validar_pagos(self, pagos: tuple[PagoVenta, ...], total: float,
                       cliente: str) -> PagoVenta | None:
        if not pagos:
            return None
        suma = round(sum(pago.importe for pago in pagos), 2)
        if round(abs(suma - total), 2) > 0.01:
            raise ErrorValidacion(
                f"La suma de los pagos ({suma:.2f}) no coincide con el total"
                f" ({total:.2f}).")
        fiados = [pago for pago in pagos if pago.medio == METODO_FIADO]
        if len(fiados) > 1:
            raise ErrorValidacion("Solo se admite un pago fiado por venta.")
        if not fiados:
            return None
        fiado = fiados[0]
        if self._fiado is None:
            raise ErrorValidacion("El fiado no está disponible.")
        if not cliente.strip():
            raise ErrorValidacion("Elegí el cliente para la venta fiada.")
        self._fiado.validar_cargo(cliente, fiado.importe)
        return fiado

    def aplicar_descuento_linea(self, codigo: str, descuento: float) -> None:
        for item in self._venta.items:
            if item.codigo == codigo:
                item.aplicar_descuento(descuento)
                return
        raise ProductoNoEncontradoError(codigo)

    def anular(self, identificador: str, fecha: date, motivo: str = "") -> list[str]:
        comprobante = self._estadisticas.buscar(identificador)
        if comprobante is None:
            raise ErrorValidacion("No se encontró la venta indicada.")
        if comprobante.anulada:
            raise ErrorValidacion("La venta ya estaba anulada.")
        self._plazo.verificar(comprobante)

        texto_anulacion = f"Anulación {identificador}"
        if motivo.strip():
            texto_anulacion = f"{texto_anulacion}: {motivo.strip()}"

        faltantes: list[str] = []
        for renglon in comprobante.detalle:
            if es_codigo_comodin(renglon.codigo):
                continue
            if self._gestor_stock.buscar_producto(renglon.codigo) is None:
                faltantes.append(renglon.codigo)
                continue
            self._gestor_stock.registrar_movimiento(
                MovimientoEntrada.TIPO,
                renglon.codigo, renglon.cantidad, fecha,
                texto_anulacion,
            )
        comprobante.anular()
        if (comprobante.importe_fiado > 0 and comprobante.cliente
                and self._fiado is not None):
            self._fiado.reversar_cargo(
                comprobante.cliente, comprobante.importe_fiado, fecha,
                texto_anulacion)
        self._estadisticas.actualizar(comprobante)
        return faltantes

    def motivo_bloqueo_anulacion(self, venta) -> str:
        return self._plazo.motivo_bloqueo(venta)

    def nueva_venta(self) -> None:
        self._venta.vaciar()
