from __future__ import annotations

import sys

import pytest
from PyQt6.QtWidgets import QApplication, QWidget

from ui.estilo_ventana import aplicar_estilo_ventana


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def test_no_tumba_la_app_sin_windows(aplicacion: QApplication) -> None:
    ventana = QWidget()
    ventana.resize(400, 300)
    ventana.show()
    resultado = aplicar_estilo_ventana(ventana)
    assert isinstance(resultado, bool)
    if sys.platform != "win32":
        assert resultado is False


def test_no_tumba_la_app_con_una_ventana_sin_pantalla(aplicacion: QApplication) -> None:
    ventana = QWidget()
    assert aplicar_estilo_ventana(ventana) in (True, False)
