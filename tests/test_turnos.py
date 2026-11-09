from __future__ import annotations

import sqlite3
from datetime import date, datetime
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QApplication, QDialog

from models.cierre import ResumenMedios
from models.medio_pago import METODO_EFECTIVO
from models.movimiento_cuenta import MovimientoCuenta
from models.usuario import Usuario
from models.venta_registrada import PagoVenta, RenglonVenta, VentaRegistrada
from repositories.cierre_repositorio import CierreRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.sqlite import conectar, ruta_db
from repositories.turno_repositorio import TurnoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.backup import ServicioBackup
from services.cierre_caja import ServicioCierre
from services.estadisticas_ventas import EstadisticasVentas
from services.turnos import ErrorTurno, ServicioTurnos
from views.seccion_turnos import SeccionTurnos
from views.ventana_cierre import VentanaCierre

HOY = date(2026, 11, 6)


class Reloj:
    def __init__(self, ahora: datetime) -> None:
        self.ahora = ahora

    def now(self) -> datetime:
        return self.ahora

    def set(self, ahora: datetime) -> None:
        self.ahora = ahora


@pytest.fixture
def reloj(monkeypatch) -> Reloj:
    reloj = Reloj(datetime(2026, 11, 6, 8, 0, 0))
    monkeypatch.setattr(
        "services.turnos.datetime", SimpleNamespace(now=reloj.now))
    return reloj


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
def ventas(base) -> VentaRepositorio:
    repositorio = VentaRepositorio(base)
    repositorio.inicializar()
    return repositorio


@pytest.fixture
def cuenta(base) -> CuentaRepositorio:
    repositorio = CuentaRepositorio(base)
    repositorio.inicializar()
    return repositorio


@pytest.fixture
def turnos_repo(base) -> TurnoRepositorio:
    repositorio = TurnoRepositorio(base)
    repositorio.inicializar()
    return repositorio


@pytest.fixture
def servicio(turnos_repo, ventas, cuenta) -> ServicioTurnos:
    servicio = ServicioTurnos(turnos_repo, ventas, cuenta)
    servicio.inicializar()
    return servicio


def _venta(fecha: date, hora: str, total: float,
           efectivo: bool = True, anulada: bool = False) -> VentaRegistrada:
    renglon = RenglonVenta("P1", "Producto de prueba", 1, total)
    if efectivo:
        venta = VentaRegistrada(
            fecha, hora, total, [renglon],
            pagos=(PagoVenta(METODO_EFECTIVO, total),))
    else:
        venta = VentaRegistrada(
            fecha, hora, total, [renglon], medio_pago="transferencia")
    if anulada:
        venta.anular()
    return venta


def test_abrir_deja_el_turno_abierto(servicio, reloj):
    turno = servicio.abrir(1500, "empleado", "mañana")

    assert turno.id_turno == 1
    assert turno.abierto
    assert servicio.abierto().usuario_apertura == "empleado"
    assert servicio.abierto().fondo_inicial == 1500

    with pytest.raises(ErrorTurno, match="Ya hay un turno abierto"):
        servicio.abrir(100, "maria")


def test_arqueo_cuenta_fondo_ventas_y_fiado_en_efectivo(servicio, ventas, cuenta,
                                                        reloj):
    servicio.abrir(1000, "empleado")
    ventas.agregar(_venta(HOY, "09:00:00", 800))
    ventas.agregar(_venta(HOY, "10:00:00", 500, efectivo=False))
    ventas.agregar(_venta(HOY, "11:00:00", 900, anulada=True))
    cuenta.agregar(MovimientoCuenta(
        HOY, "1", "pago", 200, medio="efectivo", hora="10:30:00"))
    cuenta.agregar(MovimientoCuenta(
        HOY, "1", "pago", 300, medio="transferencia", hora="10:45:00"))

    reloj.set(datetime(2026, 11, 6, 18, 0, 0))
    arqueo = servicio.arqueo()

    assert arqueo.cantidad_ventas == 2
    assert arqueo.efectivo_ventas == 1000.0
    assert arqueo.efectivo_esperado == 2000.0
    assert arqueo.total_esperado == 2800.0


def test_cerrar_guarda_la_diferencia_y_cierra(servicio, reloj):
    servicio.abrir(1000, "empleado")
    reloj.set(datetime(2026, 11, 6, 18, 0, 0))

    cerrado = servicio.cerrar(900, "empleado", Usuario.PERMISO_VENDEDOR)

    assert cerrado.cerrado
    assert cerrado.diferencia == -100
    assert cerrado.faltante == 100
    assert cerrado.sobrante == 0
    assert servicio.abierto() is None
    assert servicio.sugerir_fondo() == 900
    assert servicio.historial()[0].efectivo_esperado == 1000.0


def test_solo_quien_abrio_o_un_admin_puede_cerrar(servicio, reloj):
    servicio.abrir(1000, "empleado")

    with pytest.raises(ErrorTurno, match="administrador"):
        servicio.cerrar(1000, "maria", Usuario.PERMISO_VENDEDOR)

    cerrado = servicio.cerrar(1000, "maria", Usuario.PERMISO_ADMIN)
    assert cerrado.usuario_cierre == "maria"


def test_los_turnos_de_distintos_dias_no_se_pisan(servicio, ventas, reloj):
    reloj.set(datetime(2026, 11, 5, 8, 0, 0))
    servicio.abrir(1000, "empleado")
    ventas.agregar(_venta(date(2026, 11, 5), "09:00:00", 700))
    reloj.set(datetime(2026, 11, 5, 10, 0, 0))
    servicio.cerrar(1700, "empleado", Usuario.PERMISO_ADMIN)

    reloj.set(datetime(2026, 11, 6, 8, 0, 0))
    servicio.abrir(1700, "empleado")
    ventas.agregar(_venta(HOY, "09:30:00", 400))
    reloj.set(datetime(2026, 11, 6, 10, 0, 0))

    arqueo = servicio.arqueo()

    assert arqueo.cantidad_ventas == 1
    assert arqueo.efectivo_esperado == 2100.0


def test_un_movimiento_sin_hora_no_entra_en_el_turno(servicio, cuenta, reloj):
    servicio.abrir(1000, "empleado")
    cuenta.agregar(MovimientoCuenta(
        HOY, "1", "pago", 400, medio="efectivo", hora=""))
    reloj.set(datetime(2026, 11, 6, 18, 0, 0))

    arqueo = servicio.arqueo()

    assert arqueo.efectivo_esperado == 1000.0


def test_una_venta_fiada_no_es_efectivo(servicio, ventas, reloj):
    servicio.abrir(1000, "empleado")
    ventas.agregar(VentaRegistrada(
        HOY, "09:00:00", 500, [RenglonVenta("P1", "Producto", 1, 500)],
        pagos=(PagoVenta("fiado", 500),)))
    reloj.set(datetime(2026, 11, 6, 18, 0, 0))

    arqueo = servicio.arqueo()

    assert arqueo.efectivo_ventas == 0.0
    assert arqueo.total_esperado == 1500.0


def test_un_turno_cerrado_no_se_vuelve_a_cerrar(servicio, reloj):
    servicio.abrir(1000, "empleado")
    reloj.set(datetime(2026, 11, 6, 18, 0, 0))
    servicio.cerrar(1000, "empleado", Usuario.PERMISO_ADMIN)

    with pytest.raises(ErrorTurno, match="No hay un turno abierto"):
        servicio.cerrar(1000, "empleado", Usuario.PERMISO_ADMIN)


def test_la_base_vieja_gana_la_columna_hora(tmp_path):
    base = ruta_db(tmp_path / "viejo.db")
    conexion = sqlite3.connect(base)
    conexion.executescript(
        "DROP TABLE IF EXISTS cuenta_movimientos;"
        "CREATE TABLE cuenta_movimientos("
        " id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL,"
        " cliente TEXT NOT NULL, tipo TEXT NOT NULL, importe REAL NOT NULL,"
        " detalle TEXT DEFAULT '', medio TEXT DEFAULT '', usuario TEXT DEFAULT '');"
        "INSERT INTO cuenta_movimientos(fecha, cliente, tipo, importe,"
        " detalle, medio, usuario)"
        " VALUES('2026-11-06', '1', 'pago', 100, 'Pago', 'efectivo', 'empleado');")
    conexion.close()

    conectar(base).close()

    with sqlite3.connect(base) as conexion:
        columnas = [fila[1] for fila in conexion.execute(
            "PRAGMA table_info(cuenta_movimientos)")]
    assert "hora" in columnas


def test_seccion_turnos_abre_y_cierra(servicio, aplicacion, monkeypatch):
    seccion = SeccionTurnos(servicio, "empleado", Usuario.PERMISO_ADMIN)

    assert seccion.btnAbrir.isEnabled()
    assert not seccion.btnCerrar.isEnabled()

    monkeypatch.setattr(
        "views.seccion_turnos.DialogoAbrirTurno.exec",
        lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(
        "views.seccion_turnos.DialogoAbrirTurno.datos",
        property(lambda self: (1500.0, "mañana")))

    seccion.abrir()

    assert servicio.abierto() is not None
    assert not seccion.btnAbrir.isEnabled()
    assert seccion.btnCerrar.isEnabled()
    assert not seccion.lblEstado.text() == ""

    monkeypatch.setattr(
        "views.seccion_turnos.DialogoCerrarTurno.exec",
        lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(
        "views.seccion_turnos.DialogoCerrarTurno.datos",
        property(lambda self: (1500.0, "")))

    seccion.cerrar()

    assert servicio.abierto() is None
    assert seccion.tabla.rowCount() == 1
    seccion.deleteLater()


def test_ventana_cierre_incluye_la_seccion_de_turnos(
        servicio, base, aplicacion, tmp_path):
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    cierre = ServicioCierre(
        estadisticas, CierreRepositorio(base),
        backup=ServicioBackup(base, tmp_path / "backups"))
    cierre.inicializar()
    vista = VentanaCierre(
        cierre, "empleado", Usuario.PERMISO_ADMIN, turnos=servicio)

    assert vista.seccion_turnos is not None
    assert vista.seccion_turnos.tabla.rowCount() == 0

    vista.deleteLater()


def test_arqueo_devuelve_medios(servicio, ventas, reloj):
    servicio.abrir(1000, "empleado")
    ventas.agregar(_venta(HOY, "09:00:00", 800))
    reloj.set(datetime(2026, 11, 6, 18, 0, 0))

    arqueo = servicio.arqueo()

    assert isinstance(arqueo.esperado_por_medio, ResumenMedios)
    assert arqueo.esperado_por_medio.efectivo == 800.0
