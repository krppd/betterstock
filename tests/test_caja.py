from __future__ import annotations

import sqlite3
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from models.caja_movimiento import CajaMovimiento
from models.medio_pago import METODO_EFECTIVO
from models.venta_registrada import PagoVenta, RenglonVenta, VentaRegistrada
from repositories.caja_movimiento_repositorio import CajaMovimientoRepositorio
from repositories.cierre_repositorio import CierreRepositorio
from repositories.codigo_repositorio import CodigoRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.sqlite import conectar, ruta_db
from repositories.turno_repositorio import TurnoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.backup import ServicioBackup
from services.caja import ErrorCaja, ServicioCaja
from services.cierre_caja import ServicioCierre
from services.estadisticas_ventas import EstadisticasVentas
from services.turnos import ServicioTurnos

HOY = date(2026, 11, 7)


class Reloj:
    def __init__(self, ahora: datetime) -> None:
        self.ahora = ahora

    def now(self) -> datetime:
        return self.ahora

    def set(self, ahora: datetime) -> None:
        self.ahora = ahora


@pytest.fixture
def reloj(monkeypatch) -> Reloj:
    reloj = Reloj(datetime(2026, 11, 7, 10, 0, 0))
    monkeypatch.setattr("services.turnos.datetime", SimpleNamespace(now=reloj.now))
    monkeypatch.setattr("services.caja.datetime", SimpleNamespace(now=reloj.now))
    monkeypatch.setattr("views.ventana_cierre.date", SimpleNamespace(today=lambda: HOY))
    return reloj


@pytest.fixture
def base(tmp_path):
    ruta = ruta_db(tmp_path / "datos" / "betterstock.db")
    conectar(ruta).close()
    return ruta


@pytest.fixture
def codigos(base) -> CodigoRepositorio:
    repo = CodigoRepositorio(base)
    repo.inicializar()
    return repo


@pytest.fixture
def ventas(base) -> VentaRepositorio:
    repo = VentaRepositorio(base)
    repo.inicializar()
    return repo


@pytest.fixture
def estadisticas(ventas) -> EstadisticasVentas:
    return EstadisticasVentas(ventas)


@pytest.fixture
def cierres(base) -> CierreRepositorio:
    repo = CierreRepositorio(base)
    repo.inicializar()
    return repo


@pytest.fixture
def turnos_repo(base) -> TurnoRepositorio:
    repo = TurnoRepositorio(base)
    repo.inicializar()
    return repo


@pytest.fixture
def cuenta_repo(base) -> CuentaRepositorio:
    repo = CuentaRepositorio(base)
    repo.inicializar()
    return repo


@pytest.fixture
def caja_repo(base) -> CajaMovimientoRepositorio:
    repo = CajaMovimientoRepositorio(base)
    repo.inicializar()
    return repo


@pytest.fixture
def servicio_cierre(estadisticas, cierres) -> ServicioCierre:
    return ServicioCierre(estadisticas, cierres, backup=ServicioBackup(base=cierres.ruta_archivo))


@pytest.fixture
def servicio_turnos(turnos_repo, ventas, cuenta_repo) -> ServicioTurnos:
    return ServicioTurnos(turnos_repo, ventas, cuenta_repo)


@pytest.fixture
def servicio_caja(caja_repo, servicio_cierre, servicio_turnos, codigos) -> ServicioCaja:
    caja = ServicioCaja(
        caja_repo,
        cierres=servicio_cierre,
        turnos=servicio_turnos,
        codigos=codigos,
    )
    servicio_cierre.caja = caja
    servicio_turnos.caja = caja
    return caja


def _crear_venta_efectivo(ventas: VentaRepositorio, fecha: date, hora: str, total: float) -> VentaRegistrada:
    renglon = RenglonVenta("1001", "Producto", 1, total, total)
    venta = VentaRegistrada(
        fecha,
        hora,
        total,
        [renglon],
        medio_pago=METODO_EFECTIVO,
        pagos=[PagoVenta(METODO_EFECTIVO, total)],
    )
    ventas.agregar(venta)
    return venta


def test_egreso_descuenta_el_efectivo(servicio_cierre, servicio_caja, ventas):
    _crear_venta_efectivo(ventas, HOY, "10:00:00", 1000.0)

    arqueo_inicial = servicio_cierre.arqueo(HOY)
    assert arqueo_inicial.esperado_por_medio.efectivo == 1000.0
    assert arqueo_inicial.efectivo_esperado == 1000.0

    egreso = servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_EGRESO,
        concepto="Flete",
        importe=300.0,
        fecha=HOY,
        hora="10:30:00",
    )
    assert egreso.id_movimiento is not None

    arqueo = servicio_cierre.arqueo(HOY)
    assert arqueo.esperado_por_medio.efectivo == 700.0
    assert arqueo.efectivo_esperado == 700.0
    assert arqueo.egresos == 300.0
    assert arqueo.ventas_efectivo == 1000.0


def test_ingreso_lo_suma(servicio_cierre, servicio_caja, ventas):
    _crear_venta_efectivo(ventas, HOY, "10:00:00", 1000.0)

    ingreso = servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_INGRESO,
        concepto="Cambio extra",
        importe=200.0,
        fecha=HOY,
        hora="10:30:00",
    )
    assert ingreso.id_movimiento is not None

    arqueo = servicio_cierre.arqueo(HOY)
    assert arqueo.esperado_por_medio.efectivo == 1200.0
    assert arqueo.efectivo_esperado == 1200.0
    assert arqueo.ingresos == 200.0


def test_anular_revierte(servicio_cierre, servicio_caja, codigos, ventas):
    _crear_venta_efectivo(ventas, HOY, "10:00:00", 1000.0)
    _, codigo = codigos.generar("Supervisor")

    egreso = servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_EGRESO,
        concepto="Gasto equivocado",
        importe=400.0,
        fecha=HOY,
        hora="10:30:00",
    )

    arqueo = servicio_cierre.arqueo(HOY)
    assert arqueo.esperado_por_medio.efectivo == 600.0
    assert arqueo.egresos == 400.0

    anulado = servicio_caja.anular(
        egreso.id_movimiento,
        codigo=codigo,
        motivo="Se cargó por error",
        anulado_por="admin",
    )
    assert anulado.anulado is True
    assert anulado.motivo_anulacion == "Se cargó por error"

    arqueo_rev = servicio_cierre.arqueo(HOY)
    assert arqueo_rev.esperado_por_medio.efectivo == 1000.0
    assert arqueo_rev.egresos == 0.0


def test_no_se_puede_borrar(servicio_caja, caja_repo, base):
    mov = servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_EGRESO,
        concepto="Insumos",
        importe=150.0,
        fecha=HOY,
        hora="11:00:00",
    )

    with pytest.raises(ErrorCaja):
        servicio_caja.eliminar(mov.id_movimiento)

    with pytest.raises(RuntimeError):
        caja_repo.eliminar(mov.id_movimiento)

    conexion = conectar(base)
    try:
        with pytest.raises((sqlite3.IntegrityError, sqlite3.OperationalError)):
            conexion.execute("DELETE FROM caja_movimientos WHERE id = ?", (mov.id_movimiento,))
    finally:
        conexion.close()

    assert caja_repo.obtener(mov.id_movimiento) is not None


def test_dia_cerrado_bloquea(servicio_cierre, servicio_caja, codigos, ventas):
    _crear_venta_efectivo(ventas, HOY, "10:00:00", 1000.0)
    _, codigo = codigos.generar("Supervisor")

    mov = servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_EGRESO,
        concepto="Retiro previo",
        importe=100.0,
        fecha=HOY,
        hora="11:00:00",
    )

    servicio_cierre.cerrar(HOY, efectivo_declarado=900.0, usuario="admin")
    assert servicio_cierre.ya_cerrado(HOY) is True

    with pytest.raises(ErrorCaja, match="el día está cerrado"):
        servicio_caja.registrar(
            tipo=CajaMovimiento.TIPO_EGRESO,
            concepto="Gasto tarde",
            importe=50.0,
            fecha=HOY,
        )

    with pytest.raises(ErrorCaja, match="el día está cerrado"):
        servicio_caja.anular(
            mov.id_movimiento,
            codigo=codigo,
            motivo="Intento anular cerrado",
        )


def test_turno_descuenta(servicio_turnos, servicio_caja, ventas, reloj):
    reloj.set(datetime(2026, 11, 7, 8, 0, 0))
    turno = servicio_turnos.abrir(fondo_inicial=500.0, usuario="cajero")

    _crear_venta_efectivo(ventas, HOY, "09:00:00", 1000.0)

    servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_EGRESO,
        concepto="Envío",
        importe=200.0,
        fecha=HOY,
        hora="09:30:00",
        turno=turno,
    )

    reloj.set(datetime(2026, 11, 7, 10, 0, 0))
    arqueo = servicio_turnos.arqueo(turno)
    assert arqueo.efectivo_esperado == 1300.0
    assert arqueo.egresos == 200.0
    assert arqueo.efectivo_ventas == 800.0


def test_ui_desglose_en_ventana_cierre(servicio_cierre, servicio_caja, ventas, monkeypatch):
    from PyQt6.QtWidgets import QApplication, QPushButton, QTableWidget, QWidget
    from views.ventana_cierre import VentanaCierre

    app = QApplication.instance() or QApplication([])

    _crear_venta_efectivo(ventas, HOY, "10:00:00", 1000.0)
    servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_EGRESO,
        concepto="Flete",
        importe=150.0,
        fecha=HOY,
        hora="10:30:00",
    )

    ventana = VentanaCierre(servicio_cierre, usuario="admin", permiso="administrador", caja=servicio_caja)
    ventana.ui.dateDia.setDate(HOY)
    ventana.recalcular()

    assert ventana.windowTitle() == "Caja"
    assert ventana.ui.btnCerrarCaja.text() == "Cerrar caja"

    texto = ventana.ui.lblEsperado.text()
    assert "Esperado" in texto
    assert "1.000,00" in texto
    assert "150,00" in texto

    assert ventana.btnEgreso is not None
    assert ventana.btnEgreso.text() == "Egreso de caja"
    assert ventana.btnIngreso is not None
    assert ventana.btnIngreso.text() == "Ingreso de caja"

    assert len(ventana._tarjetas_movimientos) == 1
    tarjeta = ventana._tarjetas_movimientos[0]
    assert "Flete" in tarjeta.lbl_abajo.text()
    assert "-$ 150,00" in tarjeta.lbl_importe.text()
    assert "Activo" in tarjeta.lbl_abajo.text()

    contenedores_movimientos = [
        w for w in ventana.findChildren(QWidget)
        if w.objectName() == "contenedorMovimientosCaja"
    ]
    assert len(contenedores_movimientos) == 1
    assert contenedores_movimientos[0] is ventana.ui.contenedorMovimientos

    contenedores_historial = [
        w for w in ventana.findChildren(QWidget)
        if w.objectName() == "contenedorHistorialCaja"
    ]
    assert len(contenedores_historial) == 1
    assert contenedores_historial[0] is ventana.ui.contenedorHistorial

    botones_egreso = [
        btn for btn in ventana.findChildren(QPushButton)
        if btn.text() == "Egreso de caja"
    ]
    assert len(botones_egreso) == 1
    assert botones_egreso[0] is ventana.btnEgreso


def test_sidebar_boton_dice_caja(tmp_path):
    from PyQt6.QtWidgets import QApplication
    from views.ventana_principal import VentanaPrincipal
    from services.gestor_stock import GestorStock
    from repositories.producto_repositorio import ProductoRepositorio
    from repositories.movimiento_repositorio import MovimientoRepositorio
    from repositories.categoria_repositorio import CategoriaRepositorio

    app = QApplication.instance() or QApplication([])
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
    vp = VentanaPrincipal(stock, None, estadisticas, None, "admin")
    try:
        assert vp.ui.btnCierre.text() == "Caja (F6)"
    finally:
        vp.permitir_cierre()
        vp.close()
        vp.deleteLater()


def test_ui_caja_con_turnos_unifica_movimientos_y_egreso(servicio_turnos, servicio_cierre, servicio_caja, ventas, reloj):
    from PyQt6.QtWidgets import QApplication, QPushButton, QTableWidget, QWidget
    from views.ventana_caja import VentanaCaja

    app = QApplication.instance() or QApplication([])

    reloj.set(datetime(2026, 11, 7, 8, 0, 0))
    turno = servicio_turnos.abrir(fondo_inicial=500.0, usuario="cajero")
    _crear_venta_efectivo(ventas, HOY, "09:00:00", 1000.0)

    servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_EGRESO,
        concepto="Limpieza",
        importe=100.0,
        fecha=HOY,
        hora="09:15:00",
        turno=turno,
    )

    reloj.set(datetime(2026, 11, 7, 10, 0, 0))
    ventana = VentanaCaja(
        servicio_cierre, usuario="cajero", permiso="vendedor",
        turnos=servicio_turnos, caja=servicio_caja,
    )
    ventana.recalcular()

    contenedores_movimientos = [
        w for w in ventana.findChildren(QWidget)
        if w.objectName() == "contenedorMovimientosCaja"
    ]
    assert len(contenedores_movimientos) == 1
    assert contenedores_movimientos[0] is ventana.ui.contenedorMovimientos

    contenedores_historial = [
        w for w in ventana.findChildren(QWidget)
        if w.objectName() == "contenedorHistorialCaja"
    ]
    assert len(contenedores_historial) == 1
    assert contenedores_historial[0] is ventana.ui.contenedorHistorial

    botones_egreso = [
        btn for btn in ventana.findChildren(QPushButton)
        if btn.text() == "Egreso de caja"
    ]
    assert len(botones_egreso) == 1
    assert botones_egreso[0] is ventana.btnEgreso

    botones_ingreso = [
        btn for btn in ventana.findChildren(QPushButton)
        if btn.text() == "Ingreso de caja"
    ]
    assert len(botones_ingreso) == 1
    assert botones_ingreso[0] is ventana.btnIngreso

    botones_cerrar = [
        btn for btn in ventana.findChildren(QPushButton)
        if btn.text() == "Cerrar caja"
    ]
    assert len(botones_cerrar) == 1
    assert botones_cerrar[0] is ventana.ui.btnCerrarCaja

    assert len(ventana._tarjetas_movimientos) == 1
    assert "Limpieza" in ventana._tarjetas_movimientos[0].lbl_abajo.text()
    assert "-$ 100,00" in ventana._tarjetas_movimientos[0].lbl_importe.text()

    assert ventana.seccion_turnos is not None
    assert "Turno #1" in ventana.seccion_turnos.lblEstado.text()
    assert ventana.seccion_turnos.btnAbrir.isEnabled() is False
    assert ventana.seccion_turnos.btnCerrar.isEnabled() is True


def test_cerrar_sin_confirmar_no_guarda(monkeypatch, servicio_cierre, servicio_caja):
    from PyQt6.QtWidgets import QApplication, QDialog
    from views.ventana_caja import VentanaCaja
    from views.dialogo_cerrar_caja import DialogoCerrarCaja

    app = QApplication.instance() or QApplication([])
    ventana = VentanaCaja(servicio_cierre, caja=servicio_caja)
    ventana.ui.dateDia.setDate(HOY)
    ventana.recalcular()

    monkeypatch.setattr(
        DialogoCerrarCaja, "exec", lambda self: QDialog.DialogCode.Rejected
    )

    ventana.cerrar_caja()
    assert not servicio_cierre.ya_cerrado(HOY)


def test_cerrar_confirmando_guarda_con_notas(monkeypatch, servicio_cierre, servicio_caja):
    from PyQt6.QtWidgets import QApplication, QDialog
    from views.ventana_caja import VentanaCaja
    from views.dialogo_cerrar_caja import DialogoCerrarCaja

    app = QApplication.instance() or QApplication([])
    ventana = VentanaCaja(servicio_cierre, caja=servicio_caja)
    ventana.ui.dateDia.setDate(HOY)
    ventana.recalcular()

    def _exec_confirmar(self):
        self._datos = "Todo en orden, sin diferencias"
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(DialogoCerrarCaja, "exec", _exec_confirmar)
    monkeypatch.setattr(ventana, "mostrar_informacion", lambda *a: None)
    monkeypatch.setattr(ventana, "_avisar_backup", lambda: None)
    if hasattr(ventana, "_avisar_cierre"):
        monkeypatch.setattr(ventana, "_avisar_cierre", lambda *a: None)

    ventana.cerrar_caja()
    assert servicio_cierre.ya_cerrado(HOY)
    cierre = servicio_cierre.historial()[-1]
    assert cierre.notas == "Todo en orden, sin diferencias"


def test_dia_cerrado_bloquea_egreso_ingreso_anular(servicio_cierre, servicio_caja):
    from PyQt6.QtWidgets import QApplication
    from views.ventana_caja import VentanaCaja

    app = QApplication.instance() or QApplication([])
    servicio_cierre.cerrar(HOY, efectivo_declarado=0.0, notas="Cierre previo")

    ventana = VentanaCaja(servicio_cierre, caja=servicio_caja)
    ventana.ui.dateDia.setDate(HOY)
    ventana.recalcular()

    assert not ventana.btnEgreso.isEnabled()
    assert not ventana.btnIngreso.isEnabled()
    assert not ventana.btnAnularMovimiento.isEnabled()
    assert not ventana.ui.btnCerrarCaja.isEnabled()

    avisos = []
    ventana.mostrar_advertencia = lambda titulo, msg: avisos.append((titulo, msg))

    ventana.registrar_egreso()
    ventana.registrar_ingreso()
    ventana.cerrar_caja()

    assert len(avisos) == 3
    assert all("cerrad" in msg.lower() for _, msg in avisos)


def test_dialogo_cerrar_caja_ciego_y_admin():
    from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton
    from views.dialogo_cerrar_caja import DialogoCerrarCaja

    app = QApplication.instance() or QApplication([])

    dlg_admin = DialogoCerrarCaja(declarado=100.0, esperado=100.0, ciego=False)
    assert dlg_admin.findChild(QLineEdit, "txtNotasCierre") is not None
    assert dlg_admin.findChild(QPushButton, "btnConfirmarCierre") is not None

    dlg_ciego = DialogoCerrarCaja(declarado=100.0, esperado=100.0, ciego=True)
    textos_label = [lbl.text() for lbl in dlg_ciego.findChildren(QLabel)]
    assert not any("Esperado:" in t for t in textos_label)
    assert not any("Diferencia:" in t for t in textos_label)


def test_click_en_tarjeta_selecciona(servicio_cierre, servicio_caja):
    from PyQt6.QtWidgets import QApplication
    from views.ventana_caja import VentanaCaja

    app = QApplication.instance() or QApplication([])

    servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_EGRESO, concepto="Flete 1", importe=100.0, fecha=HOY, hora="10:00:00"
    )
    servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_INGRESO, concepto="Aporte 2", importe=200.0, fecha=HOY, hora="11:00:00"
    )

    ventana = VentanaCaja(servicio_cierre, caja=servicio_caja)
    ventana.ui.dateDia.setDate(HOY)
    ventana.recalcular()

    assert len(ventana._tarjetas_movimientos) == 2
    t0 = ventana._tarjetas_movimientos[0]
    t1 = ventana._tarjetas_movimientos[1]

    assert not t0.seleccionada
    assert not t1.seleccionada

    t0.click()
    assert t0.seleccionada
    assert not t1.seleccionada
    assert ventana._indice_seleccionado == 0

    t1.click()
    assert not t0.seleccionada
    assert t1.seleccionada
    assert ventana._indice_seleccionado == 1


def test_anular_usa_tarjeta(monkeypatch, servicio_cierre, servicio_caja, codigos):
    from PyQt6.QtWidgets import QApplication, QDialog
    from views.ventana_caja import VentanaCaja
    from views.dialogo_anulacion import DialogoAnulacion

    app = QApplication.instance() or QApplication([])
    mov = servicio_caja.registrar(
        tipo=CajaMovimiento.TIPO_EGRESO, concepto="Gasto extra", importe=350.0, fecha=HOY, hora="12:00:00"
    )

    ventana = VentanaCaja(servicio_cierre, caja=servicio_caja)
    ventana.ui.dateDia.setDate(HOY)
    ventana.recalcular()

    assert len(ventana._tarjetas_movimientos) == 1
    tarjeta = ventana._tarjetas_movimientos[0]
    assert not tarjeta.movimiento.anulado

    avisos = []
    ventana.mostrar_advertencia = lambda t, m: avisos.append((t, m))
    ventana.anular_movimiento()
    assert len(avisos) == 1
    assert "Seleccioná" in avisos[0][1]

    tarjeta.click()
    assert ventana._indice_seleccionado == 0

    _, codigo_plano = codigos.generar("admin")
    monkeypatch.setattr(DialogoAnulacion, "exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(DialogoAnulacion, "resultado", property(lambda self: (codigo_plano, "Error de carga")))

    ventana.anular_movimiento()

    mov_actualizado = servicio_caja._repositorio.obtener(mov.id_movimiento)
    assert mov_actualizado.anulado is True

    assert len(ventana._tarjetas_movimientos) == 1
    tarjeta_anulada = ventana._tarjetas_movimientos[0]
    assert tarjeta_anulada.movimiento.anulado is True
    assert "Anulado" in tarjeta_anulada.lbl_abajo.text()
    assert hasattr(tarjeta_anulada, "lbl_badge")
    assert tarjeta_anulada.lbl_badge.text() == "Anulado"


def test_historial_renderiza_tarjetas(servicio_cierre, servicio_caja):
    from PyQt6.QtWidgets import QApplication, QLabel
    from views.ventana_caja import VentanaCaja
    from views.tarjeta_caja import TarjetaHistorialCierre

    app = QApplication.instance() or QApplication([])

    servicio_cierre.cerrar(HOY, efectivo_declarado=5000.0, notas="Cuadre perfecto", usuario="supervisor")

    ventana = VentanaCaja(servicio_cierre, caja=servicio_caja)
    ventana.recalcular()

    assert len(ventana._tarjetas_historial) == 1
    card = ventana._tarjetas_historial[0]
    assert isinstance(card, TarjetaHistorialCierre)
    assert card.cierre.usuario == "supervisor"
    assert "supervisor" in card.findChildren(QLabel)[0].text()
    assert ventana.ui.contenedorHistorial is not None
    assert ventana.ui.gridHistorial.count() >= 1


def test_paneles_lado_a_lado_y_fusion_resumen(servicio_cierre, servicio_caja, servicio_turnos):
    from PyQt6.QtWidgets import QApplication
    from views.ventana_caja import VentanaCaja

    app = QApplication.instance() or QApplication([])

    ventana = VentanaCaja(
        servicio_cierre, usuario="admin", permiso="administrador",
        turnos=servicio_turnos, caja=servicio_caja,
    )
    ventana.recalcular()

    assert hasattr(ventana.ui, "hlyPaneles")
    assert ventana.ui.hlyPaneles.count() == 2
    assert ventana.ui.scrollMovimientos.maximumHeight() == 300
    assert ventana.ui.scrollHistorial.maximumHeight() == 300
    assert 70 <= ventana.ui.scrollMovimientos.minimumHeight() <= 300
    assert 70 <= ventana.ui.scrollHistorial.minimumHeight() <= 300

    assert hasattr(ventana.ui, "hlyResumen")
    assert ventana.seccion_turnos is not None

    assert hasattr(ventana.ui, "btnToggleMedios")
    assert not ventana.ui.btnToggleMedios.isHidden()
    assert not ventana.ui.tblMedios.isHidden()

    ventana.ui.btnToggleMedios.click()
    assert ventana.ui.tblMedios.isHidden()
    assert "Medios de pago ▾" in ventana.ui.btnToggleMedios.text()

    ventana.ui.btnToggleMedios.click()
    assert not ventana.ui.tblMedios.isHidden()
    assert "Ocultar medios ▴" in ventana.ui.btnToggleMedios.text()

    ventana_vendedor = VentanaCaja(
        servicio_cierre, usuario="empleado", permiso="vendedor",
        turnos=servicio_turnos, caja=servicio_caja,
    )
    ventana_vendedor.recalcular()
    if getattr(ventana_vendedor, "_ciego", False):
        assert ventana_vendedor.ui.btnToggleMedios.isHidden()
        assert ventana_vendedor.ui.tblMedios.isHidden()


def test_historial_muestra_ultimos_cuatro(servicio_cierre, servicio_caja):
    from datetime import timedelta
    from PyQt6.QtWidgets import QApplication
    from views.ventana_caja import VentanaCaja

    app = QApplication.instance() or QApplication([])
    for i in range(6):
        dia = HOY - timedelta(days=i)
        servicio_cierre.cerrar(dia, efectivo_declarado=1000.0 * (i + 1), usuario=f"user_{i}")

    ventana = VentanaCaja(servicio_cierre, caja=servicio_caja)
    ventana.recalcular()

    assert len(ventana._tarjetas_historial) == 4


def test_alturas_autoajustables_vacio_vs_many(servicio_cierre, servicio_caja):
    from PyQt6.QtWidgets import QApplication
    from views.ventana_caja import VentanaCaja

    app = QApplication.instance() or QApplication([])

    v0 = VentanaCaja(servicio_cierre, caja=servicio_caja)
    v0.ui.dateDia.setDate(HOY)
    v0.recalcular()
    assert v0.ui.scrollMovimientos.minimumHeight() == 70
    assert v0.ui.scrollHistorial.minimumHeight() == 70

    servicio_caja.registrar(tipo=CajaMovimiento.TIPO_EGRESO, concepto="A", importe=100.0, fecha=HOY, hora="10:00:00")
    v1 = VentanaCaja(servicio_cierre, caja=servicio_caja)
    v1.ui.dateDia.setDate(HOY)
    v1.recalcular()
    assert 70 < v1.ui.scrollMovimientos.minimumHeight() < 300

    for i in range(9):
        servicio_caja.registrar(tipo=CajaMovimiento.TIPO_EGRESO, concepto=f"B{i}", importe=100.0, fecha=HOY, hora="11:00:00")
    v2 = VentanaCaja(servicio_cierre, caja=servicio_caja)
    v2.ui.dateDia.setDate(HOY)
    v2.recalcular()
    assert v2.ui.scrollMovimientos.minimumHeight() == 300
    assert v2.ui.scrollMovimientos.maximumHeight() == 300

