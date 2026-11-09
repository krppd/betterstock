from __future__ import annotations

from datetime import date

import pytest
from PyQt6.QtWidgets import QApplication, QPushButton

from models import medio_pago
from models.venta_registrada import RenglonVenta, VentaRegistrada
from repositories.sqlite import conectar, ruta_db
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from views.ventana_estadisticas import VentanaEstadisticas

HOY = date.today()


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def estadisticas_avanzadas_activas():
    """La edición libre no tiene comparaciones premium: no hay que habilitar nada."""
    yield


@pytest.fixture
def estadisticas(tmp_path) -> EstadisticasVentas:
    base = ruta_db(tmp_path / "datos" / "betterstock.db")
    conectar(base).close()
    servicio = EstadisticasVentas(VentaRepositorio(base))
    servicio.inicializar()
    return servicio


@pytest.fixture
def ventana(aplicacion, estadisticas,
            estadisticas_avanzadas_activas) -> VentanaEstadisticas:
    vista = VentanaEstadisticas(estadisticas)
    yield vista
    vista.deleteLater()


def _venta(hora: str, medio: str, renglones: list[RenglonVenta],
           estado: str = VentaRegistrada.ESTADO_ACTIVA) -> VentaRegistrada:
    total = sum(renglon.subtotal for renglon in renglones)
    return VentaRegistrada(
        HOY, hora, total, renglones, estado=estado, medio_pago=medio)


def _yerba(cantidad: float) -> RenglonVenta:
    return RenglonVenta("A", "Yerba", cantidad, 1000.0)


def _azucar(cantidad: float) -> RenglonVenta:
    return RenglonVenta("B", "Azúcar", cantidad, 500.0)


def test_mas_vendidos_agrupa_por_producto_y_ordena_por_unidades(estadisticas):
    estadisticas.registrar(_venta("10:00", medio_pago.METODO_EFECTIVO,
                                  [_yerba(2), _azucar(1)]))
    estadisticas.registrar(_venta("11:00", medio_pago.METODO_DEBITO, [_yerba(3)]))

    ranking = estadisticas.mas_vendidos(HOY, HOY)

    assert [producto.codigo for producto in ranking] == ["A", "B"]
    assert ranking[0].nombre == "Yerba"
    assert ranking[0].unidades == 5
    assert ranking[0].total == 5000
    assert ranking[1].unidades == 1


def test_mas_vendidos_respeta_el_limite(estadisticas):
    estadisticas.registrar(_venta("10:00", medio_pago.METODO_EFECTIVO,
                                  [_yerba(2), _azucar(1)]))

    assert len(estadisticas.mas_vendidos(HOY, HOY, limite=1)) == 1


def test_la_solapa_mas_vendidos_muestra_el_ranking(ventana, estadisticas_avanzadas_activas, estadisticas):
    estadisticas.registrar(_venta("10:00", medio_pago.METODO_EFECTIVO,
                                  [_yerba(2), _azucar(1)]))
    estadisticas.registrar(_venta("11:00", medio_pago.METODO_DEBITO, [_yerba(3)]))

    ventana.actualizar()

    tabla = ventana.ui.tblRanking
    assert tabla.rowCount() == 2
    assert tabla.item(0, 0).text() == "Yerba"
    assert tabla.item(0, 1).text() == "5"
    assert tabla.item(0, 2).text() == "$ 5.000,00"
    assert tabla.item(0, 3).text() == "90,9 %"
    assert tabla.item(1, 0).text() == "Azúcar"
    assert tabla.item(1, 3).text() == "9,1 %"


def test_las_solapas_son_dos_y_cambian_la_tabla(ventana, estadisticas_avanzadas_activas):
    assert ventana.ui.stackVentas.count() == 2
    assert ventana.ui.stackVentas.currentIndex() == 0
    assert not ventana.ui.btnDetalle.isHidden()

    ventana.ui.btnRanking.click()
    assert ventana.ui.stackVentas.currentIndex() == 1
    assert ventana.ui.btnDetalle.isHidden()

    ventana.ui.btnVentas.click()
    assert ventana.ui.stackVentas.currentIndex() == 0
    assert not ventana.ui.btnDetalle.isHidden()


def test_estadisticas_no_ofrece_anular_ventas(ventana, estadisticas_avanzadas_activas):
    textos = {boton.text() for boton in ventana.findChildren(QPushButton)}

    assert "Anular" not in textos
    assert not hasattr(ventana, "anular_venta")
