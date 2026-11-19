from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from services.preferencias import ESCALA_TACTIL
from ui.estilos import ESCALA_NORMAL, aplicar_escala, aplicar_tema
from views.ventana_ventas import _BarraAcciones

BOTONES = ("accionDescuento", "accionRecargo", "accionComprobante")


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


def _barra(escala: float, ancho: int) -> _BarraAcciones:
    aplicar_tema(QApplication.instance(), escala)
    barra = _BarraAcciones()
    barra.resize(ancho, barra.sizeHint().height())
    barra.show()
    QApplication.processEvents()
    barra._ajustar_atajos()
    QApplication.processEvents()
    return barra


def _cerrar(barra: _BarraAcciones) -> None:
    barra.close()
    barra.deleteLater()


def _sin_recorte(barra: _BarraAcciones) -> None:
    for nombre, boton in barra._botones.items():
        assert boton.fontMetrics().horizontalAdvance(boton.text()) + 24 <= boton.width(), nombre


def test_barra_sin_boton_cuentas() -> None:
    barra = _barra(ESCALA_NORMAL, 800)
    try:
        assert set(barra._botones) == set(BOTONES)
    finally:
        _cerrar(barra)


def test_barra_normal_sin_recortes() -> None:
    barra = _barra(ESCALA_NORMAL, 720)
    try:
        _sin_recorte(barra)
    finally:
        _cerrar(barra)


def test_barra_tactil_anchos_parejos() -> None:
    barra = _barra(ESCALA_TACTIL, 960)
    try:
        anchos = [boton.width() for boton in barra._botones.values()]
        assert max(anchos) - min(anchos) <= 2
        assert barra.cobrar.width() == barra.width()
        _sin_recorte(barra)
    finally:
        _cerrar(barra)


def test_barra_normal_muestra_los_atajos() -> None:
    barra = _barra(ESCALA_NORMAL, 1000)
    try:
        for nombre, boton in barra._botones.items():
            assert barra._textos[nombre][1] in boton.text(), nombre
        _sin_recorte(barra)
    finally:
        _cerrar(barra)


def test_barra_tactil_ancha_muestra_los_atajos_parejo() -> None:
    barra = _barra(ESCALA_TACTIL, 1520)
    try:
        for nombre, boton in barra._botones.items():
            assert barra._textos[nombre][1] in boton.text(), nombre
        _sin_recorte(barra)
    finally:
        _cerrar(barra)


def test_barra_angosta_oculta_atajos_sin_recortar() -> None:
    barra = _barra(ESCALA_TACTIL, 650)
    try:
        for nombre, boton in barra._botones.items():
            assert barra._textos[nombre][1] not in boton.text(), nombre
        _sin_recorte(barra)
    finally:
        _cerrar(barra)


def test_barra_muy_angosta_desplaza_sin_recortar() -> None:
    barra = _barra(ESCALA_TACTIL, 320)
    try:
        assert barra._scroll.horizontalScrollBar().maximum() > 0
        _sin_recorte(barra)
    finally:
        _cerrar(barra)


def test_la_barra_tactil_es_mas_alta() -> None:
    barra = _barra(ESCALA_TACTIL, 890)
    try:
        assert barra.cobrar.height() > 54
        assert barra._botones["accionDescuento"].height() > 52
    finally:
        _cerrar(barra)


def test_los_botones_emiten_sus_senales() -> None:
    barra = _barra(ESCALA_NORMAL, 1000)
    recibidas: list[str] = []
    barra.descuentoPedido.connect(lambda: recibidas.append("descuento"))
    barra.recargoPedido.connect(lambda: recibidas.append("recargo"))
    barra.comprobantePedido.connect(lambda: recibidas.append("comprobante"))
    barra.cobrarPedido.connect(lambda: recibidas.append("cobrar"))
    try:
        for nombre in BOTONES:
            barra._botones[nombre].click()
        barra.cobrar.click()
        QApplication.processEvents()
        assert recibidas == ["descuento", "recargo", "comprobante", "cobrar"]
    finally:
        _cerrar(barra)


def test_el_destello_de_cobrar_no_rompe() -> None:
    barra = _barra(ESCALA_NORMAL, 1000)
    try:
        barra.pulsar("accionCobrar", destello=True)
        QApplication.processEvents()
    finally:
        _cerrar(barra)