from __future__ import annotations

from datetime import date, timedelta

import pytest
from PyQt6.QtWidgets import QApplication

from repositories.cliente_repositorio import ClienteRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from services import preferencias
from services.gestor_fiado import GestorFiado
from utils.formato import formatear_dinero
from views.dialogo_pago import DialogoPago

HOY = date.today()
DEUDA = 10000.0
RECARGO = 2000.0


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture(autouse=True)
def preferencias_propias(tmp_path, monkeypatch):
    """El diálogo lee la config: que no toque ni lea las preferencias de la máquina."""
    ruta = tmp_path / "preferencias.json"
    monkeypatch.setattr(preferencias, "ARCHIVO_PREFERENCIAS", ruta)
    return ruta


@pytest.fixture
def fiado(tmp_path) -> GestorFiado:
    gestor = GestorFiado(
        ClienteRepositorio(tmp_path / "clientes.csv"),
        CuentaRepositorio(tmp_path / "cuenta.csv"))
    gestor.inicializar()
    return gestor


def con_deuda(fiado: GestorFiado, dias: int = 60) -> str:
    cliente = fiado.guardar_cliente("Juan")
    fiado.registrar_cargo(cliente.identificador, DEUDA, HOY - timedelta(days=dias))
    return cliente.identificador


def detalles(fiado: GestorFiado, codigo: str) -> list[str]:
    return [m.detalle for m in fiado.movimientos_de(codigo)]


def test_sin_config_el_dialogo_es_el_de_siempre(aplicacion, fiado) -> None:
    codigo = con_deuda(fiado)
    dialogo = DialogoPago(fiado, codigo)
    assert dialogo.spnImporte.maximum() == DEUDA
    assert dialogo.spnImporte.value() == DEUDA


