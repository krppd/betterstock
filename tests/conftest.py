from __future__ import annotations

from pathlib import Path

import pytest


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
