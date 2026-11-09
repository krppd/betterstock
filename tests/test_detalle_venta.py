from __future__ import annotations

import sqlite3
from datetime import date

import pytest

from models.medio_pago import METODO_EFECTIVO, METODO_TRANSFERENCIA
from models.producto import Producto
from models.venta import (
    validar_descripcion_comodin,
    validar_texto_sin_separadores,
)
from models.venta_registrada import (
    PREFIJO_DETALLE_JSON,
    PagoVenta,
    RenglonVenta,
    VentaRegistrada,
)
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from services.ticket import _lineas_ticket

HOY = date(2026, 10, 19)
PRECIO = 10000.0

NOMBRES_RAROS = (
    "Pila; AA",
    "Pila | AA",
    "Pila; AA | BB",
    "Cinta \\ de 3 m; lote | 2",
    'Comilla " y barra \\ invertida',
)


def _venta(detalle: list[RenglonVenta]) -> VentaRegistrada:
    return VentaRegistrada(
        HOY, "10:15:00", 100.0, detalle,
        monto_recibido=100.0, medio_pago=METODO_EFECTIVO, usuario="admin",
    )


def test_pagos_mixtos_se_listan_con_su_importe():
    venta = VentaRegistrada(
        HOY, "10:15:00", 2500.0, [_renglon("Martillo")],
        pagos=(
            PagoVenta(METODO_EFECTIVO, 1000.0, recibido=1000.0),
            PagoVenta(METODO_TRANSFERENCIA, 1500.0, datos="alias.fts"),
        ),
        usuario="empleado",
    )

    from views.ventana_detalle_venta import _pagos_con_importe

    assert _pagos_con_importe(venta) == (
        "Efectivo $ 1.000,00 + Transferencia — alias.fts $ 1.500,00")


def _renglon(nombre: str) -> RenglonVenta:
    return RenglonVenta("1001", nombre, 2, 50.0, 21.0, 5.0)


def _armar_ventas(tmp_path, nombre_producto: str = "Martillo"):
    base = tmp_path / "detalle.db"
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base))
    stock.inicializar()
    stock.guardar_producto(Producto(
        codigo="1001", nombre=nombre_producto, precio_costo=8500,
        precio_venta=PRECIO, stock_actual=10, stock_minimo=2))
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    return base, stock, GestorVentas(stock, estadisticas), estadisticas


def test_detalle_nuevo_se_serializa_en_json_inequivoco():
    venta = _venta([_renglon("Pila; AA | BB")])
    detalle = venta.to_dict()["detalle"]
    assert detalle.startswith(PREFIJO_DETALLE_JSON)
    assert "Pila; AA | BB" in detalle


@pytest.mark.parametrize("nombre", NOMBRES_RAROS)
def test_round_trip_con_nombres_raros(nombre):
    venta = _venta([_renglon(nombre)])
    releida = VentaRegistrada.from_dict(venta.to_dict())
    assert releida.detalle == venta.detalle
    assert releida.detalle[0].nombre == nombre
    assert releida.total == venta.total


def test_round_trip_con_varios_renglones_raros():
    venta = _venta([_renglon(nombre) for nombre in NOMBRES_RAROS])
    releida = VentaRegistrada.from_dict(venta.to_dict())
    assert [r.nombre for r in releida.detalle] == list(NOMBRES_RAROS)
    assert releida.detalle == venta.detalle


def test_el_codigo_tambien_puede_llevar_separadores():
    venta = VentaRegistrada(
        HOY, "10:15:00", 100.0,
        [RenglonVenta("10;01|A", "Martillo", 1, 100.0)])
    releida = VentaRegistrada.from_dict(venta.to_dict())
    assert releida.detalle[0].codigo == "10;01|A"


@pytest.mark.parametrize("detalle", [
    "111;a;3;1000.00",
    "111;a;3;1000.00;21",
    "111;a;3;1000.00;21;0",
])
def test_el_formato_legacy_se_sigue_leyendo(detalle):
    releida = VentaRegistrada.from_dict({
        "fecha": "19/10/2026", "hora": "10:15:00", "total": "3000.00",
        "detalle": detalle,
    })
    assert len(releida.detalle) == 1
    assert releida.detalle[0].codigo == "111"
    assert releida.detalle[0].nombre == "a"
    assert releida.detalle[0].cantidad == 3
    assert releida.detalle[0].precio_unitario == 1000.0


def test_el_formato_legacy_con_punto_y_coma_se_recupera():
    releida = VentaRegistrada.from_dict({
        "fecha": "19/10/2026", "hora": "10:15:00", "total": "200.00",
        "detalle": "1001;Pila;AA;2;100.00",
    })
    assert releida.detalle[0].nombre == "Pila;AA"
    assert releida.detalle[0].cantidad == 2
    assert releida.detalle[0].precio_unitario == 100.0


def test_el_formato_legacy_con_barra_vertical_se_recupera():
    releida = VentaRegistrada.from_dict({
        "fecha": "19/10/2026", "hora": "10:15:00", "total": "200.00",
        "detalle": "1001;Pila | AA;2;100.00",
    })
    assert releida.detalle[0].nombre == "Pila | AA"
    assert releida.detalle[0].cantidad == 2


def test_venta_con_producto_raro_no_desaparece_del_listar(tmp_path):
    base, _, ventas, estadisticas = _armar_ventas(tmp_path, "Pila; AA | BB")
    ventas.agregar_producto("1001")
    ventas.cobrar(HOY, monto_recibido=PRECIO, medio_pago=METODO_EFECTIVO,
                  usuario="admin")

    guardadas = VentaRepositorio(base).listar()
    assert len(guardadas) == 1
    assert guardadas[0].detalle[0].nombre == "Pila; AA | BB"
    assert guardadas[0].total == PRECIO

    historial = estadisticas.ventas_del_periodo(HOY, HOY)
    assert len(historial) == 1
    assert historial[0].detalle[0].nombre == "Pila; AA | BB"
    assert estadisticas.resumen(HOY, HOY).total == PRECIO
    assert VentaRepositorio(base).errores_lectura == []


def test_venta_con_producto_raro_se_puede_anular(tmp_path):
    base, stock, ventas, _ = _armar_ventas(tmp_path, "Pila; AA")
    ventas.agregar_producto("1001")
    hoy = date.today()
    comprobante = ventas.cobrar(hoy, monto_recibido=PRECIO,
                                 medio_pago=METODO_EFECTIVO)
    assert comprobante.identificador
    ventas.anular(comprobante.identificador, hoy)
    anuladas = VentaRepositorio(base).listar()
    assert len(anuladas) == 1
    assert anuladas[0].anulada
    assert anuladas[0].detalle[0].nombre == "Pila; AA"
    assert stock.buscar_producto("1001").stock_actual == 10


def test_un_detalle_ilegible_se_reporta_y_no_se_traga(tmp_path):
    base, _, _, _ = _armar_ventas(tmp_path)
    conexion = sqlite3.connect(str(base))
    conexion.execute(
        "INSERT INTO ventas(fecha, hora, total, detalle, descuento_global, recargo,"
        " monto_recibido, vuelto, estado, medio_pago, datos_pago, usuario, cliente)"
        " VALUES ('2026-10-19', '11:00:00', 500.0, 'esto no es una venta', 0, 0,"
        " 500.0, 0, 'activa', '', '', 'admin', '')")
    conexion.commit()
    conexion.close()

    repositorio = VentaRepositorio(base)
    assert repositorio.listar() == []
    errores = repositorio.errores_lectura
    assert len(errores) == 1
    assert errores[0]["hora"] == "11:00:00"
    assert errores[0]["total"] == "500.0"
    assert "Detalle de venta inválido" in errores[0]["motivo"]


def test_el_detalle_ilegible_no_borra_las_ventas_buenas(tmp_path):
    base, _, ventas, _ = _armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    ventas.cobrar(HOY, monto_recibido=PRECIO, medio_pago=METODO_EFECTIVO)
    conexion = sqlite3.connect(str(base))
    conexion.execute(
        "INSERT INTO ventas(fecha, hora, total, detalle, descuento_global, recargo,"
        " monto_recibido, vuelto, estado, medio_pago, datos_pago, usuario, cliente)"
        " VALUES ('2026-10-19', '11:00:00', 500.0, 'basura', 0, 0,"
        " 500.0, 0, 'activa', '', '', 'admin', '')")
    conexion.commit()
    conexion.close()

    repositorio = VentaRepositorio(base)
    leidas = repositorio.listar()
    assert len(leidas) == 1
    assert leidas[0].total == PRECIO
    assert len(repositorio.errores_lectura) == 1


def test_la_venta_con_nombre_raro_pide_renombrar_el_producto(tmp_path):
    _, _, ventas, _ = _armar_ventas(tmp_path, "Pila; AA")
    item = ventas.agregar_producto("1001")
    assert item.texto_ambiguo
    assert item.nombre == "Pila; AA"


def test_el_producto_normal_no_se_marca_ambiguo(tmp_path):
    _, _, ventas, _ = _armar_ventas(tmp_path)
    item = ventas.agregar_producto("1001")
    assert not item.texto_ambiguo


def test_un_codigo_que_empieza_como_el_prefijo_nuevo_sigue_leyendose_legacy():
    releida = VentaRegistrada.from_dict({
        "fecha": "19/10/2026", "hora": "10:15:00", "total": "300.00",
        "detalle": "J1:;Pila;3;100.00",
    })
    assert releida.detalle[0].codigo == "J1:"
    assert releida.detalle[0].nombre == "Pila"
    assert releida.detalle[0].cantidad == 3


def test_un_json_corrupto_se_reporta():
    with pytest.raises(ValueError):
        VentaRegistrada.from_dict({
            "fecha": "19/10/2026", "hora": "10:15:00", "total": "300.00",
            "detalle": "J1:{basura",
        })


def test_el_ticket_muestra_el_nombre_raro_como_es(tmp_path):
    _, _, ventas, _ = _armar_ventas(tmp_path, "Pila; AA | 3 m")
    ventas.agregar_producto("1001")
    lineas = _lineas_ticket(ventas.venta, monto_recibido=PRECIO, vuelto=0,
                            identificador="2026-10-19 10:00:00",
                            medio=METODO_EFECTIVO)
    assert any("Pila; AA | 3 m" in texto for texto, _ in lineas)


def test_el_texto_del_producto_no_puede_llevar_separadores():
    with pytest.raises(ValueError):
        validar_texto_sin_separadores("Pila; AA", "El nombre del producto")
    with pytest.raises(ValueError):
        validar_texto_sin_separadores("Pila | AA", "El nombre del producto")
    with pytest.raises(ValueError):
        validar_texto_sin_separadores("10;01", "El código del producto")
    assert validar_texto_sin_separadores("Pila AA", "El nombre del producto") == "Pila AA"


def test_el_comodin_sigue_rechazando_los_separadores():
    with pytest.raises(ValueError):
        validar_descripcion_comodin("Pila; AA")
    with pytest.raises(ValueError):
        validar_descripcion_comodin("Pila | AA")
    with pytest.raises(ValueError):
        validar_descripcion_comodin("   ")
    assert validar_descripcion_comodin("Pila AA") == "Pila AA"
