from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from models.producto import Producto
from models.usuario import Usuario
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from services.gestor_stock import GestorStock
from views.dialogo_producto import DialogoProducto
from views.ventana_consulta import VentanaConsulta
from views.ventana_productos import VentanaProductos
from views.ventana_reportes import VentanaReportes


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def stock(tmp_path) -> GestorStock:
    base = tmp_path / "permisos.db"
    gestor = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base),
    )
    gestor.inicializar()
    gestor.guardar_producto(Producto(
        "1001", "Yerba", "Almacén", "u",
        precio_costo=100.0, precio_venta=200.0,
        stock_actual=5.0, stock_minimo=1.0,
    ))
    return gestor


def _botones_de_productos(ventana: VentanaProductos) -> list:
    botones = [
        ventana.ui.btnNuevo,
        ventana.ui.btnEditar,
        ventana.ui.btnEliminar,
        ventana.btnAgregarCategoria,
        ventana.btnReponer,
        ventana.btnRecuento,
    ]
    if hasattr(ventana, "btnImportarLista"):
        botones.append(ventana.btnImportarLista)
    premium = getattr(ventana, "btnActualizarPrecios", None)
    if premium is not None:
        botones.append(premium)
    return botones


def test_el_vendedor_no_ve_las_acciones_de_productos(stock, aplicacion):
    ventana = VentanaProductos(stock, Usuario.PERMISO_VENDEDOR)

    assert all(boton.isHidden() for boton in _botones_de_productos(ventana))


def test_el_administrador_ve_las_acciones_de_productos(stock, aplicacion):
    ventana = VentanaProductos(stock, Usuario.PERMISO_ADMIN)

    assert all(not boton.isHidden() for boton in _botones_de_productos(ventana))


def test_el_vendedor_no_puede_abrir_el_formulario_de_producto(stock, aplicacion):
    ventana = VentanaProductos(stock, Usuario.PERMISO_VENDEDOR)
    avisos: list[tuple[str, str]] = []
    ventana.mostrar_advertencia = lambda titulo, mensaje: avisos.append(
        (titulo, mensaje))

    ventana.abrir_formulario()

    assert ventana.formulario is None
    assert avisos
    assert "administrador" in avisos[0][1]


def test_el_vendedor_tampoco_puede_reponer_ni_eliminar(stock, aplicacion):
    ventana = VentanaProductos(stock, Usuario.PERMISO_VENDEDOR)
    avisos: list[tuple[str, str]] = []
    ventana.mostrar_advertencia = lambda titulo, mensaje: avisos.append(
        (titulo, mensaje))

    ventana.reponer_stock()
    ventana.eliminar_producto()

    assert stock.buscar_producto("1001") is not None
    assert len(avisos) == 2


def test_el_detalle_del_vendedor_es_solo_lectura(stock, aplicacion):
    dialogo = DialogoProducto(
        stock.buscar_producto("1001"),
        al_editar=lambda: True,
        al_eliminar=lambda: True,
        solo_lectura=True,
    )

    assert dialogo.btnEditar.isHidden()
    assert dialogo.btnEliminar.isHidden()
    assert not dialogo.btnCerrar.isHidden()


def test_el_vendedor_no_ve_el_stock_valorizado(stock, aplicacion):
    ventana = VentanaReportes(stock, None, Usuario.PERMISO_VENDEDOR)

    assert ventana.ui.lblTotal.isHidden()
    assert ventana.ui.lblTotal.text() == ""


def test_el_administrador_ve_el_stock_valorizado(stock, aplicacion):
    ventana = VentanaReportes(stock, None, Usuario.PERMISO_ADMIN)

    assert not ventana.ui.lblTotal.isHidden()
    assert "Stock total valorizado" in ventana.ui.lblTotal.text()


def test_el_vendedor_no_puede_dar_de_alta_desde_consulta(stock, aplicacion):
    ventana = VentanaConsulta(stock, Usuario.PERMISO_VENDEDOR)
    avisos: list[tuple[str, str]] = []
    ventana.mostrar_advertencia = lambda titulo, mensaje: avisos.append(
        (titulo, mensaje))

    ventana._avisar_sin_resultados("9999")
    ventana.dar_de_alta()

    assert ventana.ui.btnAlta.isHidden()
    assert avisos


def test_el_administrador_puede_dar_de_alta_desde_consulta(stock, aplicacion):
    ventana = VentanaConsulta(stock, Usuario.PERMISO_ADMIN)

    ventana._avisar_sin_resultados("9999")

    assert not ventana.ui.btnAlta.isHidden()
