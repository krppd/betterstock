from __future__ import annotations

from datetime import date
import pytest
from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QApplication

from models.venta_registrada import RenglonVenta, VentaRegistrada
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cliente_repositorio import ClienteRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.sqlite import conectar, ruta_db
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from views.ventana_dashboard import DashboardPrincipalWidget, WorkerCargaDashboard


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def base_datos(tmp_path):
    base = ruta_db(tmp_path / "datos" / "betterstock.db")
    conectar(base).close()

    repo_stock = ProductoRepositorio(base)
    repo_movs = MovimientoRepositorio(base)
    repo_cats = CategoriaRepositorio(base)
    repo_ventas = VentaRepositorio(base)
    repo_clientes = ClienteRepositorio(base)
    repo_cuentas = CuentaRepositorio(base)

    stock = GestorStock(repo_stock, repo_movs, repo_cats)
    stock.inicializar()
    estadisticas = EstadisticasVentas(repo_ventas)
    estadisticas.inicializar()
    fiado = GestorFiado(repo_clientes, repo_cuentas)
    fiado.inicializar()

    return stock, estadisticas, fiado, repo_ventas


def test_worker_carga_dashboard_ejecuta_consultas(aplicacion, base_datos):
    stock, estadisticas, fiado, repo_ventas = base_datos
    renglones = [RenglonVenta("P1", "Yerba Mate", 2.0, 750.0)]
    repo_ventas.agregar(
        VentaRegistrada(
            fecha=date.today(),
            hora="10:00",
            total=1500.0,
            detalle=renglones,
            estado=VentaRegistrada.ESTADO_ACTIVA,
            medio_pago="Efectivo",
        )
    )

    worker = WorkerCargaDashboard(1, "hoy", estadisticas, stock, fiado)
    resultado = []
    worker.signals.datos_listos.connect(resultado.append)
    worker.run()

    assert len(resultado) == 1
    datos = resultado[0]
    assert datos["id_carga"] == 1
    assert datos["total_ventas"] == 1500.0
    assert datos["cant_pedidos"] == 1
    assert len(datos["filas_ventas"]) == 1
    assert len(datos["filas_top"]) == 1


def test_dashboard_recargar_datos_asincrono(aplicacion, base_datos):
    stock, estadisticas, fiado, repo_ventas = base_datos
    renglones = [RenglonVenta("P2", "Café Molido", 1.0, 2000.0)]
    repo_ventas.agregar(
        VentaRegistrada(
            fecha=date.today(),
            hora="11:30",
            total=2000.0,
            detalle=renglones,
            estado=VentaRegistrada.ESTADO_ACTIVA,
            medio_pago="Efectivo",
        )
    )

    vista = DashboardPrincipalWidget(stock, estadisticas, fiado)
    QThreadPool.globalInstance().waitForDone(3000)
    aplicacion.processEvents()

    assert "2.000" in vista.kpi_ventas.lbl_valor.text() and ",00" in vista.kpi_ventas.lbl_valor.text()
    assert "1" in vista.kpi_pedidos.lbl_valor.text()
    assert len(vista.tablaVentas._filas) == 1
    assert len(vista.tablaTop._filas) == 1


def test_dashboard_senales_ver_mas(aplicacion, base_datos):
    stock, estadisticas, fiado, _ = base_datos
    vista = DashboardPrincipalWidget(stock, estadisticas, fiado)

    recibidas = []
    vista.solicitar_ver_ventas.connect(lambda: recibidas.append("ventas"))
    vista.solicitar_ver_ranking.connect(lambda: recibidas.append("ranking"))

    vista.solicitar_ver_ventas.emit()
    vista.solicitar_ver_ranking.emit()

    assert recibidas == ["ventas", "ranking"]

