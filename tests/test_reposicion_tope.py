"""El límite "productos" del plan cuenta productos: no limita el stock por producto.

Reponer stock por encima de ese número debe funcionar, y el aviso del plan solo
aparece al crear el producto que excede la cantidad permitida (no al editar).
"""
from __future__ import annotations

from types import SimpleNamespace

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

LIMITE_PRODUCTOS = 50


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


def _ventana(tmp_path, cantidad: int) -> tuple[VentanaProductos, GestorStock]:
    gestor = _gestor(tmp_path, stock=10)
    for numero in range(2, cantidad + 1):
        gestor.guardar_producto(Producto(
            codigo=f"P{numero:03d}", nombre=f"Producto {numero}", stock_actual=1))
    assert len(gestor.listar_productos()) == cantidad
    return VentanaProductos(gestor), gestor


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


def _formulario(topes: list[tuple[str, str]], tmp_path, producto=None) -> FormularioProducto:
    stock = _gestor(tmp_path, stock=producto.stock_actual if producto else 10)
    if producto is not None:
        stock.guardar_producto(producto)
    formulario = FormularioProducto(stock, producto)
    formulario.mostrar_advertencia = lambda titulo, mensaje: topes.append((titulo, mensaje))
    return formulario, stock


def _formulario_nuevo(ventana: VentanaProductos, stock: GestorStock) -> FormularioProducto:
    formulario = FormularioProducto(
        stock, al_antes_de_guardar=ventana._al_antes_de_guardar)
    formulario.ui.txtCodigo.setText("2002")
    formulario.ui.txtNombre.setText("Clavos")
    formulario.ui.spnStock.setValue(5)
    return formulario


def test_reponer_sobre_stock_alto_suma_sin_recortar(tmp_path, monkeypatch, aplicacion):
    gestor = _gestor(tmp_path, stock=48)
    ventana = VentanaProductos(gestor)

    avisos = _reponer(ventana, monkeypatch, 10)

    assert gestor.buscar_producto("1001").stock_actual == 58
    assert avisos and avisos[0][0] == "Stock repuesto"
    assert all("Tope del plan" not in titulo for titulo, _ in avisos)
    assert all("El plan admite" not in mensaje for _, mensaje in avisos)


def test_reponer_cuando_el_stock_ya_supera_el_limite_funciona(tmp_path, monkeypatch, aplicacion):
    gestor = _gestor(tmp_path, stock=52)
    ventana = VentanaProductos(gestor)

    avisos = _reponer(ventana, monkeypatch, 3)

    assert gestor.buscar_producto("1001").stock_actual == 55
    assert avisos and avisos[0][0] == "Stock repuesto"
    assert all("Tope del plan" not in titulo for titulo, _ in avisos)


def test_alta_con_stock_sobre_el_limite_se_guarda(tmp_path, aplicacion):
    avisos: list[tuple[str, str]] = []
    formulario, stock = _formulario(avisos, tmp_path)
    formulario.ui.txtCodigo.setText("2002")
    formulario.ui.txtNombre.setText("Clavos")
    formulario.ui.spnStock.setValue(60)

    formulario.guardar_producto()

    assert formulario.result() == QDialog.DialogCode.Accepted
    assert avisos == []
    assert stock.buscar_producto("2002").stock_actual == 60


def test_al_crear_el_producto_51_avisa_y_no_guarda_si_no_continua(
        tmp_path, aplicacion, monkeypatch):
    ventana, stock = _ventana(tmp_path, LIMITE_PRODUCTOS)
    monkeypatch.setattr(
        "views.ventana_productos.QDesktopServices",
        SimpleNamespace(openUrl=lambda _url: False))
    avisos: list[tuple[str, str]] = []

    def elegir(titulo: str, mensaje: str, _opciones) -> str:
        avisos.append((titulo, mensaje))
        return "planes"

    monkeypatch.setattr(ventana, "elegir", elegir)
    errores: list[tuple[str, str]] = []
    formulario = _formulario_nuevo(ventana, stock)
    formulario.mostrar_advertencia = lambda titulo, mensaje: errores.append((titulo, mensaje))

    formulario.guardar_producto()

    assert len(avisos) == 1
    assert avisos[0][0] == "Límite del plan"
    assert f"{LIMITE_PRODUCTOS} productos" in avisos[0][1]
    assert formulario.result() != QDialog.DialogCode.Accepted
    assert errores and "Se canceló el guardado" in errores[0][1]
    assert stock.buscar_producto("2002") is None


def test_al_crear_el_producto_51_guarda_si_se_continua(
        tmp_path, aplicacion, monkeypatch):
    ventana, stock = _ventana(tmp_path, LIMITE_PRODUCTOS)
    avisos: list[tuple[str, str]] = []

    def elegir(titulo: str, mensaje: str, _opciones) -> str:
        avisos.append((titulo, mensaje))
        return "continuar"

    monkeypatch.setattr(ventana, "elegir", elegir)
    formulario = _formulario_nuevo(ventana, stock)

    formulario.guardar_producto()

    assert len(avisos) == 1
    assert avisos[0][0] == "Límite del plan"
    assert formulario.result() == QDialog.DialogCode.Accepted
    assert stock.buscar_producto("2002") is not None


def test_editar_producto_no_dispara_el_aviso_de_cantidad(
        tmp_path, aplicacion, monkeypatch):
    ventana, stock = _ventana(tmp_path, LIMITE_PRODUCTOS)
    llamadas: list[tuple] = []
    monkeypatch.setattr(
        ventana, "elegir",
        lambda *args, **kwargs: llamadas.append(args) or "continuar")
    formulario = FormularioProducto(
        stock, stock.buscar_producto("1001"),
        al_antes_de_guardar=ventana._al_antes_de_guardar)
    formulario.ui.txtNombre.setText("Tornillos nuevos")
    formulario.ui.spnStock.setValue(60)

    formulario.guardar_producto()

    assert llamadas == []
    assert formulario.result() == QDialog.DialogCode.Accepted
    guardado = stock.buscar_producto("1001")
    assert guardado.nombre == "Tornillos nuevos"
    assert guardado.stock_actual == 60
