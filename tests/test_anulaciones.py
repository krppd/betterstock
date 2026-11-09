from __future__ import annotations

import sqlite3
from datetime import date, timedelta

import pytest
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtTest import QTest

from models.cierre import CierreRegistrado
from models.medio_pago import METODO_EFECTIVO
from models.movimiento import MovimientoEntrada
from models.producto import Producto
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cierre_repositorio import CierreRepositorio
from repositories.codigo_repositorio import CodigoRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.excepciones import ErrorValidacion
from services.gestor_anulaciones import GestorAnulaciones
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from services.plazo_anulacion import MENSAJE_DIA_CERRADO, MENSAJE_PLAZO
from views.dialogo_anulacion import DialogoAnulacion
from views.ventana_detalle_venta import VentanaDetalleVenta

PRECIO = 10000.0
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
    base = tmp_path / "anulaciones.db"
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
    cierres = CierreRepositorio(base)
    cierres.inicializar()
    ventas = GestorVentas(stock, estadisticas, None, cierres)
    codigos = CodigoRepositorio(base)
    codigos.inicializar()
    anulaciones = GestorAnulaciones(ventas, codigos)
    return base, stock, ventas, estadisticas, codigos, anulaciones


def _vender(ventas: GestorVentas, dia: date):
    ventas.agregar_producto("1001")
    return ventas.cobrar(dia, monto_recibido=PRECIO, medio_pago=METODO_EFECTIVO)


def _cerrar_dia(cierres: CierreRepositorio, dia: date) -> None:
    cierres.agregar(CierreRegistrado(
        dia, "23:00:00", 1, PRECIO, PRECIO, PRECIO, 0.0, 0.0, 0.0))


def test_el_codigo_generado_verifica_y_el_otro_no(tmp_path):
    _, _, _, _, codigos, _ = _armar(tmp_path)

    modelo, codigo = codigos.generar("Ana")

    assert len(codigo) == 10
    assert codigo.isdigit()
    assert modelo.verificar(codigo)
    assert not modelo.verificar(CODIGO_MALO)
    assert not modelo.verificar("")


def test_el_codigo_guardado_no_es_el_codigo_en_claro(tmp_path):
    base, _, _, _, codigos, _ = _armar(tmp_path)

    _, codigo = codigos.generar("Ana")

    conexion = sqlite3.connect(str(base))
    filas = conexion.execute(
        "SELECT hash_codigo, salt FROM codigos_anulacion").fetchall()
    conexion.close()
    assert len(filas) == 1
    hash_codigo, salt = filas[0]
    assert hash_codigo != codigo
    assert codigo not in hash_codigo
    assert len(salt) == 32


def test_un_codigo_revocado_no_verifica(tmp_path):
    _, _, _, _, codigos, _ = _armar(tmp_path)

    modelo, codigo = codigos.generar("Ana")
    assert codigos.buscar_activo_por_codigo(codigo) is not None

    assert codigos.revocar(modelo.identificador)

    revocado = codigos.listar()[0]
    assert revocado.activo is False
    assert not revocado.verificar(codigo)
    assert codigos.buscar_activo_por_codigo(codigo) is None


def test_el_codigo_de_otro_no_encuentra(tmp_path):
    _, _, _, _, codigos, _ = _armar(tmp_path)

    codigos.generar("Ana")

    assert codigos.buscar_activo_por_codigo(CODIGO_MALO) is None


def test_anular_con_codigo_valido_devuelve_la_etiqueta(tmp_path):
    _, stock, ventas, _, _, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")

    etiqueta = anulaciones.anular_con_codigo(
        comprobante.identificador, hoy, codigo, "Se cobró mal")

    assert etiqueta == "Supervisor Ana"
    assert stock.buscar_producto("1001").stock_actual == 10
    assert VentaRepositorio(tmp_path / "anulaciones.db").buscar(
        comprobante.identificador).anulada


def test_anular_con_codigo_invalido_falla(tmp_path):
    _, _, ventas, _, _, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")

    with pytest.raises(ErrorValidacion) as error:
        anulaciones.anular_con_codigo(
            comprobante.identificador, hoy, CODIGO_MALO, "Se cobró mal")

    assert str(error.value) == "El código no es válido."
    assert not VentaRepositorio(tmp_path / "anulaciones.db").buscar(
        comprobante.identificador).anulada


def test_anular_sin_motivo_falla(tmp_path):
    _, _, ventas, _, _, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")

    with pytest.raises(ErrorValidacion) as error:
        anulaciones.anular_con_codigo(comprobante.identificador, hoy, codigo, "   ")

    assert str(error.value) == "Escribí el motivo de la anulación."


def test_anular_con_codigo_revocado_falla(tmp_path):
    _, _, ventas, _, codigos, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    modelo, codigo = anulaciones.generar_codigo("Supervisor Ana")
    codigos.revocar(modelo.identificador)

    with pytest.raises(ErrorValidacion) as error:
        anulaciones.anular_con_codigo(
            comprobante.identificador, hoy, codigo, "Se cobró mal")

    assert str(error.value) == "El código no es válido."


def test_una_venta_de_ayer_no_se_puede_anular(tmp_path):
    _, stock, ventas, _, _, anulaciones = _armar(tmp_path)
    ayer = date.today() - timedelta(days=1)
    comprobante = _vender(ventas, ayer)
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")

    with pytest.raises(ErrorValidacion) as error:
        anulaciones.anular_con_codigo(
            comprobante.identificador, date.today(), codigo, "Se cobró mal")

    assert str(error.value) == MENSAJE_PLAZO
    assert "pasaron más de 24 horas" in str(error.value)
    assert stock.buscar_producto("1001").stock_actual == 9


def test_una_venta_de_un_dia_cerrado_no_se_puede_anular(tmp_path):
    base, stock, ventas, _, _, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")
    _cerrar_dia(CierreRepositorio(base), hoy)

    with pytest.raises(ErrorValidacion) as error:
        anulaciones.anular_con_codigo(
            comprobante.identificador, hoy, codigo, "Se cobró mal")

    assert str(error.value) == MENSAJE_DIA_CERRADO
    assert "el día está cerrado" in str(error.value)
    assert stock.buscar_producto("1001").stock_actual == 9


def test_el_movimiento_de_reversa_lleva_el_motivo(tmp_path):
    _, stock, ventas, _, _, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")

    anulaciones.anular_con_codigo(
        comprobante.identificador, hoy, codigo, "El cliente devolvió la mercadería")

    movimientos = stock.listar_movimientos_recientes()
    reversa = movimientos[0]
    assert reversa.tipo == MovimientoEntrada.TIPO
    assert reversa.codigo_producto == "1001"
    assert reversa.cantidad == 1
    assert "El cliente devolvió la mercadería" in reversa.motivo


def test_la_venta_anulada_no_cuenta_en_las_estadisticas(tmp_path):
    _, _, ventas, estadisticas, _, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    assert estadisticas.resumen(hoy, hoy).cantidad_ventas == 1
    assert estadisticas.resumen(hoy, hoy).total == PRECIO
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")

    anulaciones.anular_con_codigo(
        comprobante.identificador, hoy, codigo, "Se cobró mal")

    resumen = estadisticas.resumen(hoy, hoy)
    assert resumen.cantidad_ventas == 0
    assert resumen.total == 0
    assert len(estadisticas.ventas_del_periodo(hoy, hoy)) == 1
    assert estadisticas.ventas_del_periodo(hoy, hoy)[0].anulada


def test_el_boton_sabe_por_que_no_se_puede_anular(tmp_path):
    _, _, ventas, _, _, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)

    assert anulaciones.motivo_bloqueo(comprobante) == ""

    ventas.nueva_venta()
    _vender(ventas, hoy - timedelta(days=1))
    ayer = VentaRepositorio(tmp_path / "anulaciones.db").listar()[-1]
    assert anulaciones.motivo_bloqueo(ayer) == MENSAJE_PLAZO


def test_el_boton_de_anular_esta_habilitado_para_una_venta_de_hoy(tmp_path, aplicacion):
    _, _, ventas, _, _, anulaciones = _armar(tmp_path)
    comprobante = _vender(ventas, date.today())

    ventana = VentanaDetalleVenta(comprobante, None, anulaciones)

    assert ventana.ui.btnAnular.isEnabled()
    assert "código del supervisor" in ventana.ui.btnAnular.toolTip()
    _destruir(ventana)


def test_el_boton_de_anular_esta_deshabilitado_si_el_dia_esta_cerrado(tmp_path, aplicacion):
    base, _, ventas, _, _, anulaciones = _armar(tmp_path)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    _cerrar_dia(CierreRepositorio(base), hoy)

    ventana = VentanaDetalleVenta(comprobante, None, anulaciones)

    assert not ventana.ui.btnAnular.isEnabled()
    assert ventana.ui.btnAnular.toolTip() == MENSAJE_DIA_CERRADO
    _destruir(ventana)


def test_el_boton_de_anular_esta_deshabilitado_si_pasaron_las_24_horas(tmp_path, aplicacion):
    _, _, ventas, _, _, anulaciones = _armar(tmp_path)
    comprobante = _vender(ventas, date.today() - timedelta(days=1))

    ventana = VentanaDetalleVenta(comprobante, None, anulaciones)

    assert not ventana.ui.btnAnular.isEnabled()
    assert ventana.ui.btnAnular.toolTip() == MENSAJE_PLAZO
    _destruir(ventana)


def test_el_dialogo_acepta_con_el_enter_del_lector(tmp_path, aplicacion):
    _, _, _, _, _, anulaciones = _armar(tmp_path)
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")
    dialogo = DialogoAnulacion(None, "Venta de prueba",
                               validar_codigo=anulaciones.codigo_valido)
    dialogo.txtCodigo.setText(codigo)
    dialogo.txtMotivo.setPlainText("Se cobró mal")

    QTest.keyClick(dialogo.txtCodigo, Qt.Key.Key_Return)

    assert dialogo.result() == QDialog.DialogCode.Accepted
    assert dialogo.resultado == (codigo, "Se cobró mal")
    _destruir(dialogo)


def test_el_dialogo_no_acepta_un_codigo_invalido(tmp_path, aplicacion):
    _, _, _, _, _, anulaciones = _armar(tmp_path)
    anulaciones.generar_codigo("Supervisor Ana")
    dialogo = DialogoAnulacion(None, "Venta de prueba",
                               validar_codigo=anulaciones.codigo_valido)
    dialogo.txtCodigo.setText(CODIGO_MALO)
    dialogo.txtMotivo.setPlainText("Se cobró mal")
    dialogo.mostrar_advertencia = lambda *args: None

    dialogo.aceptar()

    assert dialogo.result() != QDialog.DialogCode.Accepted
    _destruir(dialogo)


def test_al_anular_avisa_con_el_identificador(tmp_path):
    _, _, ventas, _, codigos, _ = _armar(tmp_path)
    avisos: list[str] = []
    anulaciones = GestorAnulaciones(
        ventas, codigos, al_anular=avisos.append)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")

    anulaciones.anular_con_codigo(
        comprobante.identificador, hoy, codigo, "Se cobró mal")

    assert avisos == [comprobante.identificador]


def test_un_error_al_avisar_no_frena_la_anulacion(tmp_path):
    _, _, ventas, _, codigos, _ = _armar(tmp_path)

    def falla(_identificador: str) -> None:
        raise RuntimeError("ARCA no responde")

    anulaciones = GestorAnulaciones(ventas, codigos, al_anular=falla)
    hoy = date.today()
    comprobante = _vender(ventas, hoy)
    _, codigo = anulaciones.generar_codigo("Supervisor Ana")

    anulaciones.anular_con_codigo(
        comprobante.identificador, hoy, codigo, "Se cobró mal")
