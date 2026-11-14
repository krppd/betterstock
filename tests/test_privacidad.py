from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from repositories.comercio_repositorio import ComercioRepositorio
from repositories.sqlite import ruta_db
from services.gestor_comercio import GestorComercio
from services.preferencias import (
    fotos_en_linea,
    guardar_fotos_en_linea,
    leer,
)
from views.ventana_configuracion import VentanaConfiguracion


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def gestor_comercio(tmp_path) -> GestorComercio:
    servicio = GestorComercio(ComercioRepositorio(ruta_db(tmp_path / "datos" / "betterstock.db")))
    servicio.inicializar()
    return servicio


def test_la_busqueda_de_fotos_empieza_apagada() -> None:
    assert fotos_en_linea() is False


def test_la_busqueda_de_fotos_se_puede_prender_y_apagar() -> None:
    guardar_fotos_en_linea(True)
    assert fotos_en_linea() is True
    guardar_fotos_en_linea(False)
    assert fotos_en_linea() is False


def test_la_preferencia_no_toca_las_otras() -> None:
    guardar_fotos_en_linea(True)
    assert "fotos_en_linea" in leer()
    assert set(leer()) >= {"fotos_en_linea"}


def test_los_ajustes_muestran_el_interruptor_de_la_busqueda(aplicacion, gestor_comercio) -> None:
    ventana = VentanaConfiguracion(gestor_comercio)
    try:
        assert ventana.swFotosEnLinea.isChecked() is False
        ventana.swFotosEnLinea.setChecked(True)
        ventana.guardar()
    finally:
        ventana.close()
        ventana.deleteLater()
    assert fotos_en_linea() is True


def test_los_ajustes_guardan_la_busqueda_apagada(aplicacion, gestor_comercio) -> None:
    guardar_fotos_en_linea(True)
    ventana = VentanaConfiguracion(gestor_comercio)
    try:
        assert ventana.swFotosEnLinea.isChecked() is True
        ventana.swFotosEnLinea.setChecked(False)
        ventana.guardar()
    finally:
        ventana.close()
        ventana.deleteLater()
    assert fotos_en_linea() is False


def test_el_ajuste_inicial_tambien_muestra_el_interruptor(aplicacion, gestor_comercio) -> None:
    ventana = VentanaConfiguracion(gestor_comercio)
    try:
        assert ventana.ui.btnGuardar.text() == "Guardar y continuar"
        assert ventana.swFotosEnLinea.isChecked() is False
    finally:
        ventana.close()
        ventana.deleteLater()


def test_las_preferencias_se_guardan_aunque_el_comercio_nosea_valido(aplicacion, gestor_comercio) -> None:
    ventana = VentanaConfiguracion(gestor_comercio)
    try:
        ventana.ui.txtNombre.setText("")
        ventana.swFotosEnLinea.setChecked(True)
        ventana.guardar()
        assert ventana.ui.lblError.text() != ""
    finally:
        ventana.close()
        ventana.deleteLater()
    assert fotos_en_linea() is True
