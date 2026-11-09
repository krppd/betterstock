from __future__ import annotations

from datetime import date

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from models.producto import Producto
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from services.excepciones import ErrorValidacion
from services.gestor_stock import GestorStock
from services.recuento import ServicioRecuento, motivo_recuento
from ui.widgets.notificacion import Notificacion
from views.ventana_recuento import VentanaRecuento
from views.ventana_movimientos import VentanaMovimientos


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def _gestor(tmp_path) -> GestorStock:
    base = tmp_path / "recuento.db"
    gestor = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base))
    gestor.inicializar()
    for codigo, nombre, stock in (
        ("1001", "Tomate perita", 10),
        ("1002", "Papa blanca", 20),
        ("1003", "Leche entera", 5),
    ):
        gestor.guardar_producto(Producto(
            codigo=codigo, nombre=nombre, precio_costo=10.0,
            precio_venta=20.0, stock_actual=stock, stock_minimo=2))
    return gestor


def _cerrar(ventana: VentanaRecuento) -> None:
    ventana.close()
    ventana.deleteLater()


def test_aplica_solo_las_diferencias(tmp_path):
    gestor = _gestor(tmp_path)
    movimientos = ServicioRecuento(gestor).aplicar({"1001": 7, "1002": 20})
    assert len(movimientos) == 1
    assert movimientos[0].codigo_producto == "1001"
    assert movimientos[0].cantidad == 7
    assert gestor.buscar_producto("1001").stock_actual == 7
    assert gestor.buscar_producto("1002").stock_actual == 20


def test_permite_fijar_el_stock_en_cero(tmp_path):
    gestor = _gestor(tmp_path)
    movimientos = ServicioRecuento(gestor).aplicar({"1001": 0})
    assert len(movimientos) == 1
    assert movimientos[0].cantidad == 0
    assert gestor.buscar_producto("1001").stock_actual == 0


def test_no_toca_los_productos_que_coinciden(tmp_path):
    gestor = _gestor(tmp_path)
    movimientos = ServicioRecuento(gestor).aplicar({"1001": 10, "1002": 20})
    assert movimientos == []
    assert gestor.listar_movimientos_recientes() == []
    assert gestor.buscar_producto("1001").stock_actual == 10


def test_rechaza_conteos_negativos_sin_tocar_el_stock(tmp_path):
    gestor = _gestor(tmp_path)
    with pytest.raises(ErrorValidacion):
        ServicioRecuento(gestor).aplicar({"1001": -1})
    assert gestor.buscar_producto("1001").stock_actual == 10
    assert gestor.listar_movimientos_recientes() == []


def test_rechaza_codigos_inexistentes_sin_aplicar_nada(tmp_path):
    gestor = _gestor(tmp_path)
    with pytest.raises(ErrorValidacion):
        ServicioRecuento(gestor).aplicar({"1001": 4, "9999": 3})
    assert gestor.buscar_producto("1001").stock_actual == 10
    assert gestor.listar_movimientos_recientes() == []


def test_rechaza_conteos_que_no_son_numeros(tmp_path):
    gestor = _gestor(tmp_path)
    with pytest.raises(ErrorValidacion):
        ServicioRecuento(gestor).aplicar({"1001": "mucho"})
    assert gestor.buscar_producto("1001").stock_actual == 10


def test_aplica_varios_productos(tmp_path):
    gestor = _gestor(tmp_path)
    movimientos = ServicioRecuento(gestor).aplicar(
        {"1001": 7, "1002": 22, "1003": 1})
    assert [m.codigo_producto for m in movimientos] == ["1001", "1002", "1003"]
    assert gestor.buscar_producto("1001").stock_actual == 7
    assert gestor.buscar_producto("1002").stock_actual == 22
    assert gestor.buscar_producto("1003").stock_actual == 1


def test_el_motivo_del_movimiento_lleva_la_fecha_del_recuento(tmp_path):
    gestor = _gestor(tmp_path)
    movimientos = ServicioRecuento(gestor).aplicar(
        {"1001": 4}, date(2026, 10, 21))
    assert movimientos[0].motivo == "Recuento 21/10/2026"
    assert movimientos[0].motivo == motivo_recuento(date(2026, 10, 21))


def test_la_ventana_carga_las_filas(aplicacion: QApplication, tmp_path):
    ventana = VentanaRecuento(_gestor(tmp_path))
    assert ventana.tabla.rowCount() == 3
    encabezados = [
        ventana.tabla.horizontalHeaderItem(columna).text()
        for columna in range(ventana.tabla.columnCount())]
    assert encabezados == [
        "Código", "Producto", "Stock sistema", "Contado", "Diferencia"]
    assert ventana.tabla.item(0, 0).text() == "1001"
    assert ventana.tabla.item(0, 1).text() == "Tomate perita"
    assert ventana.tabla.item(0, 2).text() == "10"
    assert ventana.tabla.item(0, ventana.COLUMNA_CONTADO).text() == ""
    assert ventana.tabla.item(0, ventana.COLUMNA_DIFERENCIA).text() == ""
    assert ventana.tabla.item(0, ventana.COLUMNA_CONTADO).flags() & Qt.ItemFlag.ItemIsEditable
    assert not ventana.tabla.item(0, 2).flags() & Qt.ItemFlag.ItemIsEditable
    _cerrar(ventana)


def test_la_ventana_filtra_por_codigo_o_nombre(aplicacion: QApplication, tmp_path):
    ventana = VentanaRecuento(_gestor(tmp_path))
    ventana.txtBuscar.setText("papa")
    assert ventana.tabla.rowCount() == 1
    assert ventana.tabla.item(0, 0).text() == "1002"
    ventana.txtBuscar.setText("1003")
    assert ventana.tabla.rowCount() == 1
    assert ventana.tabla.item(0, 1).text() == "Leche entera"
    _cerrar(ventana)


def test_la_ventana_muestra_la_diferencia(aplicacion: QApplication, tmp_path):
    ventana = VentanaRecuento(_gestor(tmp_path))
    ventana.tabla.item(0, ventana.COLUMNA_CONTADO).setText("7")
    assert ventana.tabla.item(0, ventana.COLUMNA_DIFERENCIA).text() == "-3"
    ventana.tabla.item(0, ventana.COLUMNA_CONTADO).setText("12")
    assert ventana.tabla.item(0, ventana.COLUMNA_DIFERENCIA).text() == "+2"
    ventana.tabla.item(0, ventana.COLUMNA_CONTADO).setText("10")
    assert ventana.tabla.item(0, ventana.COLUMNA_DIFERENCIA).text() == "0"
    _cerrar(ventana)


def test_la_ventana_avisa_si_el_conteo_es_invalido(
    aplicacion: QApplication, tmp_path, monkeypatch
):
    ventana = VentanaRecuento(_gestor(tmp_path))
    ventana.tabla.item(0, ventana.COLUMNA_CONTADO).setText("mucho")
    avisos: list[tuple[str, str]] = []
    monkeypatch.setattr(
        ventana, "mostrar_advertencia",
        lambda titulo, mensaje: avisos.append((titulo, mensaje)))
    monkeypatch.setattr(
        ventana, "confirmar",
        lambda *_args: pytest.fail("no debería confirmar un conteo inválido"))
    ventana.aplicar_recuento()
    assert len(avisos) == 1
    assert "1001" in avisos[0][1]
    assert ventana._gestor_stock.buscar_producto("1001").stock_actual == 10
    _cerrar(ventana)


def test_la_ventana_aplica_y_refresca(
    aplicacion: QApplication, tmp_path, monkeypatch
):
    gestor = _gestor(tmp_path)
    ventana = VentanaRecuento(gestor)
    ventana.tabla.item(0, ventana.COLUMNA_CONTADO).setText("7")
    ventana.tabla.item(1, ventana.COLUMNA_CONTADO).setText("20")
    confirmaciones: list[tuple[str, str]] = []
    monkeypatch.setattr(
        ventana, "confirmar",
        lambda titulo, pregunta: confirmaciones.append((titulo, pregunta)) or True)
    avisos: list[tuple[str, str]] = []
    monkeypatch.setattr(
        Notificacion, "mostrar",
        lambda _self, titulo, mensaje: avisos.append((titulo, mensaje)))

    ventana.aplicar_recuento()

    assert len(confirmaciones) == 1
    assert "1 producto" in confirmaciones[0][1]
    assert "1001" in confirmaciones[0][1]
    assert "1002" not in confirmaciones[0][1]
    assert gestor.buscar_producto("1001").stock_actual == 7
    assert gestor.buscar_producto("1002").stock_actual == 20
    assert gestor.buscar_producto("1003").stock_actual == 5
    assert ventana.tabla.item(0, 2).text() == "7"
    assert ventana.tabla.item(0, ventana.COLUMNA_CONTADO).text() == ""
    assert ventana.tabla.item(0, ventana.COLUMNA_DIFERENCIA).text() == ""
    assert ventana._conteos == {}
    assert avisos == [("Recuento aplicado", "Se actualizó 1 producto.")]
    movimientos = gestor.listar_movimientos_recientes()
    assert len(movimientos) == 1
    assert movimientos[0].motivo == motivo_recuento(date.today())
    _cerrar(ventana)


def test_la_ventana_limpia_los_conteos(aplicacion: QApplication, tmp_path):
    gestor = _gestor(tmp_path)
    ventana = VentanaRecuento(gestor)
    ventana.tabla.item(0, ventana.COLUMNA_CONTADO).setText("7")
    assert ventana._conteos == {"1001": "7"}

    ventana.limpiar_conteos()

    assert ventana._conteos == {}
    assert ventana.tabla.item(0, ventana.COLUMNA_CONTADO).text() == ""
    assert ventana.tabla.item(0, ventana.COLUMNA_DIFERENCIA).text() == ""
    assert gestor.buscar_producto("1001").stock_actual == 10
    _cerrar(ventana)


def test_movimientos_filtra_por_motivo(aplicacion: QApplication, tmp_path):
    gestor = _gestor(tmp_path)
    recuento = ServicioRecuento(gestor)
    recuento.aplicar({"1001": 7}, date(2026, 10, 21))
    recuento.aplicar({"1002": 22}, date(2026, 10, 22))

    ventana = VentanaMovimientos(gestor)
    assert ventana.ui.tblHistorial.rowCount() == 2
    assert ventana.cmbMotivo.count() == 3

    indice = ventana.cmbMotivo.findData(motivo_recuento(date(2026, 10, 21)))
    ventana.cmbMotivo.setCurrentIndex(indice)

    assert ventana.ui.tblHistorial.rowCount() == 1
    assert ventana.ui.tblHistorial.item(0, 2).text() == "1001"
    assert ventana.ui.tblHistorial.item(0, 4).text() == motivo_recuento(date(2026, 10, 21))
    _cerrar(ventana)
