from __future__ import annotations

from datetime import date

from models.medio_pago import METODO_EFECTIVO
from models.producto import Producto
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas

HOY = date(2026, 10, 19)
PRECIO = 10000.0


def test_cobro_cobra_exactamente_el_total_con_recargo_manual(tmp_path):
    base = tmp_path / "cobro.db"
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base))
    stock.inicializar()
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Martillo", precio_costo=8500,
        precio_venta=PRECIO, stock_actual=10, stock_minimo=2))
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    ventas = GestorVentas(stock, estadisticas)

    ventas.agregar_producto("1001")
    ventas.venta.recargo = 4

    total = ventas.venta.total
    assert total == 10400.0

    comprobante = ventas.cobrar(
        HOY, monto_recibido=11000, medio_pago=METODO_EFECTIVO, datos_pago="")

    assert comprobante.total == total
    assert comprobante.monto_recibido == 11000
    assert comprobante.vuelto == 600
    assert comprobante.recargo == 4
