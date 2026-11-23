from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication
from PIL import Image

from views import ventana_consulta
from views.ventana_consulta import LADO_FOTO, VentanaConsulta


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def test_la_foto_de_consulta_es_mas_grande(aplicacion) -> None:
    ventana = VentanaConsulta(object())
    try:
        assert LADO_FOTO > 320
        assert ventana.ui.lblImagen.minimumSize().width() == LADO_FOTO
        assert ventana.ui.lblImagen.maximumSize().width() == LADO_FOTO
    finally:
        ventana.deleteLater()


def test_la_foto_se_escala_al_nuevo_tamano(aplicacion, monkeypatch, tmp_path) -> None:
    ruta = tmp_path / "foto.png"
    Image.new("RGB", (800, 400), "white").save(ruta)
    monkeypatch.setattr(ventana_consulta, "ruta_foto", lambda _codigo: str(ruta))

    ventana = VentanaConsulta(object())
    try:
        producto = type("ProductoFalso", (), {"codigo": "1001"})()
        ventana._mostrar_imagen(producto)
        pixmap = ventana.ui.lblImagen.pixmap()
        assert not pixmap.isNull()
        assert pixmap.width() == LADO_FOTO
        assert pixmap.height() == LADO_FOTO // 2
    finally:
        ventana.deleteLater()
