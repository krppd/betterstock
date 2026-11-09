from datetime import date

import pytest

from models.cliente import Cliente
from models.medio_pago import METODO_EFECTIVO, METODO_FIADO
from models.movimiento_cuenta import MovimientoCuenta
from models.producto import Producto
from models.venta_registrada import VentaRegistrada
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cliente_repositorio import ClienteRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.cierre_caja import ServicioCierre
from services.estadisticas_ventas import EstadisticasVentas
from services.excepciones import ErrorValidacion
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from repositories.cierre_repositorio import CierreRepositorio

HOY = date(2026, 10, 14)


def armar_fiado(tmp_path):
    clientes = ClienteRepositorio(tmp_path / "clientes.csv")
    cuenta = CuentaRepositorio(tmp_path / "cuenta.csv")
    fiado = GestorFiado(clientes, cuenta)
    fiado.inicializar()
    return fiado


def armar_ventas(tmp_path, fiado=None):
    stock = GestorStock(
        ProductoRepositorio(tmp_path / "p.csv"),
        MovimientoRepositorio(tmp_path / "m.csv"),
        CategoriaRepositorio(tmp_path / "c.csv"))
    stock.inicializar()
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Martillo", precio_costo=8500,
        precio_venta=12900, stock_actual=10, stock_minimo=2))
    estadisticas = EstadisticasVentas(VentaRepositorio(tmp_path / "v.csv"))
    estadisticas.inicializar()
    return stock, GestorVentas(stock, estadisticas, fiado), estadisticas


def test_cliente_exige_nombre():
    with pytest.raises(ValueError):
        Cliente("   ")


def test_cliente_exige_limite_no_negativo():
    with pytest.raises(ValueError):
        Cliente("Juan", limite=-10)


def test_guardar_y_buscar_cliente(tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan Pérez", telefono="123", limite=50000)
    assert cliente.identificador == "1"
    assert fiado.buscar_cliente("1").nombre == "Juan Pérez"
    assert fiado.buscar_clientes("juan")[0].telefono == "123"


def test_nombre_duplicado_falla(tmp_path):
    fiado = armar_fiado(tmp_path)
    fiado.guardar_cliente("Juan Pérez")
    with pytest.raises(ErrorValidacion):
        fiado.guardar_cliente("  juan pérez  ")


def test_movimiento_cuenta_valida_datos():
    with pytest.raises(ValueError):
        MovimientoCuenta(HOY, "1", "otro", 100)
    with pytest.raises(ValueError):
        MovimientoCuenta(HOY, "1", "cargo", 0)
    with pytest.raises(ValueError):
        MovimientoCuenta(HOY, "  ", "cargo", 100)


def test_saldo_cargos_menos_pagos(tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan")
    assert fiado.saldo(cliente.identificador) == 0
    fiado.registrar_cargo(cliente.identificador, 10000, HOY, usuario="admin")
    fiado.registrar_cargo(cliente.identificador, 5000, HOY, usuario="admin")
    fiado.registrar_pago(cliente.identificador, 4000, HOY, METODO_EFECTIVO, usuario="admin")
    assert fiado.saldo(cliente.identificador) == 11000


def test_limite_cero_es_sin_tope(tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan", limite=0)
    assert fiado.validar_cargo(cliente.identificador, 99999999) == 99999999


def test_cargo_sobre_limite_falla(tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan", limite=10000)
    fiado.registrar_cargo(cliente.identificador, 8000, HOY)
    with pytest.raises(ErrorValidacion, match="límite"):
        fiado.registrar_cargo(cliente.identificador, 3000, HOY)


def test_cargo_a_inactivo_falla(tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan")
    fiado.desactivar(cliente.identificador)
    with pytest.raises(ErrorValidacion, match="baja"):
        fiado.registrar_cargo(cliente.identificador, 1000, HOY)


def test_pago_mayor_que_deuda_falla(tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan")
    fiado.registrar_cargo(cliente.identificador, 5000, HOY)
    with pytest.raises(ErrorValidacion, match="supera la deuda"):
        fiado.registrar_pago(cliente.identificador, 5001, HOY, METODO_EFECTIVO)


def test_pago_con_medio_invalido_falla(tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan")
    fiado.registrar_cargo(cliente.identificador, 5000, HOY)
    with pytest.raises(ErrorValidacion, match="medio"):
        fiado.registrar_pago(cliente.identificador, 1000, HOY, "trueque")


def test_pago_parcial_deja_resto(tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan")
    fiado.registrar_cargo(cliente.identificador, 5000, HOY)
    fiado.registrar_pago(cliente.identificador, 2000, HOY, METODO_EFECTIVO)
    assert fiado.saldo(cliente.identificador) == 3000


def test_venta_fiada_completa(tmp_path):
    fiado = armar_fiado(tmp_path)
    stock, ventas, _ = armar_ventas(tmp_path, fiado)
    cliente = fiado.guardar_cliente("Juan", limite=50000)
    ventas.agregar_producto("1001")
    comprobante = ventas.cobrar(
        HOY, monto_recibido=12900, medio_pago=METODO_FIADO, usuario="admin",
        cliente=cliente.identificador)
    assert comprobante.medio_pago == METODO_FIADO
    assert comprobante.cliente == cliente.identificador
    assert fiado.saldo(cliente.identificador) == 12900
    assert stock.buscar_producto("1001").stock_actual == 9


def test_venta_fiada_sin_cliente_falla(tmp_path):
    fiado = armar_fiado(tmp_path)
    _, ventas, _ = armar_ventas(tmp_path, fiado)
    ventas.agregar_producto("1001")
    with pytest.raises(ErrorValidacion, match="cliente"):
        ventas.cobrar(HOY, monto_recibido=12900, medio_pago=METODO_FIADO)


def test_venta_fiada_sobre_limite_no_mueve_stock(tmp_path):
    fiado = armar_fiado(tmp_path)
    stock, ventas, _ = armar_ventas(tmp_path, fiado)
    cliente = fiado.guardar_cliente("Juan", limite=10000)
    ventas.agregar_producto("1001")
    with pytest.raises(ErrorValidacion, match="límite"):
        ventas.cobrar(
            HOY, monto_recibido=12900, medio_pago=METODO_FIADO,
            cliente=cliente.identificador)
    assert stock.buscar_producto("1001").stock_actual == 10
    assert fiado.saldo(cliente.identificador) == 0


def test_anular_fiada_reversa_cargo(tmp_path):
    fiado = armar_fiado(tmp_path)
    _, ventas, _ = armar_ventas(tmp_path, fiado)
    cliente = fiado.guardar_cliente("Juan")
    ventas.agregar_producto("1001")
    hoy = date.today()
    comprobante = ventas.cobrar(
        hoy, monto_recibido=12900, medio_pago=METODO_FIADO,
        cliente=cliente.identificador)
    ventas.anular(comprobante.identificador, hoy)
    assert fiado.saldo(cliente.identificador) == 0


def test_cierre_espera_pagos_en_efectivo(tmp_path):
    fiado = armar_fiado(tmp_path)
    _, _, estadisticas = armar_ventas(tmp_path, fiado)
    cierre = ServicioCierre(
        estadisticas, CierreRepositorio(tmp_path / "c.csv"), fiado)
    cierre.inicializar()
    cliente = fiado.guardar_cliente("Juan")
    fiado.registrar_cargo(cliente.identificador, 10000, HOY)
    fiado.registrar_pago(cliente.identificador, 4000, HOY, METODO_EFECTIVO)
    arqueo = cierre.arqueo(HOY)
    assert arqueo.esperado_por_medio.efectivo == 4000


def test_venta_fiada_no_suma_efectivo_al_cierre(tmp_path):
    fiado = armar_fiado(tmp_path)
    _, ventas, estadisticas = armar_ventas(tmp_path, fiado)
    cierre = ServicioCierre(
        estadisticas, CierreRepositorio(tmp_path / "c.csv"), fiado)
    cierre.inicializar()
    cliente = fiado.guardar_cliente("Juan")
    ventas.agregar_producto("1001")
    ventas.cobrar(
        HOY, monto_recibido=12900, medio_pago=METODO_FIADO,
        cliente=cliente.identificador)
    arqueo = cierre.arqueo(HOY)
    assert arqueo.esperado_por_medio.efectivo == 0
    assert arqueo.esperado_por_medio.de(METODO_FIADO) == 12900


def test_venta_vieja_sin_cliente_se_lee(tmp_path):
    fila = {
        "fecha": "01/10/2026", "hora": "10:00:00", "total": "100.00",
        "detalle": "1;Algo;2;50.00;21.0;0", "descuento_global": "0",
        "recargo": "0", "monto_recibido": "100.00", "vuelto": "0.00",
        "estado": "activa", "medio_pago": "efectivo", "datos_pago": "",
        "usuario": "admin",
    }
    venta = VentaRegistrada.from_dict(fila)
    assert venta.cliente == ""
