from __future__ import annotations

from datetime import date

import pytest
from PyQt6.QtWidgets import QApplication, QDialog

from models.medio_pago import (
    METODO_DEBITO,
    METODO_EFECTIVO,
    METODO_FIADO,
    METODO_MIXTO,
)
from models.producto import Producto
from models.venta import Venta
from models.venta_registrada import PagoVenta, RenglonVenta, VentaRegistrada
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cliente_repositorio import ClienteRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from services.ticket import _lineas_ticket
from views.ventana_cobro import VentanaCobro
from views.ventana_detalle_venta import VentanaDetalleVenta

HOY = date(2026, 10, 25)
TOTAL = 3000.0


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def _armar(tmp_path, limite=1_000_000.0):
    stock = GestorStock(
        ProductoRepositorio(tmp_path / "productos.csv"),
        MovimientoRepositorio(tmp_path / "movimientos.csv"),
        CategoriaRepositorio(tmp_path / "categorias.csv"))
    stock.inicializar()
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Martillo", precio_costo=600,
        precio_venta=1000, stock_actual=10, stock_minimo=2))
    fiado = GestorFiado(
        ClienteRepositorio(tmp_path / "clientes.csv"),
        CuentaRepositorio(tmp_path / "cuenta.csv"))
    fiado.inicializar()
    cliente = fiado.guardar_cliente("Juan", limite=limite)
    estadisticas = EstadisticasVentas(VentaRepositorio(tmp_path / "ventas.csv"))
    estadisticas.inicializar()
    ventas = GestorVentas(stock, estadisticas, fiado)
    for _ in range(3):
        ventas.agregar_producto("1001")
    return VentanaCobro(ventas.venta, fiado), cliente


def _elegir(cobro: VentanaCobro, metodo: str) -> None:
    cobro.ui.cmbMetodo.setCurrentIndex(cobro.ui.cmbMetodo.findData(metodo))


def _elegir_parcial(cobro: VentanaCobro, metodo: str) -> None:
    indice = cobro.ui.cmbMedioParcial.findData(metodo)
    cobro.ui.cmbMedioParcial.setCurrentIndex(indice)


def _en_modo_mixto(cobro: VentanaCobro) -> None:
    _elegir(cobro, METODO_MIXTO)


def _agregar(cobro: VentanaCobro, metodo: str, monto: float | None = None,
             datos: str = "") -> None:
    _elegir_parcial(cobro, metodo)
    if monto is not None:
        cobro.ui.spnMonto.setValue(monto)
    if datos:
        cobro.ui.txtDatos.setText(datos)
    cobro.agregar_pago()


def test_sin_pagos_y_sin_mixto_el_cobro_queda_como_hoy(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    assert cobro.metodo == METODO_EFECTIVO
    assert cobro.ui.cmbMetodo.currentData() != METODO_MIXTO
    assert cobro.ui.cmbMedioParcial.findData(METODO_MIXTO) == -1
    assert cobro.pagos == ()
    assert cobro.pendiente == TOTAL
    assert cobro.ui.spnMonto.value() == TOTAL
    assert cobro.ui.btnAgregar.text() == "Registrar dinero parcial"
    assert not cobro.ui.lblPagos.isVisibleTo(cobro)
    assert not cobro.ui.btnAgregar.isVisibleTo(cobro)
    assert not cobro.ui.btnQuitar.isVisibleTo(cobro)
    assert not cobro.ui.lblMedioParcial.isVisibleTo(cobro)
    assert not cobro.ui.cmbMedioParcial.isVisibleTo(cobro)
    assert not cobro.ui.btnQuitar.isEnabled()
    cobro.ui.spnMonto.setValue(TOTAL + 500)
    assert cobro.vuelto == 500
    cobro.aceptar()
    assert cobro.result() == QDialog.DialogCode.Accepted


def test_en_modo_mixto_se_muestra_el_panel_de_pagos(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    _en_modo_mixto(cobro)
    assert cobro.ui.lblMedioParcial.isVisibleTo(cobro)
    assert cobro.ui.cmbMedioParcial.isVisibleTo(cobro)
    assert cobro.ui.btnAgregar.isVisibleTo(cobro)
    assert cobro.ui.btnQuitar.isVisibleTo(cobro)
    assert cobro._medio_activo() == METODO_EFECTIVO
    _elegir_parcial(cobro, METODO_FIADO)
    assert cobro.ui.cmbCliente.isVisibleTo(cobro)
    assert cobro.ui.lblSaldo.isVisibleTo(cobro)


def test_en_modo_mixto_sin_parciales_cobrar_exige_registrar(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    _en_modo_mixto(cobro)
    avisos: list[tuple[str, str]] = []
    cobro.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))
    cobro.aceptar()
    assert len(avisos) == 1
    assert "pago parcial" in avisos[0][1]
    assert cobro.result() != QDialog.DialogCode.Accepted


def test_al_salir_de_mixto_con_pagos_revierte_la_seleccion(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    _en_modo_mixto(cobro)
    _agregar(cobro, METODO_EFECTIVO, monto=1000)
    avisos: list[tuple[str, str]] = []
    cobro.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))
    _elegir(cobro, METODO_DEBITO)
    assert len(avisos) == 1
    assert cobro.metodo == METODO_MIXTO
    assert len(cobro.pagos) == 1


def test_agregar_pagos_acumula_y_deja_pendiente_en_cero(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    _en_modo_mixto(cobro)
    _agregar(cobro, METODO_EFECTIVO, monto=1000)
    assert cobro.pagos[0].importe == 1000
    assert cobro.pendiente == 2000.0
    _agregar(cobro, METODO_DEBITO, datos="1234")
    assert cobro.pendiente == 0.0
    assert sum(pago.importe for pago in cobro.pagos) == TOTAL
    assert cobro.ui.lblPagos.isVisibleTo(cobro)
    assert "Sumados:" in cobro.ui.lblPagos.text()
    assert "Efectivo $ 1.000,00" in cobro.ui.lblPagos.text()
    assert "Débito — 1234 $ 2.000,00" in cobro.ui.lblPagos.text()
    assert "completo" in cobro.ui.lblPagos.text()


def test_quitar_pago_saca_el_ultimo(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    _en_modo_mixto(cobro)
    _agregar(cobro, METODO_EFECTIVO, monto=1000)
    _agregar(cobro, METODO_DEBITO, datos="1234")
    cobro.quitar_pago()
    assert [pago.medio for pago in cobro.pagos] == [METODO_EFECTIVO]
    assert cobro.pendiente == 2000.0
    assert "Débito" not in cobro.ui.lblPagos.text()


def test_el_pago_en_cero_no_se_agrega(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    _en_modo_mixto(cobro)
    avisos: list[tuple[str, str]] = []
    cobro.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))
    _agregar(cobro, METODO_EFECTIVO, monto=0)
    assert avisos and "Monto en cero" in avisos[0][0]
    assert cobro.pagos == ()


def test_el_vuelto_de_efectivo_sobrante_en_el_cierre(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    _en_modo_mixto(cobro)
    _agregar(cobro, METODO_EFECTIVO, monto=1000)
    cobro.ui.spnMonto.setValue(2100)
    cobro.aceptar()
    assert cobro.result() == QDialog.DialogCode.Accepted
    assert [pago.importe for pago in cobro.pagos] == [1000.0, 2000.0]
    assert cobro.pagos[1].recibido == 2100
    assert cobro.pagos[1].vuelto == 100


def test_el_cierre_en_efectivo_con_faltante_avisa_y_no_acepta(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    _en_modo_mixto(cobro)
    _agregar(cobro, METODO_EFECTIVO, monto=1000)
    cobro.ui.spnMonto.setValue(1500)
    avisos: list[tuple[str, str]] = []
    cobro.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))
    cobro.aceptar()
    assert len(avisos) == 1
    assert "Faltan" in avisos[0][1]
    assert cobro.result() != QDialog.DialogCode.Accepted
    assert len(cobro.pagos) == 1


def test_el_fiado_del_cierre_usa_el_cliente_elegido(tmp_path, aplicacion):
    cobro, cliente = _armar(tmp_path)
    _en_modo_mixto(cobro)
    _agregar(cobro, METODO_EFECTIVO, monto=1000)
    _elegir_parcial(cobro, METODO_FIADO)
    cobro.ui.cmbCliente.setCurrentIndex(cobro.ui.cmbCliente.findData(cliente.identificador))
    cobro.aceptar()
    assert cobro.result() == QDialog.DialogCode.Accepted
    assert cobro.cliente_fiado == cliente.identificador


def test_el_fiado_del_cierre_respeta_el_tope(tmp_path, aplicacion):
    cobro, cliente = _armar(tmp_path, limite=999)
    _en_modo_mixto(cobro)
    _agregar(cobro, METODO_EFECTIVO, monto=2000)
    _elegir_parcial(cobro, METODO_FIADO)
    cobro.ui.cmbCliente.setCurrentIndex(cobro.ui.cmbCliente.findData(cliente.identificador))
    avisos: list[tuple[str, str]] = []
    cobro.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))
    cobro.aceptar()
    assert len(avisos) == 1
    assert "límite" in avisos[0][1]
    assert cobro.result() != QDialog.DialogCode.Accepted
    assert len(cobro.pagos) == 1


def test_no_puede_haber_dos_pagos_fiados(tmp_path, aplicacion):
    cobro, _ = _armar(tmp_path)
    _en_modo_mixto(cobro)
    cobro._pagos.append(PagoVenta(METODO_FIADO, 1000))
    avisos: list[tuple[str, str]] = []
    cobro.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))
    _agregar(cobro, METODO_FIADO)
    assert avisos and "un pago fiado" in avisos[0][1]
    assert len(cobro.pagos) == 1


def test_la_venta_mixta_guarda_y_muestra_los_pagos(tmp_path, aplicacion):
    stock = GestorStock(
        ProductoRepositorio(tmp_path / "productos.csv"),
        MovimientoRepositorio(tmp_path / "movimientos.csv"),
        CategoriaRepositorio(tmp_path / "categorias.csv"))
    stock.inicializar()
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Martillo", precio_costo=600,
        precio_venta=1000, stock_actual=10, stock_minimo=2))
    estadisticas = EstadisticasVentas(VentaRepositorio(tmp_path / "ventas.csv"))
    estadisticas.inicializar()
    ventas = GestorVentas(stock, estadisticas)
    for _ in range(3):
        ventas.agregar_producto("1001")

    cobro = VentanaCobro(ventas.venta)
    _en_modo_mixto(cobro)
    _agregar(cobro, METODO_EFECTIVO, monto=1000)
    _agregar(cobro, METODO_DEBITO, datos="1234")
    comprobante = ventas.cobrar(HOY, pagos=cobro.pagos, usuario="cajero")

    assert comprobante.medio_pago == "mixto"
    assert comprobante.medio_pago_texto == "Efectivo + Débito — 1234"


def test_el_ticket_y_el_pdf_muestran_el_desglose_de_pagos(aplicacion):
    venta = Venta()
    producto = Producto(codigo="1001", nombre="Martillo", precio_venta=1000)
    venta.agregar_cantidad(producto, 3)
    lineas = _lineas_ticket(venta, None, monto_recibido=1000, vuelto=0,
                            identificador="2026-10-25 10:15:00",
                            medio="Efectivo + Débito — 1234")
    textos = [texto for texto, _ in lineas]
    assert any(texto.startswith("PAGO: Efectivo + Débito — 1234") for texto in textos)

    registrada = VentaRegistrada(
        HOY, "10:15:00", 3000.0,
        [RenglonVenta("1001", "Martillo", 3, 1000.0)],
        pagos=(PagoVenta(METODO_EFECTIVO, 1000),
               PagoVenta(METODO_DEBITO, 2000, datos="1234")))
    assert "Efectivo + Débito — 1234" in registrada.medio_pago_texto


def test_el_detalle_muestra_la_fila_de_medios_solo_en_mixto(aplicacion):
    venta = VentaRegistrada(
        HOY, "10:15:00", 3000.0,
        [RenglonVenta("1001", "Martillo", 3, 1000.0)],
        medio_pago=METODO_EFECTIVO, monto_recibido=3000)
    simple = VentanaDetalleVenta(venta)

    etiquetas = [simple.ui.tblDatos.item(fila, 0).text()
                 for fila in range(simple.ui.tblDatos.rowCount())]
    assert "Medios" not in etiquetas
    assert simple.ui.tblDatos.verticalHeader().defaultSectionSize() >= 34

    mixta = VentanaDetalleVenta(VentaRegistrada(
        HOY, "11:00:00", 3000.0,
        [RenglonVenta("1001", "Martillo", 3, 1000.0)],
        pagos=(PagoVenta(METODO_EFECTIVO, 1000),
               PagoVenta(METODO_DEBITO, 2000, datos="1234"))))
    filas = [(mixta.ui.tblDatos.item(fila, 0).text(),
              mixta.ui.tblDatos.item(fila, 1).text())
             for fila in range(mixta.ui.tblDatos.rowCount())]
    etiquetas_mixta = [clave for clave, _ in filas]
    assert "Medios" not in etiquetas_mixta
    assert "Recibido" not in etiquetas_mixta and "Vuelto" not in etiquetas_mixta
    medio_pago_mixto = dict(filas).get("Medio de pago")
    assert "Efectivo" in medio_pago_mixto and "Débito" in medio_pago_mixto
    assert "$ 1" in medio_pago_mixto and "$ 2" in medio_pago_mixto
    assert dict(filas).get("Referencia") == "1234"
    assert mixta.ui.tblDatos.verticalHeader().defaultSectionSize() >= 34
    assert mixta.ui.tblDatos.height() >= 34 * (mixta.ui.tblDatos.rowCount() + 1)
