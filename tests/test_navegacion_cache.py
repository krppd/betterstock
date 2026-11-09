from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QWidget

from models.usuario import Usuario
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.sqlite import conectar, ruta_db
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_stock import GestorStock
from views import ventana_principal as modulo


class PaginaFalsa(QWidget):
    """Página de reemplazo que cuenta cuántas veces la instancian y la muestran."""

    def __init__(self, cuenta: list[int]) -> None:
        super().__init__()
        self.cuenta = cuenta
        self.mostrados = 0
        cuenta[0] += 1

    def al_mostrar(self) -> None:
        self.mostrados += 1


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


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
def principal(gestores, aplicacion, monkeypatch) -> modulo.VentanaPrincipal:
    stock, estadisticas = gestores
    monkeypatch.setattr(
        "services.preferencias.posicion_menu", lambda ruta=None: "izquierda")
    vista = modulo.VentanaPrincipal(stock, None, estadisticas, None, "admin",
                                    permiso=Usuario.PERMISO_ADMIN)
    yield vista
    vista.permitir_cierre()
    vista.close()
    vista.deleteLater()


def test_navegar_repetido_no_vuelve_a_construir_la_pagina(principal, monkeypatch):
    cuenta = [0]
    monkeypatch.setattr(modulo, "VentanaAlertas", lambda *a, **k: PaginaFalsa(cuenta))

    principal.abrir_alertas()
    pagina = principal._paginas.currentWidget()
    principal.abrir_alertas()
    principal.abrir_alertas()

    assert cuenta[0] == 1
    assert principal._paginas.currentWidget() is pagina


def test_cada_navegacion_refresca_la_pagina(principal, monkeypatch):
    monkeypatch.setattr(modulo, "VentanaAlertas", lambda *a, **k: PaginaFalsa([0]))

    principal.abrir_alertas()
    pagina = principal._paginas.currentWidget()
    assert pagina.mostrados == 1

    principal.abrir_alertas()
    assert pagina.mostrados == 2


def test_la_pagina_repetida_queda_en_la_misma_pestana(principal, monkeypatch):
    monkeypatch.setattr(modulo, "VentanaAlertas", lambda *a, **k: PaginaFalsa([0]))

    principal.abrir_alertas()
    principal.abrir_alertas()

    assert principal._indices["alertas"] == principal._paginas.currentIndex()
