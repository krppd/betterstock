from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QApplication

import services.fotos
from models.producto import Producto
from views.dialogo_producto import DialogoProducto

CODIGO = "1001"


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def carpeta_fotos(tmp_path, monkeypatch):
    monkeypatch.setattr(services.fotos, "DIR_FOTOS", tmp_path)
    return tmp_path


def _dialogo() -> DialogoProducto:
    producto = Producto(codigo=CODIGO, nombre="Yerba mate 500g", precio_costo=3200.0,
                        precio_venta=5490.0, stock_actual=12, stock_minimo=4)
    return DialogoProducto(producto, lambda: False, lambda: False)


def test_imagen_corrupta_muestra_sin_imagen(aplicacion: QApplication, carpeta_fotos) -> None:
    (carpeta_fotos / f"{CODIGO}.png").write_bytes(b"\x89PNG\r\n\x1a\nesto no es una imagen")
    dialogo = _dialogo()
    assert dialogo.lblFoto.text() == "Sin imagen"
    assert dialogo.lblFoto.pixmap().isNull()
    assert dialogo.lblFoto.alignment() & Qt.AlignmentFlag.AlignCenter == Qt.AlignmentFlag.AlignCenter
    assert DialogoProducto.COLOR_PLACEHOLDER in dialogo.lblFoto.styleSheet()


def test_imagen_valida_se_muestra(aplicacion: QApplication, carpeta_fotos) -> None:
    foto = QPixmap(40, 40)
    foto.fill(QColor("#2DBC66"))
    assert foto.save(str(carpeta_fotos / f"{CODIGO}.png"))
    dialogo = _dialogo()
    assert dialogo.lblFoto.text() == ""
    assert not dialogo.lblFoto.pixmap().isNull()
