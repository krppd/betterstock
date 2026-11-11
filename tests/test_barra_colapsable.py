from __future__ import annotations

import pytest
from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication

from models.usuario import Usuario
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.sqlite import conectar, ruta_db
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_stock import GestorStock
from ui.estilos import ESCALA_NORMAL, aplicar_escala
from views.ventana_principal import VentanaPrincipal


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture(autouse=True)
def escala_restaurada():
    aplicar_escala(ESCALA_NORMAL)
    yield
    aplicar_escala(ESCALA_NORMAL)


@pytest.fixture
def tactil():
    aplicar_escala(1.5)
    yield


@pytest.fixture
def gestores(tmp_path):
    base = ruta_db(tmp_path / "datos" / "betterstock.db")
    conectar(base).close()
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base),
    )
    stock.inicializar()
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    return stock, estadisticas


@pytest.fixture
def principal(gestores, aplicacion, monkeypatch) -> VentanaPrincipal:
    stock, estadisticas = gestores
    monkeypatch.setattr(
        "services.preferencias.posicion_menu", lambda ruta=None: "izquierda")
    vista = VentanaPrincipal(stock, None, estadisticas, None, "admin",
                             permiso=Usuario.PERMISO_ADMIN)
    yield vista
    vista.permitir_cierre()
    vista.close()
    vista.deleteLater()
    aplicacion.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    aplicacion.processEvents()


def test_boton_de_menu_presente(principal):
    assert principal._btn_menu is not None


def test_la_barra_fluent_arranca_expandida(principal):
    assert not principal.navigationInterface.panel.isCollapsed()


def test_al_colapsar_la_barra_fluent_queda_compacta(principal):
    principal._alternar_barra(animar=False)
    assert principal.navigationInterface.panel.isCollapsed()


def test_al_expander_la_barra_fluent_vuelve_a_modo_expandido(principal):
    principal._alternar_barra(animar=False)
    assert principal.navigationInterface.panel.isCollapsed()
    principal._alternar_barra(animar=False)
    assert not principal.navigationInterface.panel.isCollapsed()


def test_usuario_configurado_en_barra(principal):
    assert principal.ui.btnUsuario is not None
    assert "admin" in principal.ui.btnUsuario.text()
