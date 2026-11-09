from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog

from models.comercio import Comercio
from models.medio_pago import METODO_EFECTIVO
from models.producto import Producto
from models.venta import Venta
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.comercio_repositorio import ComercioRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_comercio import GestorComercio
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from services.impresion import ErrorImpresion
from services.ticket import ANCHO_PAPEL, _ascii, _lineas_ticket, _recortar
from ui.widgets.trabajo_impresion import TrabajoImpresion
from views import ventana_ventas as modulo_ventana_ventas
from views.dialogo_ticket import DialogoTicket
from views.ventana_ventas import VentanaVentas

COMERCIO = Comercio("Kiosco El Talar", "Av. Siempreviva 742", "30-11122233-5", "011-1234-5678")


@pytest.fixture(scope="session", autouse=True)
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def _venta() -> Venta:
    venta = Venta()
    producto = Producto(codigo="1001", nombre="Cable de acero", precio_costo=600.0,
                        precio_venta=1000.0, stock_actual=10, stock_minimo=2)
    venta.agregar_unidad(producto)
    venta.agregar_cantidad(producto, 2.5)
    oferta = Producto(codigo="1002", nombre="Martillo", precio_costo=8500.0,
                      precio_venta=12900.0, stock_actual=10, stock_minimo=2,
                      precio_oferta=9999.0)
    venta.agregar_unidad(oferta)
    venta.agregar_comodin("Pila AA recargada", 2, 900.0)
    return venta


def _textos(venta: Venta, comercio: Comercio | None = COMERCIO,
            monto_recibido: float = 0.0, vuelto: float = 0.0,
            identificador: str = "", medio: str = "") -> list[str]:
    return [texto for texto, _ in _lineas_ticket(venta, comercio, monto_recibido,
                                                 vuelto, identificador, medio)]


def _cerrar(dialogo) -> None:
    dialogo.close()
    dialogo.deleteLater()


def _ventana_de_ventas(tmp_path) -> VentanaVentas:
    base = tmp_path / "ventas.db"
    stock = GestorStock(
        ProductoRepositorio(base),
        MovimientoRepositorio(base),
        CategoriaRepositorio(base))
    stock.inicializar()
    stock.guardar_producto(Producto(
        codigo="1001", nombre="Cable de acero", precio_costo=600.0,
        precio_venta=1000.0, stock_actual=10, stock_minimo=2))
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    estadisticas.inicializar()
    comercio = GestorComercio(ComercioRepositorio(tmp_path / "comercio.db"))
    comercio.inicializar()
    return VentanaVentas(GestorVentas(stock, estadisticas), comercio, "cajero")


def test_el_ticket_empieza_con_el_comercio():
    lineas = _lineas_ticket(_venta(), COMERCIO)
    assert lineas[0] == ("Kiosco El Talar", "titulo")
    assert ("Av. Siempreviva 742", "centro") in lineas
    assert ("CUIT: 30-11122233-5", "centro") in lineas
    assert ("Tel: 011-1234-5678", "centro") in lineas


def test_el_ticket_tiene_el_encabezado_y_el_numero():
    textos = _textos(_venta(), identificador="2026-10-21 18:30:45")
    assert "TICKET DE VENTA" in textos
    assert "Nro: 2026-10-21 18:30:45" in textos
    assert "CANTIDAD X PRECIO       SUBTOTAL" in textos


def test_el_ticket_arma_las_lineas_de_los_items():
    textos = _textos(_venta())
    assert "Cable de acero" in textos
    assert "Martillo (OFERTA)" in textos
    assert "Pila AA recargada (COMODÍN)" in textos
    assert any("3,5 x $1000.00" in texto for texto in textos)
    assert any("1 x $9999.00" in texto for texto in textos)
    assert any("2 x $900.00" in texto for texto in textos)


def test_el_ticket_desglosa_el_iva_el_total_y_el_vuelto():
    textos = _textos(_venta(), monto_recibido=20000.0, vuelto=6100.0,
                     identificador="2026-10-21 18:30:45", medio="Efectivo")
    assert any(texto.startswith("IVA 21%") for texto in textos)
    assert any(texto.startswith("TOTAL") for texto in textos)
    assert any(texto.startswith("PAGO: Efectivo") for texto in textos)
    assert any(texto.startswith("SU PAGO") for texto in textos)
    assert any(texto.startswith("VUELTO") for texto in textos)


def test_el_ticket_sin_comercio_usa_el_nombre_por_defecto():
    lineas = _lineas_ticket(_venta(), None)
    assert lineas[0] == ("BetterStock", "titulo")


def test_el_ticket_sin_pago_no_muestra_el_vuelto():
    textos = _textos(_venta(), monto_recibido=20000.0, vuelto=0.0)
    assert not any(texto.startswith("PAGO:") for texto in textos)
    assert not any(texto.startswith("VUELTO") for texto in textos)


def test_el_ticket_se_recorta_al_ancho():
    assert _recortar("un texto bastante largo", 10) == "un text..."
    assert _recortar("corto", 10) == "corto"
    assert _recortar("texto largo", None) == "texto largo"


def test_el_texto_del_ticket_sin_tildes_para_la_termica():
    assert _ascii("Pila AA recargada (COMODÍN)") == "Pila AA recargada (COMODIN)"
    assert _ascii("Ñandú") == "Nandu"


def test_el_ancho_del_papel_son_32_caracteres():
    assert ANCHO_PAPEL == 32


def test_el_hilo_de_impresion_avisa_cuando_termina():
    resultados: list[str] = []
    trabajo = TrabajoImpresion(lambda: None)
    trabajo.terminado.connect(resultados.append, Qt.ConnectionType.DirectConnection)
    trabajo.start()
    trabajo.wait(5000)
    assert resultados == [""]


def test_el_hilo_de_impresion_avisa_el_error():
    resultados: list[str] = []

    def fallar() -> None:
        raise RuntimeError("no hay impresora")

    trabajo = TrabajoImpresion(fallar)
    trabajo.terminado.connect(resultados.append, Qt.ConnectionType.DirectConnection)
    trabajo.start()
    trabajo.wait(5000)
    assert resultados == ["no hay impresora"]


def test_el_dialogo_del_ticket_muestra_el_total_y_los_botones():
    dialogo = DialogoTicket(14534.05, "Efectivo", 20000.0, 6100.0,
                            "2026-10-21 18:30:45")
    assert "$ 14.534,05" in dialogo.lblTotal.text()
    assert "Efectivo" in dialogo.lblDetalle.text()
    assert "Vuelto" in dialogo.lblDetalle.text()
    assert "2026-10-21 18:30:45" in dialogo.lblComprobante.text()
    assert dialogo.btnImprimir.text() == "Imprimir ticket"
    assert dialogo.btnCerrar.text() == "Cerrar"
    assert dialogo.accion == "cerrar"
    _cerrar(dialogo)


def test_el_dialogo_del_ticket_avisa_el_error_de_impresion():
    dialogo = DialogoTicket(100.0)
    dialogo.mostrar_error("no hay impresora")
    assert "no hay impresora" in dialogo.lblAviso.text()
    assert "registrada" in dialogo.lblAviso.text()
    assert dialogo.btnImprimir.isEnabled()
    assert dialogo.btnCerrar.isEnabled()
    _cerrar(dialogo)


def test_el_dialogo_del_ticket_se_cierra_si_no_se_imprime():
    dialogo = DialogoTicket(100.0)
    dialogo.imprimiendo()
    assert not dialogo.btnImprimir.isEnabled()
    assert not dialogo.btnCerrar.isEnabled()
    _cerrar(dialogo)


def test_despues_del_cobro_se_abre_el_dialogo_del_ticket(tmp_path, monkeypatch):
    ventana = _ventana_de_ventas(tmp_path)
    ventana.ui.txtCodigoBarras.setText("1001")
    ventana.agregar_producto()
    ventana._monto_recibido = 1000.0

    abiertos: list[DialogoTicket] = []

    def exec_espia(dialogo):
        abiertos.append(dialogo)
        return dialogo.DialogCode.Rejected

    monkeypatch.setattr(DialogoTicket, "exec", exec_espia)
    ventana._resolver_impresion()

    assert len(abiertos) == 1
    assert abiertos[0].btnImprimir.text() == "Imprimir ticket"
    assert abiertos[0].btnCerrar.text() == "Cerrar"
    assert "$ 1.000,00" in abiertos[0].lblTotal.text()
    for dialogo in abiertos:
        _cerrar(dialogo)


def test_el_cobro_registra_la_venta_y_abre_el_dialogo(tmp_path, monkeypatch):
    ventana = _ventana_de_ventas(tmp_path)
    ventana.ui.txtCodigoBarras.setText("1001")
    ventana.agregar_producto()

    class CobroFalso:
        DialogCode = QDialog.DialogCode

        def __init__(self, *_args, **_kwargs):
            self.resultado = (METODO_EFECTIVO, 1000.0, "", "")
            self.total_cobrar = 1000.0
            self.pagos = ()

        def exec(self):
            return QDialog.DialogCode.Accepted

    abiertos: list[DialogoTicket] = []

    def exec_espia(dialogo):
        abiertos.append(dialogo)
        return dialogo.DialogCode.Rejected

    monkeypatch.setattr(modulo_ventana_ventas, "VentanaCobro", CobroFalso)
    monkeypatch.setattr(DialogoTicket, "exec", exec_espia)
    ventana.cobrar_venta()

    assert ventana._ultimo_comprobante is not None
    assert ventana._ultimo_comprobante.total == 1000.0
    assert len(abiertos) == 1
    assert "$ 1.000,00" in abiertos[0].lblTotal.text()
    assert ventana._gestor_ventas.venta.esta_vacia()
    for dialogo in abiertos:
        _cerrar(dialogo)


def test_si_la_impresion_falla_se_avisa_y_no_se_pierde_la_venta(tmp_path, monkeypatch):
    ventana = _ventana_de_ventas(tmp_path)
    ventana.ui.txtCodigoBarras.setText("1001")
    ventana.agregar_producto()
    ventana._monto_recibido = 1000.0

    def fallar(*_args, **_kwargs):
        raise ErrorImpresion("No hay ninguna impresora configurada en el sistema.")

    monkeypatch.setattr(modulo_ventana_ventas, "imprimir_ticket", fallar)

    dialogo = DialogoTicket(1000.0)
    ventana._imprimir_ticket(ventana._gestor_ventas.venta,
                             ventana._gestor_comercio.comercio, 1000.0, 0.0, "", "", dialogo)
    for trabajo in list(ventana._trabajos):
        trabajo.wait(5000)
    QApplication.processEvents()

    assert "impresora" in dialogo.lblAviso.text()
    assert "registrada" in dialogo.lblAviso.text()
    assert dialogo.btnImprimir.isEnabled()
    _cerrar(dialogo)
