from __future__ import annotations

import io
import json

import pytest
from PIL import Image
from PyQt6.QtWidgets import QApplication

from services.fotos import Candidata, ErrorFoto, ProveedorFotos
from views.ventana_fotos import VentanaFotos

CODIGO = "1001"


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def imagen_bytes(ancho=40, alto=30) -> bytes:
    imagen = Image.new("RGB", (ancho, alto), color=(10, 120, 200))
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def foto_local(tmp_path):
    ruta = tmp_path / "foto.png"
    ruta.write_bytes(imagen_bytes())
    return ruta


class ProveedorFalso(ProveedorFotos):

    def __init__(self, candidatas=None, error=None):
        self.candidatas = candidatas or []
        self.error = error
        self.textos = []

    def buscar(self, texto):
        self.textos.append(texto)
        if self.error is not None:
            raise self.error
        return list(self.candidatas)


def ventana(proveedor, codigo=CODIGO):
    return VentanaFotos(codigo, "Gaseosa", proveedor=proveedor)


def test_la_ventana_pide_el_proveedor_por_el_texto_escrito(aplicacion) -> None:
    proveedor = ProveedorFalso()
    dialogo = ventana(proveedor)
    dialogo.ui.txtBuscar.setText("  Gaseosa  ")
    dialogo.buscar()
    assert proveedor.textos == ["Gaseosa"]


def test_la_ventana_pinta_las_candidatas_devueltas(aplicacion, foto_local) -> None:
    candidatas = [Candidata(titulo="Gaseosa", url_miniatura=foto_local.as_uri(),
                            url_completa=foto_local.as_uri())]
    dialogo = ventana(ProveedorFalso(candidatas))
    dialogo.ui.txtBuscar.setText("Gaseosa")
    dialogo.buscar()
    assert len(dialogo._candidatas) == 1
    assert dialogo.ui.lblEstado.text() == "Tocá una foto para verla en grande."
    assert dialogo.ui.btnFotos[0].isEnabled()


def test_la_ventana_avisa_cuando_no_encuentra_nada(aplicacion) -> None:
    dialogo = ventana(ProveedorFalso())
    dialogo.ui.txtBuscar.setText("Gaseosa")
    dialogo.buscar()
    assert dialogo.ui.lblEstado.text() == "Sin resultados: pegá la URL de una imagen."
    assert not dialogo.ui.btnFotos[0].isEnabled()


def test_la_ventana_avisa_cuando_falla_el_proveedor(aplicacion) -> None:
    dialogo = ventana(ProveedorFalso(error=ErrorFoto("El buscador no responde.")))
    dialogo.ui.txtBuscar.setText("Gaseosa")
    dialogo.buscar()
    assert dialogo.ui.lblEstado.text() == "El buscador no responde."


def test_la_ventana_avisa_si_no_hay_texto_para_buscar(aplicacion) -> None:
    dialogo = ventana(ProveedorFalso())
    dialogo.ui.txtBuscar.setText("   ")
    dialogo.buscar()
    assert dialogo.ui.lblEstado.text() == "Escribí un nombre o código para buscar."


def test_la_ventana_guarda_la_foto_con_el_codigo_del_producto(aplicacion, foto_local, tmp_path) -> None:
    candidatas = [Candidata(titulo="Gaseosa", url_miniatura=foto_local.as_uri(),
                            url_completa=foto_local.as_uri())]
    dialogo = ventana(ProveedorFalso(candidatas), codigo="AB/12")
    dialogo.ui.txtBuscar.setText("Gaseosa")
    dialogo.buscar()
    dialogo._elegir(0)
    dialogo.guardar()
    assert dialogo.ruta_guardada is not None
    assert dialogo.ruta_guardada.name == "AB_12.png"
    assert dialogo.ruta_guardada.read_bytes() == imagen_bytes()


def test_la_ventana_no_guarda_sin_haber_elegido_una_foto(aplicacion, tmp_path, monkeypatch) -> None:
    avisos = []
    dialogo = ventana(ProveedorFalso())
    monkeypatch.setattr(dialogo, "mostrar_advertencia",
                        lambda titulo, mensaje: avisos.append((titulo, mensaje)))
    dialogo.guardar()
    assert dialogo.ruta_guardada is None
    assert avisos == [("Foto", "Elegí una foto antes de guardar.")]


def test_la_ventana_busca_con_el_proveedor_real_sin_romperse(aplicacion, monkeypatch) -> None:
    datos = json.dumps({"products": [
        {"code": "1", "product_name": "Gaseosa", "image_url": "http://x/g.png"},
    ]}).encode("utf-8")

    class Respuesta:
        headers = None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, _n=-1):
            return datos

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Respuesta())
    dialogo = VentanaFotos(CODIGO, "Gaseosa")
    dialogo.ui.txtBuscar.setText("Gaseosa")
    dialogo.buscar()
    assert len(dialogo._candidatas) == 1
    assert dialogo._candidatas[0].titulo == "Gaseosa"
