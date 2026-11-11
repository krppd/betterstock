from __future__ import annotations

import re

import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox

from models.usuario import Usuario
from repositories.sqlite import conectar, ruta_db
from repositories.usuario_repositorio import UsuarioRepositorio
from services.autenticacion import Autenticacion
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_stock import GestorStock
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from views import ventana_principal as modulo_principal
from views.ventana_principal import VentanaPrincipal

RELOJ = re.compile(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$")


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def gestores(tmp_path):
    base = ruta_db(tmp_path / "datos" / "betterstock.db")
    conectar(base).close()
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base),
    )
    stock.inicializar()
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    return stock, estadisticas


@pytest.fixture
def principal(gestores, aplicacion) -> VentanaPrincipal:
    stock, estadisticas = gestores
    vista = VentanaPrincipal(stock, None, estadisticas, None, "admin",
                             permiso=Usuario.PERMISO_ADMIN)
    yield vista
    vista.permitir_cierre()
    vista.close()
    vista.deleteLater()


def test_credenciales_ejemplo():
    for nombre, permiso in (
        ("admin", Usuario.PERMISO_ADMIN),
        ("pepe", Usuario.PERMISO_VENDEDOR),
    ):
        assert Usuario.crear(nombre, "clave", permiso).permiso == permiso


def test_el_permiso_por_omision_es_vendedor():
    usuario = Usuario.crear("lupe", "clave")
    assert usuario.permiso == Usuario.PERMISO_VENDEDOR
    assert usuario.etiqueta_permiso() == "Vendedor"


def test_el_permiso_desconocido_se_muestra_como_vendedor():
    usuario = Usuario.crear("lupe", "clave", permiso="otra-cosa")
    assert usuario.permiso == "otra-cosa"
    assert usuario.etiqueta_permiso() == "Vendedor"


def test_no_hay_usuarios_por_defecto(tmp_path):
    base = tmp_path / "datos" / "betterstock.db"
    servicio = Autenticacion(UsuarioRepositorio(base))
    servicio.inicializar()

    assert not servicio.hay_usuarios()


def test_los_usuarios_creados_tienen_su_permiso(tmp_path):
    base = tmp_path / "datos" / "betterstock.db"
    servicio = Autenticacion(UsuarioRepositorio(base))
    servicio.inicializar()
    servicio.crear_usuario("dueno", "clave-fixture", Usuario.PERMISO_ADMIN)
    servicio.crear_usuario(
        "empleado", "clave-fixture-2", Usuario.PERMISO_VENDEDOR)

    repo = UsuarioRepositorio(base)
    dueno = repo.buscar("dueno")
    empleado = repo.buscar("empleado")

    assert dueno.permiso == Usuario.PERMISO_ADMIN
    assert dueno.etiqueta_permiso() == "Administrador"
    assert empleado.permiso == Usuario.PERMISO_VENDEDOR
    assert empleado.etiqueta_permiso() == "Vendedor"


def test_cerrar_sesion_borra_el_usuario_actual(tmp_path):
    base = tmp_path / "datos" / "betterstock.db"
    servicio = Autenticacion(UsuarioRepositorio(base))
    servicio.inicializar()
    servicio.crear_usuario("dueno", "clave-fixture", Usuario.PERMISO_ADMIN)

    assert servicio.iniciar_sesion("dueno", "clave-fixture")
    assert servicio.usuario_actual is not None

    servicio.cerrar_sesion()

    assert servicio.usuario_actual is None


def test_la_base_vieja_gana_la_columna_de_permiso(tmp_path):
    base = tmp_path / "datos" / "betterstock.db"
    conectar(base).close()
    conexion = conectar(base)
    conexion.executescript(
        "DROP TABLE usuarios;"
        "CREATE TABLE usuarios(usuario TEXT PRIMARY KEY, password_hash TEXT NOT NULL);"
        "INSERT INTO usuarios(usuario, password_hash) VALUES"
        " ('admin', 'viera'), ('jakim', 'guajira');"
    )
    conexion.commit()
    conexion.close()

    repo = UsuarioRepositorio(base)
    repo.inicializar()

    assert repo.buscar("admin").permiso == Usuario.PERMISO_ADMIN
    assert repo.buscar("jakim").permiso == Usuario.PERMISO_VENDEDOR


def test_el_boton_de_usuario_muestra_el_usuario_y_su_permiso(principal):
    assert principal.ui.btnUsuario.text() == " admin\n Administrador"
    assert not principal.ui.btnUsuario.icon().isNull()
    assert not principal.ui.btnUsuario.isHidden()


def test_sin_usuario_no_hay_boton_de_usuario(gestores, aplicacion):
    stock, estadisticas = gestores
    vista = VentanaPrincipal(stock, None, estadisticas, None, "")
    try:
        assert vista.ui.btnUsuario.isHidden()
    finally:
        vista.permitir_cierre()
        vista.close()
        vista.deleteLater()


def test_al_confirmar_emite_cerrar_sesion(principal, monkeypatch):
    recibidos: list[bool] = []
    principal.sesion_cerrada.connect(lambda: recibidos.append(True))
    monkeypatch.setattr(
        modulo_principal.QMessageBox, "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes)

    principal.ui.btnUsuario.click()

    assert recibidos == [True]


def test_al_cancelar_no_emite_cerrar_sesion(principal, monkeypatch):
    recibidos: list[bool] = []
    principal.sesion_cerrada.connect(lambda: recibidos.append(True))
    monkeypatch.setattr(
        modulo_principal.QMessageBox, "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No)

    principal.ui.btnUsuario.click()

    assert recibidos == []


def test_reloj_barra_superior_no_incluye_usuario(principal):
    principal._actualizar_reloj()

    assert principal._reloj.text() != ""
    assert "admin" not in principal._reloj.text()
    assert re.match(RELOJ, principal._reloj.text())
