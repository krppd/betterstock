from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from repositories.caja_movimiento_repositorio import CajaMovimientoRepositorio
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cierre_repositorio import CierreRepositorio
from repositories.cliente_repositorio import ClienteRepositorio
from repositories.codigo_repositorio import CodigoRepositorio
from repositories.comercio_repositorio import ComercioRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.turno_repositorio import TurnoRepositorio
from repositories.usuario_repositorio import UsuarioRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.autenticacion import Autenticacion
from services.caja import ServicioCaja
from services.cierre_caja import ServicioCierre
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_anulaciones import GestorAnulaciones
from services.gestor_comercio import GestorComercio
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from services.turnos import ServicioTurnos
from views.ventana_principal import VentanaPrincipal


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def principal(aplicacion, tmp_path) -> VentanaPrincipal:
    db = tmp_path / "betterstock.db"
    gestor_stock = GestorStock(
        ProductoRepositorio(db), MovimientoRepositorio(db), CategoriaRepositorio(db))
    autenticacion = Autenticacion(UsuarioRepositorio(db))
    gestor_comercio = GestorComercio(ComercioRepositorio(db))
    estadisticas = EstadisticasVentas(VentaRepositorio(db))
    fiado = GestorFiado(ClienteRepositorio(db), CuentaRepositorio(db))
    cierre = ServicioCierre(estadisticas, CierreRepositorio(db), fiado)
    turnos = ServicioTurnos(
        TurnoRepositorio(db), VentaRepositorio(db), CuentaRepositorio(db))
    caja = ServicioCaja(CajaMovimientoRepositorio(db), cierres=cierre, turnos=turnos,
                        codigos=CodigoRepositorio(db))
    cierre.caja = caja
    turnos.caja = caja
    gestor_ventas = GestorVentas(gestor_stock, estadisticas, fiado, cierre)
    anulaciones = GestorAnulaciones(gestor_ventas, CodigoRepositorio(db))
    for servicio in (gestor_stock, autenticacion, gestor_comercio, estadisticas,
                     fiado, cierre, turnos, caja, anulaciones):
        servicio.inicializar()
    ventana = VentanaPrincipal(
        gestor_stock, gestor_comercio, estadisticas, cierre, "dueno", fiado,
        gestor_ventas=gestor_ventas, anulaciones=anulaciones,
        permiso="administrador", autenticacion=autenticacion, turnos=turnos, caja=caja)
    yield ventana
    ventana.permitir_cierre()
    ventana.close()
    ventana.deleteLater()


def test_el_panel_lateral_no_tapa_el_contenido(principal) -> None:
    principal.resize(1400, 900)
    principal.show()
    QApplication.processEvents()
    panel = principal.navigationInterface.panel
    assert principal.stackedWidget.geometry().left() >= panel.width()


def test_el_contenido_empieza_al_derecho_del_panel(principal) -> None:
    principal.resize(1400, 900)
    principal.show()
    QApplication.processEvents()
    panel = principal.navigationInterface.panel
    assert principal.stackedWidget.x() >= panel.x() + panel.width() - 1


def test_el_panel_no_queda_flotuando_sobre_el_contenido(principal) -> None:
    principal.resize(1400, 900)
    principal.show()
    QApplication.processEvents()
    assert principal.navigationInterface.width() >= \
        principal.navigationInterface.panel.width()
