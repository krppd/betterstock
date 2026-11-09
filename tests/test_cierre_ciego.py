from __future__ import annotations

import sqlite3
from datetime import date

import pytest
from PyQt6.QtWidgets import QApplication

from models.cierre import CierreRegistrado
from models.venta_registrada import RenglonVenta, VentaRegistrada
from repositories.cierre_repositorio import CierreRepositorio
from repositories.sqlite import conectar, ruta_db
from repositories.venta_repositorio import VentaRepositorio
from services.backup import ServicioBackup
from services.cierre_caja import ServicioCierre
from services.estadisticas_ventas import EstadisticasVentas
from views.ventana_cierre import VentanaCierre

HOY = date.today()

PLAN_CIEGO = {
    "id": "anual",
    "titulo": "Anual",
    "limites": {"productos": None, "dias_estadisticas": 365, "importaciones": 200},
    "funciones": {"cierre_ciego": True},
}


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def base(tmp_path):
    ruta = ruta_db(tmp_path / "datos" / "betterstock.db")
    conectar(ruta).close()
    return ruta


@pytest.fixture
def estadisticas(base) -> EstadisticasVentas:
    servicio = EstadisticasVentas(VentaRepositorio(base))
    servicio.inicializar()
    return servicio


@pytest.fixture
def servicio(base, estadisticas, tmp_path) -> ServicioCierre:
    cierre = ServicioCierre(
        estadisticas,
        CierreRepositorio(base),
        backup=ServicioBackup(base, tmp_path / "backups"),
    )
    cierre.inicializar()
    return cierre


@pytest.fixture
def ventana(aplicacion, servicio):
    creadas: list[VentanaCierre] = []

    def crear(permiso: str = "vendedor", usuario: str = "empleado") -> VentanaCierre:
        vista = VentanaCierre(servicio, usuario, permiso)
        creadas.append(vista)
        return vista

    yield crear
    for vista in creadas:
        vista.deleteLater()


def _venta(total: float = 1000.0) -> VentaRegistrada:
    return VentaRegistrada(
        HOY, "10:00", total, [RenglonVenta("P1", "Producto de prueba", 1, total)],
        medio_pago="efectivo")


def test_el_cierre_guarda_el_usuario(estadisticas, servicio):
    estadisticas.registrar(_venta())

    registro = servicio.cerrar(HOY, 1000.0, "turno mañana", "empleado")

    assert registro.usuario == "empleado"
    assert servicio.historial()[-1].usuario == "empleado"


def test_la_tabla_vieja_de_cierres_gana_la_columna_usuario(tmp_path):
    base = ruta_db(tmp_path / "datos" / "betterstock.db")
    conectar(base).close()
    conexion = sqlite3.connect(base)
    conexion.executescript(
        "DROP TABLE cierres;"
        "CREATE TABLE cierres(id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " fecha TEXT NOT NULL, hora TEXT NOT NULL,"
        " cantidad_ventas INTEGER DEFAULT 0, total_esperado REAL DEFAULT 0,"
        " efectivo_esperado REAL DEFAULT 0, declarado REAL DEFAULT 0,"
        " diferencia REAL DEFAULT 0, sobrante REAL DEFAULT 0,"
        " faltante REAL DEFAULT 0, notas TEXT DEFAULT '', medios TEXT DEFAULT '');"
    )
    conexion.execute(
        "INSERT INTO cierres(fecha, hora, cantidad_ventas, total_esperado,"
        " efectivo_esperado, declarado, diferencia, sobrante, faltante, notas, medios)"
        " VALUES ('2026-01-15', '10:00:00', 1, 1000, 1000, 1000, 0, 0, 0, '',"
        " 'efectivo:1000.00')"
    )
    conexion.commit()
    conexion.close()

    repositorio = CierreRepositorio(base)
    repositorio.inicializar()
    repositorio.agregar(CierreRegistrado(
        HOY, "11:00:00", 1, 1000.0, 1000.0, 1000.0, 0.0, 0.0, 0.0,
        "", "", "admin"))

    cierres = repositorio.listar()

    assert [cierre.usuario for cierre in cierres] == ["", "admin"]


def test_sin_plan_el_vendedor_ve_el_esperado(
        estadisticas, ventana):
    estadisticas.registrar(_venta())

    vista = ventana("vendedor")

    assert "Esperado en el cajón" in vista.ui.lblEsperado.text()
    assert vista.ui.spnEfectivo.value() == 1000.0
    assert not vista.ui.tblMedios.isHidden()
    assert not vista.ui.tblHistorial.isColumnHidden(3)
    assert not vista.ui.tblHistorial.isColumnHidden(4)


def test_un_plan_ciego_no_cambia_el_open(
        estadisticas, ventana):
    estadisticas.registrar(_venta())

    vista = ventana("vendedor")

    assert "Esperado en el cajón" in vista.ui.lblEsperado.text()
    assert vista.ui.spnEfectivo.value() == 1000.0
    assert not vista.ui.tblMedios.isHidden()
    assert not vista.ui.tblHistorial.isColumnHidden(3)
    assert not vista.ui.tblHistorial.isColumnHidden(4)


def test_el_administrador_ve_el_esperado_en_el_open(
        estadisticas, ventana):
    estadisticas.registrar(_venta())

    vista = ventana("administrador", "admin")

    assert "Esperado en el cajón" in vista.ui.lblEsperado.text()
    assert vista.ui.spnEfectivo.value() == 1000.0
    assert not vista.ui.tblMedios.isHidden()
    assert not vista.ui.tblHistorial.isColumnHidden(3)
    assert not vista.ui.tblHistorial.isColumnHidden(4)


def test_el_historial_muestra_quien_cerro(estadisticas, servicio, ventana):
    estadisticas.registrar(_venta())
    servicio.cerrar(HOY, 1000.0, "", "empleado")

    vista = ventana("administrador", "admin")

    assert vista.ui.tblHistorial.item(0, 5).text() == "empleado"


def test_el_historial_muestra_diferencias_en_el_open(
        estadisticas, servicio, ventana):
    estadisticas.registrar(_venta())
    servicio.cerrar(HOY, 900.0, "", "empleado")

    vista = ventana("vendedor")
    tabla = vista.ui.tblHistorial

    assert not tabla.isColumnHidden(3)
    assert not tabla.isColumnHidden(4)
    assert not tabla.isColumnHidden(5)
    assert tabla.item(0, 5).text() == "empleado"


def test_el_mensaje_del_cierre_del_open_revela_la_diferencia(
        estadisticas, servicio, ventana):
    estadisticas.registrar(_venta())
    vista = ventana("vendedor")

    registro = servicio.cerrar(HOY, 900.0, "", "empleado")
    mensaje = vista._mensaje_de_cierre(registro)

    assert "quedó guardado" in mensaje
    assert "diferencia" in mensaje
