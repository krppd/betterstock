from __future__ import annotations

import sqlite3
from datetime import date

import pytest
from PyQt6.QtWidgets import QApplication

from models.medio_pago import METODO_EFECTIVO
from models.movimiento import MovimientoEntrada, MovimientoSalida
from models.producto import Producto
from models.venta import candidatos_de_cantidad
from models.venta_registrada import PREFIJO_DETALLE_JSON, RenglonVenta, VentaRegistrada
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.comercio_repositorio import ComercioRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.excepciones import (
    ErrorValidacion,
    LimiteStockError,
    ProductoNoEncontradoError,
)
from services.gestor_comercio import GestorComercio
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from utils.formato import cantidad_a_texto, formatear_cantidad, redondear_cantidad
from views.formulario_producto import FormularioProducto
from views.ventana_ventas import VentanaVentas

HOY = date(2026, 10, 20)
PRECIO = 1000.0


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def _armar_stock(tmp_path) -> tuple[GestorStock, object]:
    base = tmp_path / "fraccion.db"
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base))
    stock.inicializar()
    return stock, base


def _armar_ventas(tmp_path, stock_actual: float = 10.0):
    stock, base = _armar_stock(tmp_path)
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Cable de acero", precio_costo=600,
        precio_venta=PRECIO, stock_actual=stock_actual, stock_minimo=2))
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    return stock, GestorVentas(stock, estadisticas), estadisticas


def test_el_stock_fraccionario_se_guarda_y_se_reeye(tmp_path):
    stock, _ = _armar_stock(tmp_path)
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Clavos", precio_venta=PRECIO, stock_actual=2.5))

    guardado = stock.buscar_producto("1001")
    assert guardado is not None
    assert guardado.stock_actual == 2.5
    assert guardado.tiene_stock()


def test_la_columna_integer_guarda_el_fraccion_como_real(tmp_path):
    stock, base = _armar_stock(tmp_path)
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Clavos", precio_venta=PRECIO, stock_actual=2.5))

    conexion = sqlite3.connect(str(base))
    try:
        tipo = conexion.execute(
            "SELECT typeof(stock_actual) FROM productos WHERE codigo = '1001'"
        ).fetchone()[0]
        valor = conexion.execute(
            "SELECT stock_actual FROM productos WHERE codigo = '1001'"
        ).fetchone()[0]
        declaracion = conexion.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'productos'"
        ).fetchone()[0]
    finally:
        conexion.close()

    assert tipo == "real"
    assert valor == 2.5
    assert "stock_actual INTEGER" in declaracion


def test_un_movimiento_fraccionario_deja_el_stock_fraccionado(tmp_path):
    stock, _ = _armar_stock(tmp_path)
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Clavos", precio_venta=PRECIO, stock_actual=0))

    stock.registrar_movimiento(MovimientoEntrada.TIPO, "1001", 1.25, HOY, "Compra")

    assert stock.buscar_producto("1001").stock_actual == 1.25
    movimientos = stock.listar_movimientos_recientes()
    assert movimientos[0].cantidad == 1.25


def test_la_salida_fraccionaria_deja_el_stock_que_sobra(tmp_path):
    stock, _ = _armar_stock(tmp_path)
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Clavos", precio_venta=PRECIO, stock_actual=3.75))

    stock.registrar_movimiento(MovimientoSalida.TIPO, "1001", 1.25, HOY, "Venta")

    assert stock.buscar_producto("1001").stock_actual == 2.5


def test_vender_fracciones_descuenta_el_stock_y_calcula_el_total(tmp_path):
    stock, ventas, estadisticas = _armar_ventas(tmp_path, stock_actual=10)

    ventas.agregar_producto("1001", 3.5)
    assert ventas.venta.items[0].cantidad == 3.5
    assert ventas.venta.total == 3500

    comprobante = ventas.cobrar(
        HOY, monto_recibido=3500, medio_pago=METODO_EFECTIVO, usuario="cajero")

    assert comprobante.total == 3500
    assert comprobante.detalle[0].cantidad == 3.5
    assert stock.buscar_producto("1001").stock_actual == 6.5
    guardada = estadisticas.ventas_del_dia(HOY)[0]
    assert guardada.detalle[0].cantidad == 3.5


def test_no_se_puede_vender_mas_del_stock_fraccionado(tmp_path):
    _, ventas, _ = _armar_ventas(tmp_path, stock_actual=2.5)

    with pytest.raises(LimiteStockError):
        ventas.agregar_producto("1001", 3)

    ventas.agregar_producto("1001", 2.5)
    assert ventas.venta.items[0].cantidad == 2.5

    with pytest.raises(LimiteStockError):
        ventas.agregar_producto("1001", 0.5)


def test_al_stock_fraccionado_se_le_puede_sumar_una_fraccion_mas(tmp_path):
    _, ventas, _ = _armar_ventas(tmp_path, stock_actual=2.5)

    ventas.agregar_producto("1001", 2.0)
    ventas.agregar_producto("1001", 0.5)

    assert ventas.venta.items[0].cantidad == 2.5


def test_el_detalle_guarda_la_cantidad_fraccionada_y_se_relee(tmp_path):
    _, ventas, estadisticas = _armar_ventas(tmp_path, stock_actual=10)
    ventas.agregar_producto("1001", 3.5)
    ventas.cobrar(HOY, monto_recibido=3500, medio_pago=METODO_EFECTIVO)

    detalle = estadisticas.ventas_del_dia(HOY)[0].to_dict()["detalle"]
    assert detalle.startswith(PREFIJO_DETALLE_JSON)
    assert '"cantidad":"3.5"' in detalle
    assert '"3.0"' not in detalle

    releida = VentaRegistrada.from_dict(
        estadisticas.ventas_del_dia(HOY)[0].to_dict())
    assert releida.detalle[0].cantidad == 3.5
    assert releida.detalle[0].subtotal == 3500


def test_el_parser_legacy_sigue_leyendo_las_ventas_viejas():
    releida = VentaRegistrada.from_dict({
        "fecha": "20/10/2026", "hora": "10:15:00", "total": "3000.00",
        "detalle": "111;a;3;1000.00",
    })
    assert releida.detalle[0].cantidad == 3
    assert releida.detalle[0].subtotal == 3000


def test_el_detalle_viejo_en_json_sigue_entendiéndose():
    releida = VentaRegistrada.from_dict({
        "fecha": "20/10/2026", "hora": "10:15:00", "total": "3500.00",
        "detalle": PREFIJO_DETALLE_JSON +
                   '[{"codigo":"1001","nombre":"Cable","cantidad":3,'
                   '"precio_unitario":1000.0}]',
    })
    assert releida.detalle[0].cantidad == 3


def test_la_cantidad_se_formatea_sin_ceros_de_mas():
    assert formatear_cantidad(2.0) == "2"
    assert formatear_cantidad(3.5) == "3,5"
    assert formatear_cantidad(1.25) == "1,25"
    assert formatear_cantidad(2.5000001) == "2,5"
    assert formatear_cantidad(0) == "0"
    assert cantidad_a_texto(3.5) == "3.5"
    assert cantidad_a_texto(2.0) == "2"


def test_las_cantidades_se_redondean_a_tres_decimales():
    assert redondear_cantidad(2.9999999) == 3.0
    assert redondear_cantidad(0.1 + 0.2) == 0.3
    assert redondear_cantidad("2,5") == 2.5


def test_la_caja_agrega_la_cantidad_escrita_con_asterisco(aplicacion, tmp_path):
    stock, ventas, _ = _armar_ventas(tmp_path, stock_actual=10)
    comercio = GestorComercio(ComercioRepositorio(tmp_path / "comercio.db"))
    comercio.inicializar()
    ventana = VentanaVentas(ventas, comercio, "cajero")

    ventana.ui.txtCodigoBarras.setText("3*1001")
    ventana.agregar_producto()
    assert ventas.venta.items[0].cantidad == 3

    ventana.ui.txtCodigoBarras.setText("1001*3")
    ventana.agregar_producto()
    assert ventas.venta.items[0].cantidad == 6


def test_la_caja_sin_asterisco_agrega_una_unidad(aplicacion, tmp_path):
    _, ventas, _ = _armar_ventas(tmp_path, stock_actual=10)
    comercio = GestorComercio(ComercioRepositorio(tmp_path / "comercio.db"))
    comercio.inicializar()
    ventana = VentanaVentas(ventas, comercio, "cajero")

    ventana.ui.txtCodigoBarras.setText("1001")
    ventana.agregar_producto()
    assert ventas.venta.items[0].cantidad == 1


def test_una_cantidad_cero_no_se_agrega(tmp_path):
    _, ventas, _ = _armar_ventas(tmp_path, stock_actual=10)

    with pytest.raises(ErrorValidacion):
        ventas.agregar_producto("1001", 0)


def test_un_texto_con_asterisco_sin_producto_no_se_agrega(tmp_path):
    _, ventas, _ = _armar_ventas(tmp_path, stock_actual=10)

    with pytest.raises(ProductoNoEncontradoError):
        ventas.agregar_producto("9999", 3)


def test_el_asterisco_solo_separa_numeros(tmp_path):
    assert candidatos_de_cantidad("1001") == [("1001", 1.0)]
    assert candidatos_de_cantidad("3*1001")[0] == ("1001", 3.0)
    assert candidatos_de_cantidad("1001*3")[0] == ("1001", 3.0)
    assert candidatos_de_cantidad("cable*3") == [("cable", 3.0)]
    assert candidatos_de_cantidad("3*cable") == [("cable", 3.0)]
    assert candidatos_de_cantidad("a*b") == [("a*b", 1.0)]
    assert candidatos_de_cantidad("3*2,5")[0] == ("3", 2.5)
    assert candidatos_de_cantidad("1001*") == [("1001*", 1.0)]
    assert candidatos_de_cantidad("1001**2") == [("1001**2", 1.0)]


def test_la_caja_muestra_la_cantidad_sin_ceros_de_mas(aplicacion, tmp_path):
    _, ventas, _ = _armar_ventas(tmp_path, stock_actual=10)
    comercio = GestorComercio(ComercioRepositorio(tmp_path / "comercio.db"))
    comercio.inicializar()
    ventana = VentanaVentas(ventas, comercio, "cajero")

    ventas.agregar_producto("1001", 2.0)
    ventana.actualizar_tabla_y_total()
    assert ventana.ui.tblVentas.item(0, 3).text() == "2"

    ventas.agregar_producto("1001", 1.5)
    ventana.actualizar_tabla_y_total()
    assert ventana.ui.tblVentas.item(0, 3).text() == "3,5"


def test_el_formulario_de_producto_acepta_un_stock_decimal(aplicacion, tmp_path):
    stock, _ = _armar_stock(tmp_path)
    formulario = FormularioProducto(stock)
    formulario.ui.txtCodigo.setText("1001")
    formulario.ui.txtNombre.setText("Clavos")
    formulario.ui.spnStock.setText("2,5")
    formulario.ui.spnStockMinimo.setText("1,25")
    formulario.guardar_producto()

    guardado = stock.buscar_producto("1001")
    assert guardado is not None
    assert guardado.stock_actual == 2.5
    assert guardado.stock_minimo == 1.25


def test_el_comodin_acepta_una_cantidad_fraccionada(tmp_path):
    _, ventas, estadisticas = _armar_ventas(tmp_path, stock_actual=10)
    item = ventas.agregar_comodin("Cinta de papel", 2.5, 750)
    assert item.cantidad == 2.5
    assert item.subtotal == 1875

    ventas.cobrar(HOY, monto_recibido=1875, medio_pago=METODO_EFECTIVO)
    guardada = estadisticas.ventas_del_dia(HOY)[0]
    assert guardada.detalle[0].cantidad == 2.5


def test_la_venta_guardada_tiene_las_unidades_fraccionadas(tmp_path):
    _, ventas, estadisticas = _armar_ventas(tmp_path, stock_actual=10)
    ventas.agregar_producto("1001", 3.5)
    ventas.cobrar(HOY, monto_recibido=3500, medio_pago=METODO_EFECTIVO)
    guardada = estadisticas.ventas_del_dia(HOY)[0]
    assert guardada.unidades == 3.5


def test_el_renglon_de_venta_redondea_la_cantidad():
    renglon = RenglonVenta("1001", "Cable", 2.5000001, 1000.0)
    assert renglon.cantidad == 2.5
