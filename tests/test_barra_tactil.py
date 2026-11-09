from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtWidgets import QApplication
from PyQt6.QtQuickWidgets import QQuickWidget

from services.preferencias import ESCALA_TACTIL
from ui.estilos import ESCALA_NORMAL, aplicar_escala, aplicar_tema
from ui.tema import puente_tema

RAIZ = Path(__file__).resolve().parent.parent
QML = RAIZ / "ui" / "qml" / "components" / "BarraAccionesVentas.qml"
BOTONES = ("accionDescuento", "accionRecargo",
           "accionComprobante", "accionCuentas")
ALTO_BARRA = 114


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


def _barra(escala: float, ancho: int, alto: int):
    aplicar_tema(QApplication.instance(), escala)
    rapido = QQuickWidget()
    rapido.rootContext().setContextProperty("Tema", puente_tema(rapido))
    rapido.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    rapido.setSource(QUrl.fromLocalFile(str(QML)))
    raiz = rapido.rootObject()
    assert raiz is not None, "la barra no cargó"
    raiz.setProperty("escala", escala)
    rapido.resize(ancho, alto)
    rapido.show()
    QApplication.processEvents()
    return rapido, raiz


def _botones(raiz: QObject) -> list[tuple[str, QObject]]:
    encontrados = []
    for nombre in BOTONES:
        boton = raiz.findChild(QObject, nombre)
        assert boton is not None, nombre
        encontrados.append((nombre, boton))
    return encontrados


def _ancho_contenido(boton: QObject) -> float:
    return (boton.property("anchoTexto")
            + boton.property("anchoInsignia") + 32)


def _assert_sin_recorte(raiz: QObject) -> None:
    for nombre, boton in _botones(raiz):
        assert boton.property("anchoEtiqueta") + 0.5 >= boton.property("anchoTexto"), nombre
        assert boton.property("width") + 0.5 >= _ancho_contenido(boton), nombre


def test_barra_normal_sin_recortes() -> None:
    rapido, raiz = _barra(ESCALA_NORMAL, 720, ALTO_BARRA)
    try:
        _assert_sin_recorte(raiz)
    finally:
        rapido.close()
        rapido.deleteLater()


def test_barra_tactil_ancho_maximizado_parejo_sin_scroll() -> None:
    rapido, raiz = _barra(ESCALA_TACTIL, 1168, round(ALTO_BARRA * ESCALA_TACTIL))
    try:
        botones = _botones(raiz)
        anchos = [boton.property("width") for _, boton in botones]
        assert max(anchos) - min(anchos) <= 2.0
        scroll = raiz.findChild(QObject, "accionesScroll")
        assert scroll is not None
        assert scroll.property("contentWidth") <= scroll.property("width") + 1.0
        for _, boton in botones:
            assert boton.property("anchoInsignia") == 0
        _assert_sin_recorte(raiz)
    finally:
        rapido.close()
        rapido.deleteLater()


def test_barra_normal_muestra_los_atajos() -> None:
    rapido, raiz = _barra(ESCALA_NORMAL, 1000, ALTO_BARRA)
    try:
        for _, boton in _botones(raiz):
            assert boton.property("anchoInsignia") > 0
        _assert_sin_recorte(raiz)
    finally:
        rapido.close()
        rapido.deleteLater()


def test_barra_tactil_sin_recortes() -> None:
    rapido, raiz = _barra(ESCALA_TACTIL, 890, round(ALTO_BARRA * ESCALA_TACTIL))
    try:
        _assert_sin_recorte(raiz)
    finally:
        rapido.close()
        rapido.deleteLater()


def test_barra_tactil_anchos_parejos_y_llena_el_ancho() -> None:
    rapido, raiz = _barra(ESCALA_TACTIL, 1400, round(ALTO_BARRA * ESCALA_TACTIL))
    try:
        botones = _botones(raiz)
        anchos = [boton.property("width") for _, boton in botones]
        assert max(anchos) - min(anchos) <= 2.0
        separacion = raiz.property("separacion")
        total = sum(anchos) + separacion * (len(anchos) - 1)
        assert abs(total - raiz.property("width")) <= 1.0
        _assert_sin_recorte(raiz)
    finally:
        rapido.close()
        rapido.deleteLater()


def test_barra_tactil_ancha_muestra_los_atajos_parejo() -> None:
    rapido, raiz = _barra(ESCALA_TACTIL, 1520, round(ALTO_BARRA * ESCALA_TACTIL))
    try:
        botones = _botones(raiz)
        for _, boton in botones:
            assert boton.property("anchoInsignia") > 0
        anchos = [boton.property("width") for _, boton in botones]
        assert max(anchos) - min(anchos) <= 2.0
        scroll = raiz.findChild(QObject, "accionesScroll")
        assert scroll is not None
        assert scroll.property("contentWidth") <= scroll.property("width") + 1.0
        _assert_sin_recorte(raiz)
    finally:
        rapido.close()
        rapido.deleteLater()


def test_barra_tactil_ventana_angosta_desplaza_sin_recortar() -> None:
    rapido, raiz = _barra(ESCALA_TACTIL, 890, round(ALTO_BARRA * ESCALA_TACTIL))
    try:
        scroll = raiz.findChild(QObject, "accionesScroll")
        assert scroll is not None
        assert scroll.property("contentWidth") + 0.5 >= scroll.property("width")
        ultimo = raiz.findChild(QObject, BOTONES[-1])
        assert ultimo is not None
        assert (scroll.property("contentWidth") + 0.5
                >= ultimo.property("x") + ultimo.property("width"))
        _assert_sin_recorte(raiz)
    finally:
        rapido.close()
        rapido.deleteLater()


def test_la_barra_tactil_es_mas_alta() -> None:
    rapido, raiz = _barra(ESCALA_TACTIL, 890, round(ALTO_BARRA * ESCALA_TACTIL))
    try:
        assert raiz.property("escala") == ESCALA_TACTIL
        cobrar = raiz.findChild(QObject, "accionCobrar")
        assert cobrar is not None
        assert cobrar.property("height") > 54
    finally:
        rapido.close()
        rapido.deleteLater()
