from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from PyQt6.QtTest import QTest
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

from models.medio_pago import METODO_EFECTIVO, METODO_MP, METODO_TRANSFERENCIA
from models.producto import Producto
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cliente_repositorio import ClienteRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.usuario_repositorio import UsuarioRepositorio
from repositories.venta_repositorio import VentaRepositorio
from models.usuario import Usuario
from services.autenticacion import Autenticacion
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_comercio import GestorComercio
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from ui.estilos import aplicar_tema
from ui.widgets.boton_rodante import BotonRodante
from ui.widgets.etiqueta_rodante import EtiquetaRodante
from views.ventana_alertas import VentanaAlertas
from views.ventana_clientes import VentanaClientes
from views.ventana_cobro import VentanaCobro
from views.ventana_consulta import VentanaConsulta
from views.ventana_detalle_venta import VentanaDetalleVenta
from views.ventana_estadisticas import VentanaEstadisticas
from views.ventana_login import VentanaLogin
from views.ventana_movimientos import VentanaMovimientos
from views.ventana_principal import VentanaPrincipal
from views.ventana_productos import VentanaProductos
from views.ventana_reportes import VentanaReportes
from views.ventana_ventas import VentanaVentas

TAMANO_VENTANA = (1000, 700)
MARGEN_BOTON = 16

PRODUCTOS = (
    Producto(codigo="1001", nombre="Tomate perita", categoria="Verdura",
             unidad_medida="kg", precio_costo=850.0, precio_venta=1450.0,
             stock_actual=48, stock_minimo=10),
    Producto(codigo="1002", nombre="Papa blanca", categoria="Verdura",
             unidad_medida="kg", precio_costo=600.0, precio_venta=1100.0,
             stock_actual=120, stock_minimo=25),
    Producto(codigo="1003", nombre="Leche entera 1L", categoria="Lácteos",
             unidad_medida="u", precio_costo=1200.0, precio_venta=2100.5,
             stock_actual=6, stock_minimo=12),
    Producto(codigo="1004", nombre="Pan de molde", categoria="Panadería",
             unidad_medida="u", precio_costo=2100.0, precio_venta=3800.0,
             stock_actual=24, stock_minimo=5),
)


def _ambiente(carpeta: Path):
    base = carpeta / "verificacion.db"
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base),
    )
    stock.inicializar()
    for producto in PRODUCTOS:
        stock.guardar_producto(producto)
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    fiado = GestorFiado(ClienteRepositorio(base), CuentaRepositorio(base))
    fiado.inicializar()
    for nombre, telefono, limite in (
        ("María González", "1166666666", 50000.0),
        ("Juan Pérez", "1177777777", 25000.0),
    ):
        fiado.guardar_cliente(nombre, telefono, limite)
    autenticacion = Autenticacion(UsuarioRepositorio(base))
    autenticacion.inicializar()
    autenticacion.crear_usuario(
        "captura", "clave-captura", Usuario.PERMISO_ADMIN)
    comercio = GestorComercio.__new__(GestorComercio)
    return stock, estadisticas, fiado, autenticacion, comercio


def _ventas_historicas(stock: GestorStock, estadisticas: EstadisticasVentas,
                       fiado: GestorFiado) -> tuple[GestorVentas, object]:
    hoy = date.today()
    historial = (
        (hoy, "1001", 2, METODO_EFECTIVO),
        (hoy, "1004", 1, METODO_EFECTIVO),
        (hoy - timedelta(days=1), "1002", 3, METODO_TRANSFERENCIA),
        (hoy - timedelta(days=2), "1003", 2, METODO_MP),
    )
    comprobante = None
    for fecha, codigo, cantidad, medio in historial:
        ventas = GestorVentas(stock, estadisticas, fiado)
        ventas.agregar_producto(codigo)
        ventas.venta.items[0].cantidad = cantidad
        comprobante = ventas.cobrar(fecha, medio_pago=medio, usuario="cajero")
    return GestorVentas(stock, estadisticas, fiado), comprobante


def _ancho_disponible(widget: QWidget) -> int:
    if isinstance(widget, BotonRodante):
        icono = (widget.iconSize().width() + 4) if not widget.icon().isNull() else 0
        return widget.width() - icono - MARGEN_BOTON
    return widget.width()


def _revisar_etiqueta(etiqueta: QLabel, problemas: list[str], detalle: list[str]) -> None:
    if not etiqueta.isVisible() or etiqueta.wordWrap() or etiqueta.__class__.__name__ == "AvatarWidget":
        return
    texto = etiqueta.text().strip()
    if not texto or "<" in texto and ">" in texto:
        return
    ancho = QFontMetrics(etiqueta.font()).boundingRect(texto).width()
    disponible = etiqueta.width()
    if ancho > disponible:
        problemas.append(
            f"{etiqueta.objectName() or etiqueta.__class__.__name__}: "
            f"texto de {ancho}px en {disponible}px -> {texto!r}")
    detalle.append(
        f"    {etiqueta.objectName() or etiqueta.__class__.__name__}: "
        f"{ancho}px en {disponible}px -> {texto!r}")


def _revisar_rodante(widget: BotonRodante | EtiquetaRodante, problemas: list[str],
                     detalle: list[str]) -> None:
    if not widget.isVisible():
        return
    texto = widget.text()
    if not texto or widget.width() <= 0:
        return
    metricas = QFontMetrics(widget.font())
    ancho = metricas.boundingRect(texto).width()
    disponible = _ancho_disponible(widget)
    if ancho > disponible:
        problemas.append(
            f"{widget.objectName() or widget.__class__.__name__}: "
            f"texto de {ancho}px en {disponible}px disponibles -> {texto!r}")
    alto_necesario = metricas.height()
    if isinstance(widget, EtiquetaRodante):
        alto_necesario = widget._alto_caja(metricas)
    if alto_necesario > widget.height():
        problemas.append(
            f"{widget.objectName() or widget.__class__.__name__}: "
            f"texto de {alto_necesario}px de alto en {widget.height()}px disponibles "
            f"-> {texto!r}")
    detalle.append(
        f"    {widget.objectName() or widget.__class__.__name__}: "
        f"{ancho}px en {disponible}px -> {texto!r}")


def _revisar(ventana: QWidget, problemas: list[str], detalle: list[str]) -> None:
    for etiqueta in ventana.findChildren(QLabel):
        _revisar_etiqueta(etiqueta, problemas, detalle)
    for rodante in ventana.findChildren(BotonRodante) + ventana.findChildren(EtiquetaRodante):
        _revisar_rodante(rodante, problemas, detalle)


def main() -> int:
    aplicacion = QApplication(sys.argv[:1])
    aplicar_tema(aplicacion)
    problemas: list[str] = []
    detalle: list[str] = []

    with tempfile.TemporaryDirectory() as temporal:
        stock, estadisticas, fiado, autenticacion, comercio = _ambiente(Path(temporal))
        ventas, comprobante = _ventas_historicas(stock, estadisticas, fiado)
        ventas.agregar_producto("1001")
        ventas.agregar_producto("1004")

        principal = VentanaPrincipal(stock, comercio, estadisticas, None, "cajero", fiado)
        principal.resize(*TAMANO_VENTANA)
        principal.show()
        QTest.qWait(1500)
        aplicacion.processEvents()
        print("principal")
        _revisar(principal, problemas, detalle)

        ventana_ventas = VentanaVentas(ventas, comercio, "cajero", fiado)
        ventana_ventas.resize(*TAMANO_VENTANA)
        ventana_ventas.show()
        ventana_ventas.al_mostrar()
        QTest.qWait(1500)
        aplicacion.processEvents()
        print("ventas")
        _revisar(ventana_ventas, problemas, detalle)

        ventanas = {
            "cobro": lambda: VentanaCobro(ventas.venta, fiado),
            "productos": lambda: VentanaProductos(stock),
            "estadisticas": lambda: VentanaEstadisticas(estadisticas),
            "consulta": lambda: VentanaConsulta(stock),
            "login": lambda: VentanaLogin(autenticacion),
            "clientes": lambda: VentanaClientes(fiado, "cajero"),
            "movimientos": lambda: VentanaMovimientos(stock),
            "reportes": lambda: VentanaReportes(stock),
            "alertas": lambda: VentanaAlertas(stock),
            "detalle_venta": lambda: VentanaDetalleVenta(comprobante),
        }
        for nombre, constructor in ventanas.items():
            ventana = constructor()
            # Sin resize la ventana queda con el tamaño por defecto del plugin
            # de Qt, que en offscreen no alcanza y marca falsos positivos.
            ventana.resize(*TAMANO_VENTANA)
            ventana.show()
            QTest.qWait(1500)
            aplicacion.processEvents()
            print(nombre)
            _revisar(ventana, problemas, detalle)
            ventana.hide()

    print("medidas")
    for linea in detalle:
        print(linea)
    if problemas:
        print("TEXTOS CORTADOS:")
        for problema in problemas:
            print(f"  - {problema}")
        return 1
    print("OK: ningun texto queda cortado")
    return 0


if __name__ == "__main__":
    # El teardown de Qt se cuelga con un segment fault: se sale sin limpiar.
    codigo = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(codigo)
