"""Tope del plan en stock: reposición y formulario no superan el límite del plan."""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QDialog

from models.producto import Producto
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from services.gestor_stock import GestorStock
from ui.widgets.notificacion import Notificacion
from views.formulario_producto import FormularioProducto
from views.ventana_productos import VentanaProductos


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def _gestor(tmp_path, stock: float) -> GestorStock:
    gestor = GestorStock(
        ProductoRepositorio(tmp_path / "stock.db"),
        MovimientoRepositorio(tmp_path / "stock.db"),
        CategoriaRepositorio(tmp_path / "stock.db"))
    gestor.inicializar()
    gestor.guardar_producto(Producto(
        codigo="1001", nombre="Tornillos", stock_actual=stock))
    return gestor


def _reponer(ventana, monkeypatch, cantidad: float) -> list[tuple[str, str]]:
    monkeypatch.setattr(
        "views.ventana_productos.pedir_cantidad",
        lambda *a, **k: (cantidad, True))
    avisos: list[tuple[str, str]] = []
    monkeypatch.setattr(
        Notificacion, "mostrar",
        lambda _self, titulo, mensaje: avisos.append((titulo, mensaje)))
    ventana.ui.tblProductos.selectRow(0)
    ventana.reponer_stock()
    return avisos


def test_repo_recorta_al_tope_del_plan(tmp_path, monkeypatch, aplicacion):
    gestor = _gestor(tmp_path, stock=48)
    ventana = VentanaProductos(gestor)

    avisos = _reponer(ventana, monkeypatch, 10)

    assert gestor.buscar_producto("1001").stock_actual == 50
    assert avisos and "El plan admite" in avisos[0][1]


def test_repo_ya_en_el_tope_avisa_y_no_repone(tmp_path, monkeypatch, aplicacion):
    gestor = _gestor(tmp_path, stock=52)
    ventana = VentanaProductos(gestor)
    movimientos = len(gestor.listar_movimientos_recientes())

    avisos = _reponer(ventana, monkeypatch, 3)

    assert gestor.buscar_producto("1001").stock_actual == 52
    assert len(gestor.listar_movimientos_recientes()) == movimientos
    assert avisos and avisos[0][0] == "Tope del plan"


def _formulario(topes: list[tuple[str, str]], tmp_path, producto=None) -> FormularioProducto:
    stock = _gestor(tmp_path, stock=producto.stock_actual if producto else 10)
    if producto is not None:
        stock.guardar_producto(producto)
    formulario = FormularioProducto(stock, producto)
    formulario.mostrar_advertencia = lambda titulo, mensaje: topes.append((titulo, mensaje))
    return formulario, stock


def test_alta_con_stock_sobre_el_tope_avisa(tmp_path, aplicacion):
    avisos: list[tuple[str, str]] = []
    formulario, stock = _formulario(avisos, tmp_path)
    formulario.ui.txtCodigo.setText("2002")
    formulario.ui.txtNombre.setText("Clavos")
    formulario.ui.spnStock.setValue(60)

    formulario.guardar_producto()

    assert formulario.result() != QDialog.DialogCode.Accepted
    assert len(avisos) == 1 and "El plan admite" in avisos[0][1]
    assert stock.buscar_producto("2002") is None


def test_editar_subiendo_stock_sobre_el_tope_avisa(tmp_path, aplicacion):
    avisos: list[tuple[str, str]] = []
    formulario, stock = _formulario(avisos, tmp_path, Producto(
        codigo="1001", nombre="Tornillos", stock_actual=48))
    assert formulario.ui.spnStock.value() == 48
    formulario.ui.txtNombre.setText("Tornillos nuevos")
    formulario.ui.spnStock.setValue(60)

    formulario.guardar_producto()

    assert len(avisos) == 1 and "El plan admite" in avisos[0][1]
    guardado = stock.buscar_producto("1001")
    assert guardado.stock_actual == 48
    assert guardado.nombre == "Tornillos"


def test_editar_deja_stock_heredado_sobre_el_tope_si_no_sub(tmp_path, aplicacion):
    avisos: list[tuple[str, str]] = []
    formulario, stock = _formulario(avisos, tmp_path, Producto(
        codigo="1001", nombre="Tornillos", stock_actual=52))
    formulario.ui.txtNombre.setText("Tornillos nuevos")

    formulario.guardar_producto()

    assert formulario.result() == QDialog.DialogCode.Accepted
    assert avisos == []
    guardado = stock.buscar_producto("1001")
    assert guardado.nombre == "Tornillos nuevos"
    assert guardado.stock_actual == 52
