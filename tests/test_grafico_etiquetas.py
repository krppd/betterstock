from __future__ import annotations

import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from ui.estilos import ESCALA_NORMAL, aplicar_escala, aplicar_tema
from ui.widgets.grafico_ventas import GraficoVentas

PUNTOS = [(f"{dia:02d}", 2500.0 + dia) for dia in range(1, 31)]


@pytest.fixture(scope="session", autouse=True)
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture(autouse=True)
def escala_normal():
    aplicar_escala(ESCALA_NORMAL)
    yield
    aplicar_escala(ESCALA_NORMAL)


def _grafico(ancho: int, escala: float) -> GraficoVentas:
    aplicar_tema(QApplication.instance(), escala)
    vista = GraficoVentas(PUNTOS, 12.5)
    vista.resize(ancho, 285)
    vista.show()
    QApplication.processEvents()
    return vista


def _etiquetas_visibles(vista: GraficoVentas) -> int:
    return sum(1 for categoria in vista._eje_x.categories() if categoria)


def test_ventana_ancha_muestra_todas_las_etiquetas() -> None:
    vista = _grafico(1520, 1.5)
    try:
        assert _etiquetas_visibles(vista) == len(PUNTOS)
    finally:
        vista.close()
        vista.deleteLater()


def test_ventana_angosta_muestra_una_de_cada_dos() -> None:
    vista = _grafico(890, 1.5)
    try:
        assert _etiquetas_visibles(vista) == len(PUNTOS) // 2
    finally:
        vista.close()
        vista.deleteLater()


def test_las_etiquetas_se_recalculan_al_redimensionar() -> None:
    vista = _grafico(1520, 1.5)
    try:
        assert _etiquetas_visibles(vista) == len(PUNTOS)
        vista.resize(890, 285)
        if not _ancho_aplicado(vista, 890):
            pytest.skip("El compositor no aplica el cambio de tamaño redimensionar")
        assert _etiquetas_visibles(vista) == len(PUNTOS) // 2
        vista.resize(1600, 285)
        if not _ancho_aplicado(vista, 1600):
            pytest.skip("El compositor no aplica el cambio de tamaño redimensionar")
        assert _etiquetas_visibles(vista) == len(PUNTOS)
    finally:
        vista.close()
        vista.deleteLater()


def _ancho_aplicado(vista: GraficoVentas, ancho: int) -> bool:
    for _ in range(50):
        QApplication.processEvents()
        if vista.width() == ancho:
            return True
        QTest.qWait(20)
    return False


def test_escala_normal_tambien_reparte_las_etiquetas() -> None:
    vista = _grafico(1000, ESCALA_NORMAL)
    try:
        assert _etiquetas_visibles(vista) == len(PUNTOS) // 2
    finally:
        vista.close()
        vista.deleteLater()
