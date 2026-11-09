from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from PyQt6.QtWidgets import QApplication, QDialog

from models.cliente import Cliente
from models.medio_pago import METODO_DEBITO, METODO_EFECTIVO, METODO_FIADO, METODO_MP
from models.producto import Producto
from models.usuario import Usuario
from models.venta import Venta
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cierre_repositorio import CierreRepositorio
from repositories.cliente_repositorio import ClienteRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.backup import ServicioBackup
from services.cierre_caja import ServicioCierre
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from ui.manual.cobro_ui import MAXIMO_MONTO
from utils.formato import a_decimal, diferencia
from views.formulario_cliente import FormularioCliente
from views.formulario_producto import FormularioProducto
from views.ventana_cobro import VentanaCobro
from views.ventana_cierre import VentanaCierre

HOY = date(2026, 10, 19)
PRECIO_ENORME = 999_999_999
PRECIO_NORMAL = 999_999
STOCK_MAXIMO = 999_999
LIMITE_ENORME = 999_999_999
LIMITE_NORMAL = 500_000
TOTAL_ENORME = 500_000_000


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def armar_stock(tmp_path) -> GestorStock:
    stock = GestorStock(
        ProductoRepositorio(tmp_path / "productos.csv"),
        MovimientoRepositorio(tmp_path / "movimientos.csv"),
        CategoriaRepositorio(tmp_path / "categorias.csv"))
    stock.inicializar()
    return stock


def armar_fiado(tmp_path) -> GestorFiado:
    fiado = GestorFiado(
        ClienteRepositorio(tmp_path / "clientes.csv"),
        CuentaRepositorio(tmp_path / "cuenta.csv"))
    fiado.inicializar()
    return fiado


def armar_ventas(tmp_path, stock: GestorStock, fiado: GestorFiado | None = None):
    estadisticas = EstadisticasVentas(VentaRepositorio(tmp_path / "ventas.csv"))
    estadisticas.inicializar()
    return GestorVentas(stock, estadisticas, fiado), estadisticas


def venta_enorme(tmp_path, stock: GestorStock):
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Bobina de acero",
        precio_costo=40_000_000, precio_venta=50_000_000,
        stock_actual=100, stock_minimo=1))
    ventas, estadisticas = armar_ventas(tmp_path, stock)
    for _ in range(10):
        ventas.agregar_producto("1001")
    return ventas, estadisticas


def producto_enorme() -> Producto:
    return Producto.from_dict({
        "codigo": "1001", "nombre": "Bobina de acero",
        "precio_costo": "40000000", "precio_venta": str(PRECIO_ENORME),
        "stock_actual": "10", "stock_minimo": "1", "alicuota_iva": "21",
        "precio_oferta": ""})


def test_el_precio_de_venta_no_puede_superar_el_maximo():
    with pytest.raises(ValueError) as error:
        Producto(codigo="1001", nombre="Tornillo", precio_venta=PRECIO_ENORME)
    assert "99.999.999,99" in str(error.value)
    assert "precio de venta" in str(error.value)


def test_el_precio_de_costo_no_puede_superar_el_maximo():
    with pytest.raises(ValueError) as error:
        Producto(codigo="1001", nombre="Tornillo", precio_costo=PRECIO_ENORME)
    assert "99.999.999,99" in str(error.value)


def test_un_producto_con_precio_enorme_no_se_guarda_truncado(tmp_path):
    stock = armar_stock(tmp_path)
    producto = producto_enorme()
    assert producto.precio_venta == PRECIO_ENORME

    with pytest.raises(ValueError, match="99.999.999,99"):
        stock.guardar_producto(producto)

    assert stock.listar_productos() == []


def test_un_producto_con_precio_normal_se_guarda_completo(tmp_path):
    stock = armar_stock(tmp_path)
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Tornillo", precio_venta=PRECIO_NORMAL,
        stock_actual=10, stock_minimo=1))

    guardado = stock.buscar_producto("1001")
    assert guardado is not None
    assert guardado.precio_venta == PRECIO_NORMAL


def test_el_stock_no_puede_superar_el_maximo():
    with pytest.raises(ValueError) as error:
        Producto(codigo="1001", nombre="Tornillo", stock_actual=STOCK_MAXIMO + 1)
    assert "999.999" in str(error.value)
    assert "stock actual" in str(error.value)


def test_un_stock_maximo_se_guarda_completo(tmp_path):
    stock = armar_stock(tmp_path)
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Tornillo", precio_venta=1000,
        stock_actual=STOCK_MAXIMO, stock_minimo=1))

    guardado = stock.buscar_producto("1001")
    assert guardado is not None
    assert guardado.stock_actual == STOCK_MAXIMO


def test_el_limite_de_credito_no_puede_superar_el_maximo(tmp_path):
    fiado = armar_fiado(tmp_path)

    with pytest.raises(ValueError) as error:
        fiado.guardar_cliente("Juan", limite=LIMITE_ENORME)
    assert "99.999.999,00" in str(error.value)

    assert fiado.listar_clientes() == []


def test_un_limite_de_credito_normal_se_guarda_completo(tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan", limite=LIMITE_NORMAL)

    guardado = fiado.buscar_cliente(cliente.identificador)
    assert guardado is not None
    assert guardado.limite == LIMITE_NORMAL


def test_el_formulario_de_producto_avisa_y_no_pisa_el_precio(aplicacion, tmp_path):
    stock = armar_stock(tmp_path)
    ProductoRepositorio(tmp_path / "productos.csv").guardar(producto_enorme())

    formulario = FormularioProducto(stock, stock.buscar_producto("1001"))
    avisos: list[tuple[str, str]] = []
    formulario.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))

    assert formulario.ui.spnPrecioVenta.value() == PRECIO_ENORME

    formulario.guardar_producto()

    assert len(avisos) == 1
    assert "99.999.999,99" in avisos[0][1]
    assert formulario.result() != QDialog.DialogCode.Accepted
    guardado = stock.buscar_producto("1001")
    assert guardado is not None
    assert guardado.precio_venta == PRECIO_ENORME


def test_el_formulario_de_cliente_avisa_y_no_pisa_el_limite(aplicacion, tmp_path):
    fiado = armar_fiado(tmp_path)
    cliente = Cliente.from_dict({
        "codigo": "1", "nombre": "Juan", "telefono": "123",
        "limite": str(LIMITE_ENORME), "activo": "1"})
    ClienteRepositorio(tmp_path / "clientes.csv").actualizar(cliente)

    formulario = FormularioCliente(fiado, cliente)
    avisos: list[tuple[str, str]] = []
    formulario.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))

    assert formulario.spnLimite.value() == LIMITE_ENORME

    formulario.guardar()

    assert len(avisos) == 1
    assert "99.999.999,00" in avisos[0][1]
    assert formulario.result() != QDialog.DialogCode.Accepted
    guardado = fiado.buscar_cliente("1")
    assert guardado is not None
    assert guardado.limite == LIMITE_ENORME


def test_el_cobro_admite_un_total_enorme_sin_recortar(aplicacion, tmp_path):
    stock = armar_stock(tmp_path)
    ventas, _ = venta_enorme(tmp_path, stock)
    assert ventas.venta.total == TOTAL_ENORME

    cobro = VentanaCobro(ventas.venta)

    assert cobro.total_cobrar == TOTAL_ENORME
    assert cobro.ui.spnMonto.value() == TOTAL_ENORME
    assert MAXIMO_MONTO > TOTAL_ENORME


def test_el_cobro_de_un_total_enorme_da_el_vuelto_correcto(aplicacion, tmp_path):
    stock = armar_stock(tmp_path)
    ventas, _ = venta_enorme(tmp_path, stock)

    cobro = VentanaCobro(ventas.venta)
    cobro.ui.spnMonto.setValue(TOTAL_ENORME + 1234.56)

    assert cobro.vuelto == 1234.56
    assert cobro.faltante == 0


def test_el_cobro_de_una_venta_de_499_millones_no_se_recorta(aplicacion, tmp_path):
    stock = armar_stock(tmp_path)
    venta = Venta()
    producto = Producto(
        codigo="1001", nombre="Equipo industrial", precio_venta=99_999_999.99)
    for _ in range(5000):
        venta.agregar_unidad(producto)

    cobro = VentanaCobro(venta)

    assert cobro.total_cobrar == 499_999_999_950
    assert cobro.ui.spnMonto.value() == 499_999_999_950
    cobro.ui.spnMonto.setValue(499_999_999_950 + 100)
    assert cobro.vuelto == 100


def test_el_cobro_con_monto_menor_al_total_avisa_y_no_cobra(aplicacion, tmp_path):
    stock = armar_stock(tmp_path)
    ventas, _ = venta_enorme(tmp_path, stock)

    cobro = VentanaCobro(ventas.venta)
    avisos: list[tuple[str, str]] = []
    cobro.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))
    cobro.ui.spnMonto.setValue(TOTAL_ENORME - 1000)

    assert cobro.faltante == 1000

    cobro.aceptar()

    assert len(avisos) == 1
    assert "Faltan" in avisos[0][1]
    assert "1.000,00" in avisos[0][1]
    assert "no se cobró" in avisos[0][1]
    assert cobro.result() != QDialog.DialogCode.Accepted


def test_el_cobro_con_mercadopago_cobra_el_total_entero(aplicacion, tmp_path):
    stock = armar_stock(tmp_path)
    ventas, _ = venta_enorme(tmp_path, stock)

    cobro = VentanaCobro(ventas.venta)
    cobro.ui.cmbMetodo.setCurrentIndex(cobro.ui.cmbMetodo.findData(METODO_MP))

    assert cobro.metodo == METODO_MP
    assert cobro.monto == TOTAL_ENORME
    assert not cobro.ui.spnMonto.isEnabled()


def test_el_cobro_con_datos_de_tarjeta_cobra_el_total_entero(aplicacion, tmp_path):
    stock = armar_stock(tmp_path)
    ventas, _ = venta_enorme(tmp_path, stock)

    cobro = VentanaCobro(ventas.venta)
    cobro.ui.cmbMetodo.setCurrentIndex(cobro.ui.cmbMetodo.findData(METODO_DEBITO))
    cobro.ui.txtDatos.setText("1234")

    assert cobro.metodo == METODO_DEBITO
    assert cobro.monto == TOTAL_ENORME
    assert cobro.datos == "1234"
    assert cobro.ui.txtDatos.isVisibleTo(cobro)


def test_el_cobro_fiado_no_pasa_del_tope_del_cliente(aplicacion, tmp_path):
    stock = armar_stock(tmp_path)
    fiado = armar_fiado(tmp_path)
    cliente = fiado.guardar_cliente("Juan", limite=1000)
    ventas, _ = venta_enorme(tmp_path, stock)

    cobro = VentanaCobro(ventas.venta, fiado)
    cobro.ui.cmbMetodo.setCurrentIndex(cobro.ui.cmbMetodo.findData(METODO_FIADO))
    cobro.ui.cmbCliente.setCurrentIndex(
        cobro.ui.cmbCliente.findData(cliente.identificador))
    avisos: list[tuple[str, str]] = []
    cobro.mostrar_advertencia = lambda titulo, mensaje: avisos.append((titulo, mensaje))

    assert cobro.metodo == METODO_FIADO
    assert cobro.monto == TOTAL_ENORME
    assert cobro.cliente == cliente.identificador

    cobro.aceptar()

    assert len(avisos) == 1
    assert "límite" in avisos[0][1]
    assert cobro.result() != QDialog.DialogCode.Accepted


def test_el_cierre_con_montos_enormes_cuadra(aplicacion, tmp_path):
    stock = armar_stock(tmp_path)
    fiado = armar_fiado(tmp_path)
    ventas, estadisticas = venta_enorme(tmp_path, stock)
    ventas.cobrar(HOY, monto_recibido=TOTAL_ENORME, medio_pago=METODO_EFECTIVO)
    backup = ServicioBackup(tmp_path / "betterstock.db", tmp_path / "backups")
    cierre = ServicioCierre(
        estadisticas, CierreRepositorio(tmp_path / "cierres.csv"), fiado, backup)
    cierre.inicializar()

    arqueo = cierre.arqueo(HOY)
    assert arqueo.esperado_por_medio.efectivo == TOTAL_ENORME

    registro = cierre.cerrar(HOY, TOTAL_ENORME)
    assert registro.diferencia == 0
    assert registro.cuadra

    ventana = VentanaCierre(cierre, permiso=Usuario.PERMISO_ADMIN)
    ventana.ui.dateDia.setDate(HOY)
    ventana.recalcular()

    assert ventana.ui.spnEfectivo.value() == TOTAL_ENORME
    assert "Cuadra" in ventana.ui.lblDiferencia.text()

    ventana.ui.spnEfectivo.setValue(TOTAL_ENORME - 0.5)
    assert "Faltante" in ventana.ui.lblDiferencia.text()
    assert "0,50" in ventana.ui.lblDiferencia.text()


def test_la_diferencia_de_montos_es_exacta():
    assert diferencia(TOTAL_ENORME, TOTAL_ENORME) == Decimal("0.00")
    assert diferencia(TOTAL_ENORME - 0.5, TOTAL_ENORME) == Decimal("-0.50")
    assert diferencia(0.1, 0.2) == Decimal("-0.10")
    assert a_decimal(0.1) + a_decimal(0.2) == Decimal("0.30")
    assert a_decimal(1_000_000_000.01) == Decimal("1000000000.01")


def test_los_spinboxes_no_recortan_montos_grandes(aplicacion):
    from ui.generated.formulario_Producto_ui import Ui_Dialog

    ventana = QDialog()
    ui = Ui_Dialog()
    ui.setupUi(ventana)

    assert ui.spnPrecioVenta.maximum() >= PRECIO_ENORME
    assert ui.spnPrecioCosto.maximum() >= PRECIO_ENORME
    assert ui.spnPrecioOferta.maximum() >= PRECIO_ENORME
    assert ui.spnStock.maximum() >= STOCK_MAXIMO
    assert ui.spnStockMinimo.maximum() >= STOCK_MAXIMO
    assert MAXIMO_MONTO > TOTAL_ENORME
