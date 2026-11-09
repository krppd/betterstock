from __future__ import annotations

from datetime import date

import pytest

from models.medio_pago import METODO_EFECTIVO
from models.movimiento import MovimientoSalida
from models.producto import Producto
from models.venta import PREFIJO_COMODIN, Venta, es_codigo_comodin
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.excepciones import ErrorValidacion
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from services.ticket import _lineas_ticket

HOY = date(2026, 10, 18)
PRECIO_MARTILLO = 12900.0


def armar_ventas(tmp_path):
    """Arma el gestor de ventas sobre una base SQLite temporal, nunca la real."""
    base = tmp_path / "comodin.db"
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base))
    stock.inicializar()
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Martillo", precio_costo=8500,
        precio_venta=12900, stock_actual=10, stock_minimo=2))
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    return stock, GestorVentas(stock, estadisticas), estadisticas


def salidas(stock, codigo: str) -> list:
    return [m for m in stock.filtrar_movimientos(HOY, HOY, MovimientoSalida.TIPO)
            if m.codigo_producto == codigo]


def test_codigo_comodin_usa_prefijo_interno_inquebrantable():
    assert PREFIJO_COMODIN == "COMODIN"
    assert es_codigo_comodin(f"{PREFIJO_COMODIN}-1")
    assert es_codigo_comodin(f"{PREFIJO_COMODIN}-42")
    assert not es_codigo_comodin("1001")
    assert not es_codigo_comodin(f"{PREFIJO_COMODIN}")
    assert ";" not in PREFIJO_COMODIN and "|" not in PREFIJO_COMODIN


def test_codigo_comodin_no_pisa_ni_rueda_al_reiniciar():
    venta = Venta()
    primero = venta.agregar_comodin("Pila AA", 1, 500)
    segundo = venta.agregar_comodin("Pila AA", 4, 500)
    assert primero.codigo == f"{PREFIJO_COMODIN}-1"
    assert segundo.codigo == f"{PREFIJO_COMODIN}-2"
    assert primero.es_comodin and segundo.es_comodin
    assert venta.total == 2500
    venta.vaciar()
    assert venta.agregar_comodin("Pila AA", 1, 500).codigo == f"{PREFIJO_COMODIN}-1"


def test_comodin_pide_descripcion_y_respeta_separadores():
    venta = Venta()
    with pytest.raises(ValueError):
        venta.agregar_comodin("   ", 1, 500)
    with pytest.raises(ValueError):
        venta.agregar_comodin("Pila; AA", 1, 500)
    with pytest.raises(ValueError):
        venta.agregar_comodin("Pila | AA", 1, 500)
    assert venta.esta_vacia()


def test_comodin_entra_al_total_de_la_venta(tmp_path):
    _, ventas, _ = armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    item = ventas.agregar_comodin("Service de taladro", 2, 3500)
    assert item.es_comodin
    assert item.subtotal == 7000
    assert ventas.venta.total == PRECIO_MARTILLO + 7000


def test_cobrar_con_comodin_no_toca_el_stock(tmp_path):
    stock, ventas, _ = armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    ventas.agregar_comodin("Service de taladro", 2, 3500)
    comprobante = ventas.cobrar(
        HOY, monto_recibido=20000, medio_pago=METODO_EFECTIVO, usuario="admin")
    assert comprobante.total == PRECIO_MARTILLO + 7000
    assert comprobante.vuelto == 20000 - (PRECIO_MARTILLO + 7000)
    assert comprobante.monto_recibido == 20000


def test_comodin_no_genera_movimiento_de_salida(tmp_path):
    stock, ventas, _ = armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    ventas.agregar_comodin("Service de taladro", 2, 3500)
    ventas.cobrar(HOY, monto_recibido=20000, medio_pago=METODO_EFECTIVO)
    assert not [m for m in stock.listar_movimientos_recientes()
                if m.codigo_producto.startswith(f"{PREFIJO_COMODIN}-")]
    assert stock.buscar_producto("1001").stock_actual == 9


def test_producto_normal_sigue_generando_su_salida(tmp_path):
    stock, ventas, _ = armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    ventas.agregar_producto("1001")
    ventas.agregar_comodin("Service de taladro", 1, 3500)
    ventas.cobrar(HOY, monto_recibido=30000, medio_pago=METODO_EFECTIVO)
    salidas_martillo = salidas(stock, "1001")
    assert len(salidas_martillo) == 1
    assert salidas_martillo[0].cantidad == 2
    assert salidas_martillo[0].tipo == MovimientoSalida.TIPO
    assert salidas(stock, f"{PREFIJO_COMODIN}-1") == []
    assert stock.buscar_producto("1001").stock_actual == 8


def test_venta_registrada_guarda_el_comodin(tmp_path):
    _, ventas, estadisticas = armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    ventas.agregar_comodin("Pila AA recargada", 3, 900)
    ventas.cobrar(HOY, monto_recibido=20000, medio_pago=METODO_EFECTIVO,
                  usuario="admin")
    guardada = estadisticas.ventas_del_dia(HOY)[0]
    assert guardada is not None
    assert guardada.total == PRECIO_MARTILLO + 2700
    assert len(guardada.detalle) == 2
    renglon = guardada.detalle[-1]
    assert renglon.codigo == f"{PREFIJO_COMODIN}-1"
    assert renglon.nombre == "Pila AA recargada"
    assert renglon.cantidad == 3
    assert renglon.precio_unitario == 900
    assert guardada.subtotal_detalle == PRECIO_MARTILLO + 2700
    assert guardada.unidades == 4


def test_detalle_serializado_sobrevive_ida_y_vuelta(tmp_path):
    _, ventas, estadisticas = armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    ventas.agregar_comodin("Empaque con cinta 3 m - caja grande", 1, 0)
    ventas.agregar_comodin("Cinta de papel", 2, 750)
    ventas.cobrar(HOY, monto_recibido=PRECIO_MARTILLO + 1500,
                  medio_pago=METODO_EFECTIVO)
    releida = estadisticas.ventas_del_dia(HOY)[0]
    nombres = [r.nombre for r in releida.detalle]
    assert [r.nombre for r in releida.detalle] == [
        "Martillo", "Empaque con cinta 3 m - caja grande", "Cinta de papel"]
    assert releida.total == PRECIO_MARTILLO + 1500


def test_venta_solo_con_comodin_es_valida(tmp_path):
    stock, ventas, estadisticas = armar_ventas(tmp_path)
    ventas.agregar_comodin("Café molido 500 g", 1, 7500)
    with pytest.raises(ErrorValidacion):
        ventas.cobrar(HOY, monto_recibido=1, medio_pago=METODO_EFECTIVO)
    comprobante = ventas.cobrar(HOY, monto_recibido=7500, medio_pago=METODO_EFECTIVO)
    assert comprobante.total == 7500
    assert comprobante.vuelto == 0
    assert len(estadisticas.ventas_del_dia(HOY)) == 1
    assert stock.listar_movimientos_recientes() == []


def test_anular_venta_con_comodin_no_lo_reporta_como_faltante(tmp_path):
    stock, ventas, estadisticas = armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    ventas.agregar_comodin("Service de taladro", 1, 3500)
    hoy = date.today()
    comprobante = ventas.cobrar(hoy, monto_recibido=20000, medio_pago=METODO_EFECTIVO)
    faltantes = ventas.anular(comprobante.identificador, hoy)
    assert faltantes == []
    assert stock.buscar_producto("1001").stock_actual == 10


def test_ticket_imprime_el_comodin_sin_codigo_de_barras(tmp_path):
    _, ventas, _ = armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    ventas.agregar_comodin("Pila AA recargada", 2, 900)
    lineas = _lineas_ticket(ventas.venta, monto_recibido=20000, vuelto=6100,
                            identificador="2026-10-18 10:00:00",
                            medio=METODO_EFECTIVO)
    textos = [texto for texto, _ in lineas]
    assert any("Pila AA recargada (COMODÍN)" in texto for texto in textos)
    assert any("Martillo" in texto for texto in textos)
    assert any("  2 x $900.00" in texto for texto in textos)
    assert any("TOTAL" in texto for texto in textos)