from __future__ import annotations

import sqlite3
from datetime import date

import pytest
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QApplication, QDialog, QLabel
from PyQt6.QtTest import QTest

from models.medio_pago import METODO_DEBITO, METODO_EFECTIVO, METODO_FIADO
from models.movimiento import MOTIVO_DEVOLUCION_PREFIJO
from models.producto import Producto
from models.venta_registrada import PagoVenta
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cierre_repositorio import CierreRepositorio
from repositories.codigo_repositorio import CodigoRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.sqlite import conectar, ruta_db
from repositories.turno_repositorio import TurnoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.cierre_caja import ServicioCierre
from services.devoluciones import (
    ServicioDevoluciones,
    registrar_con_codigo,
    registrar_devolucion,
)
from services.estadisticas_ventas import EstadisticasVentas
from services.excepciones import ErrorValidacion
from services.gestor_anulaciones import GestorAnulaciones
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from services.turnos import ServicioTurnos
from views.dialogo_cerrar_caja import DialogoCerrarCaja
from views.dialogo_devolucion import DialogoDevolucion
from views.dialogo_turno import DialogoCerrarTurno
from views.ventana_detalle_venta import VentanaDetalleVenta
from views.ventana_movimientos import VentanaMovimientos

PRECIO_MARTILLO = 10000.0
PRECIO_CLAVOS = 2000.0
CODIGO_MALO = "0000000000"


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def _destruir(ventana) -> None:
    ventana.close()
    ventana.deleteLater()
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _armar(tmp_path):
    base = tmp_path / "test_devoluciones.db"
    conectar(base).close()
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base),
    )
    stock.inicializar()
    stock.guardar_producto(
        Producto(
            codigo="1001",
            nombre="Martillo",
            precio_costo=8500,
            precio_venta=PRECIO_MARTILLO,
            stock_actual=10,
            stock_minimo=2,
        )
    )
    stock.guardar_producto(
        Producto(
            codigo="1002",
            nombre="Clavos",
            precio_costo=1000,
            precio_venta=PRECIO_CLAVOS,
            stock_actual=50,
            stock_minimo=5,
        )
    )
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    cierres = CierreRepositorio(base)
    cierres.inicializar()
    ventas = GestorVentas(stock, estadisticas, None, cierres)
    codigos = CodigoRepositorio(base)
    codigos.inicializar()
    anulaciones = GestorAnulaciones(ventas, codigos)
    return base, stock, ventas, estadisticas, codigos, anulaciones


def _armar_completo(tmp_path):
    base = tmp_path / "test_devoluciones_completo.db"
    conectar(base).close()
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base),
    )
    stock.inicializar()
    stock.guardar_producto(
        Producto(
            codigo="1001",
            nombre="Martillo",
            precio_costo=8500,
            precio_venta=PRECIO_MARTILLO,
            stock_actual=10,
            stock_minimo=2,
        )
    )
    stock.guardar_producto(
        Producto(
            codigo="1002",
            nombre="Clavos",
            precio_costo=1000,
            precio_venta=PRECIO_CLAVOS,
            stock_actual=50,
            stock_minimo=5,
        )
    )
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    cierres = CierreRepositorio(base)
    cierres.inicializar()
    servicio_cierre = ServicioCierre(estadisticas, cierres)
    turnos = TurnoRepositorio(base)
    turnos.inicializar()
    cuenta = CuentaRepositorio(base)
    cuenta.inicializar()
    servicio_turnos = ServicioTurnos(turnos, VentaRepositorio(base), cuenta)
    ventas = GestorVentas(stock, estadisticas, None, cierres)
    codigos = CodigoRepositorio(base)
    codigos.inicializar()
    anulaciones = GestorAnulaciones(ventas, codigos)
    return (
        base,
        stock,
        ventas,
        estadisticas,
        codigos,
        anulaciones,
        servicio_cierre,
        servicio_turnos,
    )


def _vender_dos_items(ventas: GestorVentas, dia: date):
    ventas.agregar_producto("1001", 2)
    ventas.agregar_producto("1002", 5)
    return ventas.cobrar(dia, monto_recibido=30000.0, medio_pago=METODO_EFECTIVO)


def test_restituye_stock_de_los_items_correctos(tmp_path):
    base, stock, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())

    assert stock.buscar_producto("1001").stock_actual == 8
    assert stock.buscar_producto("1002").stock_actual == 45

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Cliente devolvió un martillo",
        base=base,
    )

    assert stock.buscar_producto("1001").stock_actual == 9
    assert stock.buscar_producto("1002").stock_actual == 45


def test_venta_original_intacta(tmp_path):
    base, _, ventas, estadisticas, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())
    total_original = comprobante.total
    detalle_original = comprobante.to_dict()["detalle"]

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Devolución parcial",
        base=base,
    )

    venta_despues = estadisticas.buscar(comprobante.identificador)
    assert not venta_despues.anulada
    assert venta_despues.estado == "activa"
    assert venta_despues.total == total_original
    assert venta_despues.to_dict()["detalle"] == detalle_original


def test_venta_anulada_no_permite_devolucion(tmp_path):
    base, _, ventas, _, codigos, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender_dos_items(ventas, hoy)
    _, codigo = codigos.generar("Supervisor")
    anulaciones.anular_con_codigo(comprobante.identificador, hoy, codigo, "Error de cobro")

    with pytest.raises(ErrorValidacion, match="anulada"):
        registrar_devolucion(
            comprobante.identificador,
            [{"codigo_producto": "1001", "cantidad": 1}],
            usuario="admin",
            motivo="Intento de devolución",
            base=base,
        )


def test_articulo_no_vendido_no_permite(tmp_path):
    base, stock, ventas, _, _, _ = _armar(tmp_path)
    stock.guardar_producto(
        Producto(
            codigo="9999",
            nombre="Destornillador",
            precio_costo=500,
            precio_venta=1000,
            stock_actual=10,
        )
    )
    comprobante = _vender_dos_items(ventas, date.today())

    with pytest.raises(ErrorValidacion, match="no pertenece"):
        registrar_devolucion(
            comprobante.identificador,
            [{"codigo_producto": "9999", "cantidad": 1}],
            usuario="admin",
            motivo="Producto ajeno a la venta",
            base=base,
        )


def test_cantidad_parcial_ok(tmp_path):
    base, stock, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())

    dev1 = registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Primera devolución",
        base=base,
    )
    assert stock.buscar_producto("1001").stock_actual == 9
    assert dev1.total == PRECIO_MARTILLO

    dev2 = registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Segunda devolución",
        base=base,
    )
    assert stock.buscar_producto("1001").stock_actual == 10
    assert dev2.total == PRECIO_MARTILLO


def test_no_permite_devolver_mas_de_lo_vendido(tmp_path):
    base, _, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())

    with pytest.raises(ErrorValidacion, match="más cantidad"):
        registrar_devolucion(
            comprobante.identificador,
            [{"codigo_producto": "1001", "cantidad": 3}],
            usuario="admin",
            motivo="Exceso de cantidad",
            base=base,
        )


def test_supervisor_requerido(tmp_path):
    base, _, ventas, _, codigos, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())
    _, codigo_valido = codigos.generar("Supervisor")

    with pytest.raises(ErrorValidacion, match="código no es válido"):
        registrar_con_codigo(
            comprobante.identificador,
            [{"codigo_producto": "1001", "cantidad": 1}],
            usuario="admin",
            motivo="Devolución con supervisor",
            codigo=CODIGO_MALO,
            base=base,
            codigos=codigos,
        )

    dev = registrar_con_codigo(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Devolución con supervisor",
        codigo=codigo_valido,
        base=base,
        codigos=codigos,
    )
    assert dev.id is not None


def test_motivo_obligatorio(tmp_path):
    base, _, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())

    with pytest.raises(ErrorValidacion, match="motivo"):
        registrar_devolucion(
            comprobante.identificador,
            [{"codigo_producto": "1001", "cantidad": 1}],
            usuario="admin",
            motivo="",
            base=base,
        )


def test_movimiento_de_entrada_registrado_con_motivo(tmp_path):
    base, _, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Falla de fábrica",
        base=base,
    )

    movimientos = MovimientoRepositorio(base).listar()
    movimientos_devolucion = [
        m
        for m in movimientos
        if m.motivo.startswith(f"Devolución venta {comprobante.identificador}")
    ]
    assert len(movimientos_devolucion) == 1
    mov = movimientos_devolucion[0]
    assert mov.tipo == "Entrada"
    assert mov.codigo_producto == "1001"
    assert mov.cantidad == 1
    assert "Falla de fábrica" in mov.motivo


def test_transaccion_atomica_rollback_si_falla(tmp_path):
    base, stock, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())

    with pytest.raises(ErrorValidacion):
        registrar_devolucion(
            comprobante.identificador,
            [
                {"codigo_producto": "1001", "cantidad": 1},
                {"codigo_producto": "1002", "cantidad": 99},
            ],
            usuario="admin",
            motivo="Prueba atomica",
            base=base,
        )

    assert stock.buscar_producto("1001").stock_actual == 8
    assert stock.buscar_producto("1002").stock_actual == 45

    con = conectar(base)
    filas = con.execute("SELECT COUNT(*) as c FROM devoluciones").fetchone()
    assert filas["c"] == 0
    con.close()


def test_dialogo_devolucion_parcial(tmp_path, aplicacion):
    base, _, ventas, _, codigos, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())
    _, codigo_valido = codigos.generar("Supervisor")

    dialogo = DialogoDevolucion(
        None,
        comprobante,
        validar_codigo=codigos.buscar_activo_por_codigo,
        base=base,
    )

    dialogo.mostrar_advertencia = lambda *args: None
    dialogo.aceptar()
    assert dialogo.result() != QDialog.DialogCode.Accepted

    spinbox = dialogo.spinboxes["1001"]
    spinbox.setValue(1.0)
    assert dialogo.total_devolucion == PRECIO_MARTILLO

    dialogo.txtCodigo.setText(codigo_valido)
    dialogo.txtMotivo.setText("Defectuoso")
    dialogo.aceptar()

    assert dialogo.result() == QDialog.DialogCode.Accepted
    items = dialogo.items_a_devolver
    assert len(items) == 1
    assert items[0]["codigo_producto"] == "1001"
    assert items[0]["cantidad"] == 1.0
    _destruir(dialogo)


def test_boton_devolucion_en_ventana_detalle_venta(tmp_path, aplicacion):
    base, _, ventas, _, codigos, anulaciones = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())

    ventana = VentanaDetalleVenta(comprobante, None, anulaciones)
    assert hasattr(ventana.ui, "btnDevolucion")
    assert ventana.ui.btnDevolucion.isEnabled()
    _destruir(ventana)

    _, codigo_valido = codigos.generar("Supervisor")
    anulaciones.anular_con_codigo(comprobante.identificador, date.today(), codigo_valido, "Anulada")
    comprobante.anular()

    ventana_anulada = VentanaDetalleVenta(comprobante, None, anulaciones)
    assert not ventana_anulada.ui.btnDevolucion.isEnabled()
    _destruir(ventana_anulada)


def test_movimientos_de_devolucion_usa_prefijo_conocido(tmp_path):
    base, _, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="cliente arrepentido",
        base=base,
    )
    movs = MovimientoRepositorio(base).listar()
    mov_dev = [m for m in movs if m.codigo_producto == "1001" and m.tipo == "Entrada"]
    assert len(mov_dev) == 1
    assert mov_dev[0].motivo.startswith(MOTIVO_DEVOLUCION_PREFIJO)
    assert (
        f"Devolución venta {comprobante.identificador}: cliente arrepentido"
        == mov_dev[0].motivo
    )


def test_cmb_historial_muestra_devolucion_como_categoria(tmp_path, aplicacion):
    base, stock, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="cambio de talle",
        base=base,
    )
    ventana = VentanaMovimientos(stock)
    assert ventana.cmbMotivo.count() >= 2
    assert ventana.cmbMotivo.itemText(1) == MOTIVO_DEVOLUCION_PREFIJO
    assert ventana.cmbMotivo.itemData(1) == MOTIVO_DEVOLUCION_PREFIJO
    _destruir(ventana)


def test_filtro_cmb_devolucion_muestra_solo_devoluciones(tmp_path, aplicacion):
    base, stock, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())
    stock.registrar_ajuste("1001", 15, date.today(), motivo="Ajuste anual")
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="falla de fábrica",
        base=base,
    )
    ventana = VentanaMovimientos(stock)
    idx = ventana.cmbMotivo.findData(MOTIVO_DEVOLUCION_PREFIJO)
    assert idx > 0
    ventana.cmbMotivo.setCurrentIndex(idx)
    filas = [
        ventana.ui.tblHistorial.item(r, 4).text()
        for r in range(ventana.ui.tblHistorial.rowCount())
    ]
    assert len(filas) == 1
    assert filas[0].startswith(MOTIVO_DEVOLUCION_PREFIJO)
    _destruir(ventana)


def test_no_entra_en_el_filtro_todos_escondida_aparece_con_el_prefijo(
    tmp_path, aplicacion
):
    base, stock, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="producto roto",
        base=base,
    )
    ventana = VentanaMovimientos(stock)
    ventana.cmbMotivo.setCurrentIndex(0)
    filas = [
        ventana.ui.tblHistorial.item(r, 4).text()
        for r in range(ventana.ui.tblHistorial.rowCount())
    ]
    assert any(f.startswith(MOTIVO_DEVOLUCION_PREFIJO) for f in filas)
    _destruir(ventana)


def test_motivos_de_movimientos_no_duplica_devoluciones_individuales(tmp_path):
    base, stock, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="devolucion 1",
        base=base,
    )
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1002", "cantidad": 1}],
        usuario="admin",
        motivo="devolucion 2",
        base=base,
    )
    motivos = stock.motivos_de_movimientos()
    assert not any(m.startswith(MOTIVO_DEVOLUCION_PREFIJO) for m in motivos)


def test_estadisticas_resta_devoluciones_del_total_del_periodo(tmp_path):
    base, _, ventas, estadisticas, _, _ = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender_dos_items(ventas, hoy)
    res_antes = estadisticas.resumen(hoy, hoy)
    assert res_antes.total == 30000.0

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Cliente arrepentido",
        base=base,
    )

    res_despues = estadisticas.resumen(hoy, hoy)
    assert res_despues.total == 20000.0
    assert res_despues.devoluciones_total == 10000.0


def test_estadisticas_resta_unidades_devueltas_por_producto(tmp_path):
    base, _, ventas, estadisticas, _, _ = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender_dos_items(ventas, hoy)

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Devolucion parcial",
        base=base,
    )

    res = estadisticas.resumen(hoy, hoy)
    assert res.unidades == 6.0

    mas_vendidos = {p.codigo: p for p in estadisticas.mas_vendidos(hoy, hoy)}
    assert mas_vendidos["1001"].unidades == 1.0
    assert mas_vendidos["1001"].total == 10000.0


def test_estadisticas_total_por_dia_descuenta_devolucion(tmp_path):
    base, _, ventas, estadisticas, _, _ = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender_dos_items(ventas, hoy)

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Devolución",
        base=base,
    )

    por_dia = dict(estadisticas.total_por_dia(hoy, hoy))
    assert por_dia[hoy] == 20000.0


def test_arqueo_cierre_resta_devolucion_si_fue_efectivo(tmp_path):
    base, _, ventas, _, _, _, servicio_cierre, _ = _armar_completo(tmp_path)
    hoy = date.today()
    comprobante = _vender_dos_items(ventas, hoy)

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Devolución en efectivo",
        base=base,
    )

    cierre = servicio_cierre.arqueo(hoy)
    assert cierre.devoluciones_total == 10000.0
    assert cierre.efectivo_esperado == 20000.0
    assert cierre.esperado == 20000.0


def test_arqueo_cierre_no_toca_efectivo_si_fue_tarjeta_o_fiado(tmp_path):
    base, _, ventas, _, _, _, servicio_cierre, _ = _armar_completo(tmp_path)
    hoy = date.today()
    ventas.agregar_producto("1001", 2)
    comprobante = ventas.cobrar(hoy, monto_recibido=20000.0, medio_pago=METODO_DEBITO)

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Devolución débito",
        base=base,
    )

    cierre = servicio_cierre.arqueo(hoy)
    assert cierre.devoluciones_total == 10000.0
    assert cierre.efectivo_esperado == 0.0


def test_arqueo_turno_resta_devolucion_si_fue_efectivo(tmp_path):
    base, _, ventas, _, _, _, _, servicio_turnos = _armar_completo(tmp_path)
    hoy = date.today()
    servicio_turnos.abrir(5000.0, "cajero")
    comprobante = _vender_dos_items(ventas, hoy)

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="cajero",
        motivo="Devolución turno efectivo",
        base=base,
    )

    arqueo = servicio_turnos.arqueo()
    assert arqueo.devoluciones_total == 10000.0
    assert arqueo.efectivo_ventas == 20000.0
    assert arqueo.efectivo_esperado == 25000.0
    assert arqueo.total_esperado == 25000.0


def test_arqueo_turno_no_toca_efectivo_si_fue_tarjeta_o_fiado(tmp_path):
    base, _, ventas, _, _, _, _, servicio_turnos = _armar_completo(tmp_path)
    hoy = date.today()
    servicio_turnos.abrir(5000.0, "cajero")
    ventas.agregar_producto("1001", 2)
    comprobante = ventas.cobrar(hoy, monto_recibido=20000.0, medio_pago=METODO_DEBITO)

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="cajero",
        motivo="Devolución turno débito",
        base=base,
    )

    arqueo = servicio_turnos.arqueo()
    assert arqueo.devoluciones_total == 10000.0
    assert arqueo.efectivo_ventas == 0.0
    assert arqueo.efectivo_esperado == 5000.0


def test_devolucion_venta_original_intacta_y_stock_restituido(tmp_path):
    base, stock, ventas, estadisticas, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())
    assert stock.buscar_producto("1001").stock_actual == 8

    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1001", "cantidad": 1}],
        usuario="admin",
        motivo="Verificar integridad",
        base=base,
    )

    assert stock.buscar_producto("1001").stock_actual == 9
    v_check = estadisticas.buscar(comprobante.identificador)
    assert v_check.estado == "activa"
    assert v_check.total == 30000.0


def test_rollback_si_la_devolucion_falla_a_mitad(tmp_path):
    base, stock, ventas, _, _, _ = _armar(tmp_path)
    comprobante = _vender_dos_items(ventas, date.today())

    with pytest.raises(ErrorValidacion):
        registrar_devolucion(
            comprobante.identificador,
            [
                {"codigo_producto": "1001", "cantidad": 1},
                {"codigo_producto": "9999", "cantidad": 1},
            ],
            usuario="admin",
            motivo="Fallo a mitad",
            base=base,
        )

    assert stock.buscar_producto("1001").stock_actual == 8
    con = conectar(base)
    c = con.execute("SELECT COUNT(*) as c FROM devoluciones").fetchone()["c"]
    con.close()
    assert c == 0


def test_arqueo_mixto_descuenta_solo_efectivo(tmp_path):
    base, _, ventas, _, _, _, servicio_cierre, _ = _armar_completo(tmp_path)
    hoy = date.today()
    ventas.agregar_producto("1002", 5)
    comprobante = ventas.cobrar(
        hoy,
        pagos=(
            PagoVenta(METODO_EFECTIVO, 4000.0),
            PagoVenta(METODO_DEBITO, 6000.0),
        ),
    )
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1002", "cantidad": 1}],
        usuario="admin",
        motivo="Devolución parcial 2k",
        base=base,
    )
    cierre = servicio_cierre.arqueo(hoy)
    assert cierre.devoluciones_total == 2000.0
    assert cierre.efectivo_esperado == 2000.0


def test_arqueo_mixto_cap_al_efectivo_pagado(tmp_path):
    base, _, ventas, _, _, _, servicio_cierre, _ = _armar_completo(tmp_path)
    hoy = date.today()
    ventas.agregar_producto("1002", 5)
    comprobante = ventas.cobrar(
        hoy,
        pagos=(
            PagoVenta(METODO_EFECTIVO, 4000.0),
            PagoVenta(METODO_DEBITO, 6000.0),
        ),
    )
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1002", "cantidad": 4}],
        usuario="admin",
        motivo="Devolución parcial 8k",
        base=base,
    )
    cierre = servicio_cierre.arqueo(hoy)
    assert cierre.devoluciones_total == 8000.0
    assert cierre.efectivo_esperado == 0.0


def test_arqueo_tarjeta_no_afecta_cajon(tmp_path):
    base, _, ventas, _, _, _, servicio_cierre, _ = _armar_completo(tmp_path)
    hoy = date.today()
    ventas.agregar_producto("1002", 5)
    comprobante = ventas.cobrar(hoy, monto_recibido=10000.0, medio_pago=METODO_DEBITO)
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1002", "cantidad": 2}],
        usuario="admin",
        motivo="Devolución débito",
        base=base,
    )
    cierre = servicio_cierre.arqueo(hoy)
    assert cierre.devoluciones_total == 4000.0
    assert cierre.efectivo_esperado == 0.0


def test_arqueo_control_mismo_comportamiento_turno(tmp_path):
    base, _, ventas, _, _, _, _, servicio_turnos = _armar_completo(tmp_path)
    hoy = date.today()
    servicio_turnos.abrir(5000.0, "cajero")
    ventas.agregar_producto("1002", 5)
    comprobante = ventas.cobrar(hoy, monto_recibido=10000.0, medio_pago=METODO_DEBITO)
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1002", "cantidad": 2}],
        usuario="cajero",
        motivo="Devolución débito turno",
        base=base,
    )
    arqueo = servicio_turnos.arqueo()
    assert arqueo.devoluciones_total == 4000.0
    assert arqueo.efectivo_esperado == 5000.0


def test_arqueo_turno_mixto_descuenta_solo_efectivo(tmp_path):
    base, _, ventas, _, _, _, _, servicio_turnos = _armar_completo(tmp_path)
    hoy = date.today()
    servicio_turnos.abrir(5000.0, "cajero")
    ventas.agregar_producto("1002", 5)
    comprobante = ventas.cobrar(
        hoy,
        pagos=(
            PagoVenta(METODO_EFECTIVO, 4000.0),
            PagoVenta(METODO_DEBITO, 6000.0),
        ),
    )
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1002", "cantidad": 1}],
        usuario="cajero",
        motivo="Devolución 2k turno",
        base=base,
    )
    arqueo = servicio_turnos.arqueo()
    assert arqueo.devoluciones_total == 2000.0
    assert arqueo.efectivo_ventas == 2000.0
    assert arqueo.efectivo_esperado == 7000.0


def test_arqueo_turno_mixto_cap_al_efectivo_pagado(tmp_path):
    base, _, ventas, _, _, _, _, servicio_turnos = _armar_completo(tmp_path)
    hoy = date.today()
    servicio_turnos.abrir(5000.0, "cajero")
    ventas.agregar_producto("1002", 5)
    comprobante = ventas.cobrar(
        hoy,
        pagos=(
            PagoVenta(METODO_EFECTIVO, 4000.0),
            PagoVenta(METODO_DEBITO, 6000.0),
        ),
    )
    registrar_devolucion(
        comprobante.identificador,
        [{"codigo_producto": "1002", "cantidad": 4}],
        usuario="cajero",
        motivo="Devolución 8k turno",
        base=base,
    )
    arqueo = servicio_turnos.arqueo()
    assert arqueo.devoluciones_total == 8000.0
    assert arqueo.efectivo_ventas == 0.0
    assert arqueo.efectivo_esperado == 5000.0


def test_dialogo_cierre_muestra_devoluciones_si_existen(aplicacion):
    dlg_con_dev = DialogoCerrarCaja(declarado=100.0, esperado=100.0, devoluciones_total=500.0)
    textos = [lbl.text() for lbl in dlg_con_dev.findChildren(QLabel)]
    assert any("Devoluciones del día:" in t for t in textos)
    assert any("$ 500,00" in t for t in textos)

    dlg_sin_dev = DialogoCerrarCaja(declarado=100.0, esperado=100.0, devoluciones_total=0.0)
    textos_sin = [lbl.text() for lbl in dlg_sin_dev.findChildren(QLabel)]
    assert not any("Devoluciones del día:" in t for t in textos_sin)


def test_dialogo_cierre_turno_muestra_devoluciones_si_existen(aplicacion):
    dlg_con_dev = DialogoCerrarTurno(
        efectivo_esperado=1000.0, fondo_inicial=500.0, efectivo_ventas=500.0,
        devoluciones_total=250.0,
    )
    textos = [lbl.text() for lbl in dlg_con_dev.findChildren(QLabel)]
    assert any("Devoluciones del día: $ 250,00" in t for t in textos)

    dlg_sin_dev = DialogoCerrarTurno(
        efectivo_esperado=1000.0, fondo_inicial=500.0, efectivo_ventas=500.0,
        devoluciones_total=0.0,
    )
    textos_sin = [lbl.text() for lbl in dlg_sin_dev.findChildren(QLabel)]
    assert not any("Devoluciones del día" in t for t in textos_sin)


def test_error_lectura_devoluciones_registra_warning_y_no_explota(tmp_path, caplog, monkeypatch):
    base, _, _, _, _, _, servicio_cierre, servicio_turnos = _armar_completo(tmp_path)
    servicio_turnos.abrir(1000.0, "cajero")

    def _conectar_roto(*args, **kwargs):
        raise sqlite3.OperationalError("error de lectura simulado")

    monkeypatch.setattr("services.cierre_caja.conectar", _conectar_roto)
    monkeypatch.setattr("services.turnos.conectar", _conectar_roto)

    with caplog.at_level("WARNING"):
        cierre = servicio_cierre.arqueo(date.today())
        assert cierre.devoluciones_total == 0.0
        assert "No se pudieron leer las devoluciones para el arqueo" in caplog.text

    caplog.clear()
    with caplog.at_level("WARNING"):
        arqueo = servicio_turnos.arqueo()
        assert arqueo.devoluciones_total == 0.0
        assert "No se pudieron leer las devoluciones para el arqueo de turno" in caplog.text

