from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QDialog

from models.usuario import Usuario
from repositories.usuario_repositorio import UsuarioRepositorio
from services.autenticacion import Autenticacion
from views.dialogo_password import DialogoCambiarPassword


@pytest.fixture
def servicio(tmp_path) -> Autenticacion:
    servicio = Autenticacion(UsuarioRepositorio(tmp_path / "usuarios.csv"))
    servicio.inicializar(sembrar_iniciales=False)
    servicio.crear_usuario("dueno", "clave1", Usuario.PERMISO_ADMIN)
    return servicio


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def test_cambiar_password_requiere_la_actual(servicio):
    with pytest.raises(ValueError, match="actual"):
        servicio.cambiar_password("incorrecta", "clave2")

    assert servicio.iniciar_sesion("dueno", "clave1")


def test_cambia_la_password_y_mantiene_la_sesion(servicio):
    servicio.cambiar_password("clave1", "clave2")

    assert servicio.usuario_actual.nombre == "dueno"

    servicio.cerrar_sesion()
    assert not servicio.iniciar_sesion("dueno", "clave1")
    assert servicio.iniciar_sesion("dueno", "clave2")


def test_la_password_nueva_debe_ser_valida(servicio):
    with pytest.raises(ValueError, match="al menos"):
        servicio.cambiar_password("clave1", "12")


def test_el_dialogo_valida_los_datos(aplicacion, monkeypatch):
    dialogo = DialogoCambiarPassword()
    avisos: list[tuple[str, str]] = []
    monkeypatch.setattr(
        dialogo, "mostrar_advertencia",
        lambda titulo, mensaje: avisos.append((titulo, mensaje)))

    dialogo.txtActual.setText("clave1")
    dialogo.txtPassword.setText("clave2")
    dialogo.txtRepetir.setText("otra")
    dialogo.guardar()

    assert avisos
    assert dialogo.datos == ("", "")
    assert dialogo.result() != QDialog.DialogCode.Accepted


def test_el_dialogo_devuelve_la_password(aplicacion):
    dialogo = DialogoCambiarPassword()
    dialogo.txtActual.setText("clave1")
    dialogo.txtPassword.setText("clave2")
    dialogo.txtRepetir.setText("clave2")

    dialogo.guardar()

    assert dialogo.datos == ("clave1", "clave2")
    assert dialogo.result() == QDialog.DialogCode.Accepted
