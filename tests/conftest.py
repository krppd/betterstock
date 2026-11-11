from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def aplicacion_global():
    """Mantiene viva una única QApplication durante toda la sesión de tests.

    PyQt destruye los QObject sin padre (como el ``qconfig`` de Fluent) cuando
    la QApplication se garbage-colecciona. Si cada test crea su propia
    instancia y la suelta, los widgets Fluent dejan de poder crearse a mitad
    de la sesión. Reutilizar una única aplicación evita ese problema.
    """
    from PyQt6.QtWidgets import QApplication
    from ui.estilos import aplicar_color_fluent

    app = QApplication.instance() or QApplication([])
    aplicar_color_fluent(app)
    return app


@pytest.fixture(autouse=True)
def _aplicacion_viva(aplicacion_global, monkeypatch, tmp_path_factory):
    """Garantiza que exista una QApplication viva antes de cada test."""
    from qfluentwidgets import Theme, setTheme
    from services import preferencias

    setTheme(Theme.LIGHT)
    ruta_tmp = tmp_path_factory.mktemp("pref") / "preferencias.json"
    monkeypatch.setattr(preferencias, "ARCHIVO_PREFERENCIAS", ruta_tmp)
    monkeypatch.setattr(preferencias, "modo_oscuro", lambda ruta=None: False)
    return aplicacion_global


@pytest.fixture(autouse=True)
def sin_licencia_real():
    """La edición libre no tiene licencia: no hay nada que enmascarar."""
    yield


@pytest.fixture
def sin_motor_compilado():
    """La edición libre no trae motores compilados: no hay nada que apagar."""
    yield


@pytest.fixture
def sin_plugins(tmp_path):
    """La edición libre no tiene plugins: no hay nada que deshabilitar."""
    yield None
