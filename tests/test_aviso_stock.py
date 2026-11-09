from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication, QWidget

from config import ALERTAS_EN_AVISO_STOCK
from models.producto import Producto
from ui.widgets.notificacion import Notificacion
from views.ventana_principal import VentanaPrincipal

ALTO_MAXIMO_AVISO = 260


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def _producto(codigo: str, nombre: str, actual: int, minimo: int) -> Producto:
    return Producto(codigo=codigo, nombre=nombre, precio_costo=10.0, precio_venta=20.0,
                    stock_actual=actual, stock_minimo=minimo)


def _criticos(cantidad: int) -> list[Producto]:
    return [_producto(str(1000 + n), f"Producto {n:02d}", 1 + n % 4, 5 + n % 3)
            for n in range(cantidad)]


def test_por_defecto_muestra_cinco() -> None:
    assert ALERTAS_EN_AVISO_STOCK == 5
    assert VentanaPrincipal.MAXIMO_ALERTAS_EN_MENSAJE == 5


def test_muestra_los_primeros_y_cuantos_quedan() -> None:
    mensaje = VentanaPrincipal.armar_aviso_stock(_criticos(12), 5)
    renglones = [linea for linea in mensaje.splitlines() if linea.startswith("•")]
    assert len(renglones) == 5
    assert mensaje.splitlines()[-1] == "+7 más"


def test_sin_sobrante_no_agrega_la_linea_de_mas() -> None:
    mensaje = VentanaPrincipal.armar_aviso_stock(_criticos(3), 5)
    assert "más" not in mensaje
    assert mensaje.count("•") == 3


def test_primero_los_que_no_tienen_stock() -> None:
    productos = [
        _producto("1", "Casi bien", 4, 5),
        _producto("2", "Mitad", 5, 10),
        _producto("3", "Agotado", 0, 3),
        _producto("4", "Muy poco", 1, 10),
    ]
    mensaje = VentanaPrincipal.armar_aviso_stock(productos, 3)
    nombres = [linea.split(" (")[0].lstrip("• ") for linea in mensaje.splitlines()
               if linea.startswith("•")]
    assert nombres == ["Agotado", "Muy poco", "Mitad"]
    assert mensaje.splitlines()[-1] == "+1 más"


def test_el_aviso_no_ocupa_la_pantalla(aplicacion: QApplication) -> None:
    padre = QWidget()
    padre.resize(1000, 760)
    padre.show()
    aviso = Notificacion(padre, duracion_ms=5000)
    aviso.mostrar("Alerta de stock", VentanaPrincipal.armar_aviso_stock(_criticos(40), 5))
    assert aviso.height() <= ALTO_MAXIMO_AVISO
