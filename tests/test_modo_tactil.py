from __future__ import annotations

import json

import pytest
from PyQt6.QtWidgets import QApplication

from services import preferencias
from ui.estilos import (
    ESCALA_NORMAL,
    TAMANO_BODY,
    TAMANO_SMALL,
    TEMA_APP,
    aplicar_escala,
    aplicar_tema,
    escala,
    fuente,
)
from views.ventana_login import VentanaLogin


@pytest.fixture(scope="session")
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


def _abrir_login():
    ventana = VentanaLogin(object())
    QApplication.processEvents()
    return ventana


def test_escala_tactil_es_1_5() -> None:
    assert preferencias.ESCALA_TACTIL == 1.5


def test_preferencias_ida_y_vuelta(tmp_path) -> None:
    ruta = tmp_path / "preferencias.json"

    assert preferencias.guardar({"modo_tactil": True, "otra": "dato"}, ruta)
    assert preferencias.leer(ruta) == {"modo_tactil": True, "otra": "dato"}


def test_archivo_faltante_devuelve_vacio(tmp_path) -> None:
    ruta = tmp_path / "no_existe.json"

    assert preferencias.leer(ruta) == {}
    assert preferencias.modo_tactil(ruta) is False
    assert preferencias.escala_modo_tactil(ruta) == preferencias.ESCALA_NORMAL


def test_json_corrupto_no_rompe(tmp_path) -> None:
    ruta = tmp_path / "preferencias.json"
    ruta.write_text("{esto no es json", encoding="utf-8")

    assert preferencias.leer(ruta) == {}
    assert preferencias.modo_tactil(ruta) is False


def test_guardar_modo_tactil_conserva_el_resto(tmp_path) -> None:
    ruta = tmp_path / "preferencias.json"
    preferencias.guardar({"otra": "dato"}, ruta)

    assert preferencias.guardar_modo_tactil(True, ruta)
    assert preferencias.leer(ruta) == {"otra": "dato", "modo_tactil": True}
    assert preferencias.modo_tactil(ruta) is True
    assert preferencias.escala_modo_tactil(ruta) == preferencias.ESCALA_TACTIL


def test_guardar_no_falla_sin_permisos(tmp_path) -> None:
    ruta = tmp_path / "carpeta.json"
    ruta.mkdir()

    assert preferencias.guardar({"modo_tactil": True}, ruta) is False


def test_fuente_escalada(aplicacion: QApplication) -> None:
    normal = fuente(TAMANO_SMALL)
    assert normal.pointSize() == TAMANO_SMALL

    aplicar_escala(preferencias.ESCALA_TACTIL)
    tactil = fuente(TAMANO_SMALL)
    assert tactil.pointSize() > normal.pointSize()
    assert tactil.pointSize() == round(TAMANO_SMALL * preferencias.ESCALA_TACTIL)

    aplicar_escala(ESCALA_NORMAL)
    assert fuente(TAMANO_BODY).pointSize() == TAMANO_BODY


def test_qss_escalado(aplicacion: QApplication) -> None:
    aplicar_tema(aplicacion, preferencias.ESCALA_TACTIL)
    hoja = aplicacion.styleSheet()

    assert "font-size: 16pt;" in hoja
    assert hoja.count("font-size: 16pt;") == TEMA_APP.count("font-size: 11pt;")
    assert hoja.count("min-height: 36px;") == TEMA_APP.count("min-height: 24px;")
    assert hoja != TEMA_APP
    assert escala() == preferencias.ESCALA_TACTIL


def test_qss_normal_es_identico(aplicacion: QApplication) -> None:
    aplicar_tema(aplicacion, ESCALA_NORMAL)

    assert aplicacion.styleSheet() == TEMA_APP
    assert escala() == ESCALA_NORMAL


def test_checkbox_login_guarda_y_refleja(tmp_path, aplicacion, monkeypatch) -> None:
    ruta = tmp_path / "preferencias.json"
    monkeypatch.setattr(preferencias, "ARCHIVO_PREFERENCIAS", ruta)

    ventana = _abrir_login()
    try:
        assert ventana.chkModoTactil.isChecked() is False

        ventana.chkModoTactil.setChecked(True)

        assert ventana.chkModoTactil.isChecked() is True
        assert json.loads(ruta.read_text(encoding="utf-8"))["modo_tactil"] is True
        assert preferencias.modo_tactil(ruta) is True
        assert preferencias.escala_modo_tactil(ruta) == preferencias.ESCALA_TACTIL
    finally:
        ventana.deleteLater()

    otra = _abrir_login()
    try:
        assert otra.chkModoTactil.isChecked() is True

        otra.chkModoTactil.setChecked(False)

        assert preferencias.modo_tactil(ruta) is False
        assert json.loads(ruta.read_text(encoding="utf-8"))["modo_tactil"] is False
    finally:
        otra.deleteLater()


def test_login_tamano_fijo_y_texto_sin_recortes(aplicacion, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        preferencias, "ARCHIVO_PREFERENCIAS", tmp_path / "preferencias.json")
    ventana = _abrir_login()
    try:
        assert ventana.width() == 400
        assert ventana.minimumWidth() == ventana.maximumWidth() == 400
        assert ventana.minimumHeight() == ventana.maximumHeight()
        assert ventana.height() >= 440

        disponible = (
            ventana.ui.layoutWidget.width()
            - ventana.ui.gridLayout.contentsMargins().left()
            - ventana.ui.gridLayout.contentsMargins().right()
        )
        assert ventana.chkModoTactil.sizeHint().width() <= disponible
        assert ventana.chkModoTactil.text() == ventana.TEXTO_MODO_TACTIL
    finally:
        ventana.deleteLater()


def test_preferencia_mostrar_reloj_persistencia(tmp_path) -> None:
    ruta = tmp_path / "preferencias.json"
    assert preferencias.mostrar_reloj(ruta) is True
    assert preferencias.guardar_mostrar_reloj(False, ruta) is True
    assert preferencias.mostrar_reloj(ruta) is False
    assert preferencias.guardar_mostrar_reloj(True, ruta) is True
    assert preferencias.mostrar_reloj(ruta) is True
