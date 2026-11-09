"""Primer arranque: alta del usuario principal."""
import pytest

from models.usuario import Usuario
from repositories.usuario_repositorio import UsuarioRepositorio
from services.autenticacion import Autenticacion


@pytest.fixture
def autenticacion(tmp_path) -> Autenticacion:
    return Autenticacion(UsuarioRepositorio(tmp_path / "usuarios.csv"))


def test_primer_arranque_sin_usuarios(autenticacion):
    autenticacion.inicializar(sembrar_iniciales=False)
    assert autenticacion.hay_usuarios() is False


def test_primer_usuario_es_administrador(autenticacion):
    autenticacion.inicializar(sembrar_iniciales=False)
    usuario = autenticacion.crear_usuario("dueno", "clave1234")
    assert usuario.permiso == Usuario.PERMISO_ADMIN
    assert autenticacion.hay_usuarios() is True
    assert autenticacion.usuario_actual is usuario
    assert autenticacion.iniciar_sesion("dueno", "clave1234")


def test_no_se_pisa_un_nombre_existente(autenticacion):
    autenticacion.inicializar(sembrar_iniciales=False)
    autenticacion.crear_usuario("dueno", "clave1234")
    with pytest.raises(ValueError):
        autenticacion.crear_usuario("dueno", "otraclave")
