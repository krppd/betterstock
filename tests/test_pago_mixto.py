from __future__ import annotations

from datetime import date

import pytest

from models.cierre import ResumenMedios
from models.medio_pago import (
    METODO_DEBITO,
    METODO_EFECTIVO,
    METODO_FIADO,
    METODO_MIXTO,
    METODO_MP,
)
from models.producto import Producto
from models.venta_registrada import (
    PREFIJO_PAGOS_JSON,
    PagoVenta,
    RenglonVenta,
    VentaRegistrada,
)
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cliente_repositorio import ClienteRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.excepciones import ErrorValidacion
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas

HOY = date(2026, 10, 19)
PRECIO = 12900.0
TOTAL = 12900.0


def _detalle() -> list[RenglonVenta]:
    return [RenglonVenta("1001", "Martillo", 1, TOTAL)]


def _venta_registrada(pagos: tuple[PagoVenta, ...]) -> VentaRegistrada:
    return VentaRegistrada(
        HOY, "10:15:00", TOTAL, _detalle(), usuario="admin", pagos=pagos
    )


def _armar_fiado(tmp_path) -> GestorFiado:
    fiado = GestorFiado(
        ClienteRepositorio(tmp_path / "clientes.csv"),
        CuentaRepositorio(tmp_path / "cuenta.csv"),
    )
    fiado.inicializar()
    return fiado


def _armar_ventas(tmp_path, fiado=None):
    stock = GestorStock(
        ProductoRepositorio(tmp_path / "p.csv"),
        MovimientoRepositorio(tmp_path / "m.csv"),
        CategoriaRepositorio(tmp_path / "c.csv"))
    stock.inicializar()
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Martillo", precio_costo=8500,
        precio_venta=PRECIO, stock_actual=10, stock_minimo=2))
    estadisticas = EstadisticasVentas(VentaRepositorio(tmp_path / "v.csv"))
    estadisticas.inicializar()
    return stock, GestorVentas(stock, estadisticas, fiado), estadisticas


def test_el_pago_en_efectivo_calcula_el_vuelto():
    pago = PagoVenta(METODO_EFECTIVO, 100, recibido=150)
    assert pago.recibido == 150
    assert pago.importe == 100
    assert pago.vuelto == 50


def test_el_pago_no_efectivo_no_tiene_vuelto():
    pago = PagoVenta(METODO_MP, 100, recibido=500, datos="p-1")
    assert pago.recibido == 100
    assert pago.vuelto == 0
    assert pago.datos == "p-1"


def test_el_pago_valida_medio_importe_y_efectivo():
    with pytest.raises(ValueError):
        PagoVenta("  ", 100)
    with pytest.raises(ValueError):
        PagoVenta(METODO_EFECTIVO, 0)
    with pytest.raises(ValueError):
        PagoVenta(METODO_EFECTIVO, -5)
    with pytest.raises(ValueError):
        PagoVenta(METODO_EFECTIVO, 100, recibido=50)


def test_el_pago_en_efectivo_sube_el_recibido_al_importe():
    assert PagoVenta(METODO_EFECTIVO, 100).recibido == 100


def test_la_venta_mixta_arma_los_campos_legacy():
    venta = _venta_registrada((
        PagoVenta(METODO_EFECTIVO, 60, recibido=100),
        PagoVenta(METODO_DEBITO, 90, datos="1234"),
    ))
    assert len(venta.pagos) == 2
    assert venta.medio_pago == METODO_MIXTO
    assert venta.monto_recibido == 100
    assert venta.vuelto == 40
    assert venta.datos_pago == "1234"
    assert venta.importe_fiado == 0


def test_un_solo_pago_mantiene_el_medio():
    venta = _venta_registrada((PagoVenta(METODO_EFECTIVO, TOTAL, recibido=13200),))
    assert venta.medio_pago == METODO_EFECTIVO
    assert venta.monto_recibido == 13200
    assert venta.vuelto == 300


def test_el_legado_deriva_un_pago_unico():
    legado = VentaRegistrada(
        HOY, "10:15:00", 100.0, _detalle(),
        monto_recibido=130, medio_pago=METODO_EFECTIVO)
    assert len(legado.pagos) == 1
    pago = legado.pagos[0]
    assert pago.medio == METODO_EFECTIVO
    assert pago.importe == 100
    assert pago.recibido == 130
    assert pago.vuelto == 30
    assert legado.medio_pago_texto == "Efectivo"

    fiado = VentaRegistrada(
        HOY, "10:15:00", 200.0, _detalle(),
        monto_recibido=200, medio_pago=METODO_FIADO, cliente="1")
    assert fiado.importe_fiado == 200
    assert fiado.cliente == "1"


def test_la_venta_sin_medio_no_deriva_pagos():
    venta = VentaRegistrada(HOY, "10:15:00", 100.0, _detalle())
    assert venta.pagos == ()
    assert venta.importe_fiado == 0
    assert venta.medios_texto == ""


def test_el_texto_de_medios_detalle_los_pagos():
    mixta = _venta_registrada((
        PagoVenta(METODO_EFECTIVO, 60),
        PagoVenta(METODO_DEBITO, 90, datos="1234"),
    ))
    assert mixta.medio_pago_texto == "Efectivo + Débito — 1234"


def test_los_pagos_sobreviven_una_vuelta_por_diccionario():
    venta = _venta_registrada((
        PagoVenta(METODO_EFECTIVO, 60, recibido=100),
        PagoVenta(METODO_MP, 90, datos="p-1"),
    ))
    datos = venta.to_dict()
    assert datos["pagos"].startswith(PREFIJO_PAGOS_JSON)
    relectura = VentaRegistrada.from_dict(datos)
    assert relectura.pagos == venta.pagos
    assert relectura.medio_pago == METODO_MIXTO
    assert relectura.monto_recibido == 100
    assert relectura.vuelto == 40


def test_el_diccionario_legado_se_lee_sin_pagos():
    datos = VentaRegistrada(
        HOY, "10:15:00", 100.0, _detalle(),
        monto_recibido=130, medio_pago=METODO_EFECTIVO).to_dict()
    datos.pop("pagos")
    relectura = VentaRegistrada.from_dict(datos)
    assert len(relectura.pagos) == 1
    assert relectura.pagos[0].importe == 100


def test_los_pagos_con_json_invalido_fallan():
    with pytest.raises(ValueError):
        VentaRegistrada.from_dict({
            **VentaRegistrada(HOY, "10:15:00", 100.0, _detalle()).to_dict(),
            "pagos": "1;" + PREFIJO_PAGOS_JSON,
        })


def test_los_pagos_se_guardan_y_se_lee_de_la_base(tmp_path):
    ventas = VentaRepositorio(tmp_path / "v.csv")
    venta = _venta_registrada((
        PagoVenta(METODO_EFECTIVO, 60, recibido=100),
        PagoVenta(METODO_MP, 90, datos="p-1"),
    ))
    ventas.agregar(venta)
    leida = ventas.buscar(venta.identificador)
    assert leida.pagos == venta.pagos
    assert leida.medio_pago == METODO_MIXTO
    assert leida.medios_texto == venta.medios_texto
    venta.anular()
    ventas.actualizar(venta)
    guardada = ventas.buscar(venta.identificador)
    assert guardada.anulada
    assert guardada.pagos == venta.pagos


def test_la_venta_legada_se_guarda_sin_pagos(tmp_path):
    ventas = VentaRepositorio(tmp_path / "v.csv")
    venta = VentaRegistrada(
        HOY, "10:15:00", 100.0, _detalle(),
        monto_recibido=100, medio_pago=METODO_MP, datos_pago="p-9")
    ventas.agregar(venta)
    leida = ventas.buscar(venta.identificador)
    assert len(leida.pagos) == 1
    assert leida.pagos[0].medio == METODO_MP
    assert leida.pagos[0].datos == "p-9"
    assert leida.medio_pago == METODO_MP


def test_el_cobro_mixto_guarda_los_pagos(tmp_path):
    stock, ventas, estadisticas = _armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    comprobante = ventas.cobrar(HOY, usuario="cajero", pagos=(
        PagoVenta(METODO_EFECTIVO, 10000),
        PagoVenta(METODO_MP, 2900, datos="p-1"),
    ))
    assert comprobante.medio_pago == METODO_MIXTO
    assert comprobante.monto_recibido == 10000
    assert comprobante.vuelto == 0
    assert stock.buscar_producto("1001").stock_actual == 9
    guardada = estadisticas.buscar(comprobante.identificador)
    assert guardada.pagos == comprobante.pagos


def test_el_cobro_en_efectivo_registra_el_vuelto(tmp_path):
    stock, ventas, _ = _armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    comprobante = ventas.cobrar(HOY, pagos=(
        PagoVenta(METODO_EFECTIVO, TOTAL, recibido=15000),
    ))
    assert comprobante.medio_pago == METODO_EFECTIVO
    assert comprobante.monto_recibido == 15000
    assert comprobante.vuelto == 2100


def test_la_suma_de_los_pagos_debe_dar_el_total(tmp_path):
    stock, ventas, _ = _armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    total = round(ventas.venta.total, 2)
    with pytest.raises(ErrorValidacion):
        ventas.cobrar(HOY, pagos=(PagoVenta(METODO_EFECTIVO, total - 1000),))
    with pytest.raises(ErrorValidacion):
        ventas.cobrar(HOY, pagos=(PagoVenta(METODO_EFECTIVO, total + 1),))
    assert stock.buscar_producto("1001").stock_actual == 10


def test_la_suma_de_los_pagos_toma_un_centavo_de_margen(tmp_path):
    _, ventas, _ = _armar_ventas(tmp_path)
    ventas.agregar_producto("1001")
    total = round(ventas.venta.total, 2)
    comprobante = ventas.cobrar(HOY, pagos=(
        PagoVenta(METODO_EFECTIVO, 6450),
        PagoVenta(METODO_MP, total - 6450.01),
    ))
    assert len(comprobante.pagos) == 2
    with pytest.raises(ErrorValidacion):
        ventas.cobrar(HOY, pagos=(
            PagoVenta(METODO_EFECTIVO, 6450),
            PagoVenta(METODO_MP, round(total - 6450.01, 2) - 0.01),
        ))


def test_no_puede_haber_dos_pagos_fiados(tmp_path):
    fiado = _armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan")
    _, ventas, _ = _armar_ventas(tmp_path, fiado)
    ventas.agregar_producto("1001")
    mitad = TOTAL / 2
    with pytest.raises(ErrorValidacion):
        ventas.cobrar(HOY, cliente=cliente.identificador, pagos=(
            PagoVenta(METODO_FIADO, mitad),
            PagoVenta(METODO_FIADO, TOTAL - mitad),
        ))


def test_el_fiado_parcial_sale_con_el_resto_en_efectivo(tmp_path):
    fiado = _armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan", limite=100000)
    stock, ventas, estadisticas = _armar_ventas(tmp_path, fiado)
    ventas.agregar_producto("1001")
    comprobante = ventas.cobrar(HOY, cliente=cliente.identificador, pagos=(
        PagoVenta(METODO_EFECTIVO, 6900),
        PagoVenta(METODO_FIADO, 6000),
    ))
    assert comprobante.medio_pago == METODO_MIXTO
    assert comprobante.importe_fiado == 6000
    assert comprobante.cliente == "1"
    assert fiado.saldo("1") == 6000
    assert stock.buscar_producto("1001").stock_actual == 9
    guardada = estadisticas.buscar(comprobante.identificador)
    assert guardada.importe_fiado == 6000


def test_el_fiado_parcial_respeta_el_limite(tmp_path):
    fiado = _armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan", limite=5000)
    _, ventas, _ = _armar_ventas(tmp_path, fiado)
    ventas.agregar_producto("1001")
    with pytest.raises(ErrorValidacion):
        ventas.cobrar(HOY, cliente=cliente.identificador, pagos=(
            PagoVenta(METODO_EFECTIVO, 6900),
            PagoVenta(METODO_FIADO, 6000),
        ))


def test_el_fiado_parcial_exige_cliente(tmp_path):
    fiado = _armar_fiado(tmp_path)
    _, ventas, _ = _armar_ventas(tmp_path, fiado)
    ventas.agregar_producto("1001")
    with pytest.raises(ErrorValidacion):
        ventas.cobrar(HOY, pagos=(
            PagoVenta(METODO_EFECTIVO, 6900),
            PagoVenta(METODO_FIADO, 6000),
        ))


def test_la_anulacion_revierte_solo_el_fiado(tmp_path):
    fiado = _armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan", limite=100000)
    _, ventas, _ = _armar_ventas(tmp_path, fiado)
    ventas.agregar_producto("1001")
    hoy = date.today()
    comprobante = ventas.cobrar(hoy, cliente=cliente.identificador, pagos=(
        PagoVenta(METODO_EFECTIVO, 6900),
        PagoVenta(METODO_FIADO, 6000),
    ))
    ventas.anular(comprobante.identificador, hoy)
    assert fiado.saldo("1") == 0


def test_el_resumen_de_medios_suma_por_pago():
    resumen = ResumenMedios()
    resumen.sumar(_venta_registrada((
        PagoVenta(METODO_EFECTIVO, 60, recibido=100),
        PagoVenta(METODO_MP, 90, datos="p-1"),
    )))
    assert resumen.efectivo == 60
    assert resumen.de(METODO_MP) == 90
    assert resumen.total() == 150


def test_el_resumen_de_medios_mantiene_el_legado():
    resumen = ResumenMedios()
    resumen.sumar(VentaRegistrada(
        HOY, "10:15:00", 100.0, _detalle(),
        monto_recibido=130, medio_pago=METODO_EFECTIVO))
    assert resumen.efectivo == 100
    resumen.sumar(VentaRegistrada(HOY, "11:00:00", 70.0, _detalle()))
    assert resumen.de("sin_registrar") == 70
    assert resumen.total() == 170
