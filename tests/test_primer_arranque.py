"""Smoke test del primer arranque: alta del administrador y primer ingreso."""
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QDialog

from models.usuario import Usuario
from repositories.sqlite import ruta_db
from repositories.usuario_repositorio import UsuarioRepositorio
from services.autenticacion import Autenticacion
from views.ventana_primer_usuario import (
    TEXTO_PASSWORD,
    TEXTO_REPETICION,
    TEXTO_USUARIO,
    VentanaPrimerUsuario,
)

PASSWORD = "clave1234"
PASSWORD_NUEVA = "clave5678"


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def base(tmp_path):
    return ruta_db(tmp_path / "datos" / "betterstock.db")


@pytest.fixture
def autenticacion(base) -> Autenticacion:
    servicio = Autenticacion(UsuarioRepositorio(base))
    servicio.inicializar(sembrar_iniciales=False)
    return servicio


def _completar(ventana, usuario, password, repetir=None) -> None:
    ventana.txtUsuario.setText(usuario)
    ventana.txtPassword.setText(password)
    ventana.txtRepetir.setText(password if repetir is None else repetir)


def _cerrar(ventana) -> None:
    ventana.close()
    ventana.deleteLater()


def test_una_base_nueva_queda_sin_usuarios(autenticacion):
    assert not autenticacion.hay_usuarios()
    assert autenticacion.usuario_actual is None


def test_la_ventana_crea_el_administrador_y_deja_la_sesion_iniciada(
        aplicacion, autenticacion, base):
    ventana = VentanaPrimerUsuario(autenticacion)
    try:
        _completar(ventana, "dueno", PASSWORD)
        ventana.crear()

        assert ventana.result() == QDialog.DialogCode.Accepted
    finally:
        _cerrar(ventana)

    assert autenticacion.hay_usuarios()

    actual = autenticacion.usuario_actual
    assert actual is not None
    assert actual.nombre == "dueno"
    assert actual.permiso == Usuario.PERMISO_ADMIN
    assert actual.etiqueta_permiso() == "Administrador"

    otra = Autenticacion(UsuarioRepositorio(base))
    assert otra.iniciar_sesion("dueno", PASSWORD)


@pytest.mark.parametrize(
    ("usuario", "password", "repetir", "mensaje"),
    [
        ("ab", PASSWORD, PASSWORD, TEXTO_USUARIO),
        ("dueno", "abc", "abc", TEXTO_PASSWORD),
        ("dueno", PASSWORD, "otra1234", TEXTO_REPETICION),
    ],
)
def test_las_validaciones_avisan_y_no_crean_usuario(
        aplicacion, autenticacion, usuario, password, repetir, mensaje):
    ventana = VentanaPrimerUsuario(autenticacion)
    try:
        _completar(ventana, usuario, password, repetir)
        ventana.crear()

        assert ventana.lblError.text() == mensaje
        assert ventana.result() != QDialog.DialogCode.Accepted
    finally:
        _cerrar(ventana)

    assert not autenticacion.hay_usuarios()
    assert autenticacion.usuario_actual is None


def test_el_admin_cambia_su_password_y_la_nueva_sirve_para_entrar(
        aplicacion, autenticacion, base):
    ventana = VentanaPrimerUsuario(autenticacion)
    try:
        _completar(ventana, "dueno", PASSWORD)
        ventana.crear()
    finally:
        _cerrar(ventana)

    assert autenticacion.usuario_actual is not None

    autenticacion.cambiar_password(PASSWORD, PASSWORD_NUEVA)

    otra = Autenticacion(UsuarioRepositorio(base))
    assert not otra.iniciar_sesion("dueno", PASSWORD)
    assert otra.iniciar_sesion("dueno", PASSWORD_NUEVA)
