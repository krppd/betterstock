import io
import json

import pytest
from PIL import Image

from services.fotos import (
    MAX_RESULTADOS,
    Candidata,
    ErrorFoto,
    ProveedorFotos,
    ProveedorOpenFoodFacts,
    descargar_bytes,
    descargar_foto,
    guardar_bytes,
    nombre_archivo,
    ruta_foto,
)


def imagen_bytes(ancho=100, alto=80, formato="PNG"):
    imagen = Image.new("RGB", (ancho, alto), color=(10, 120, 200))
    buffer = io.BytesIO()
    imagen.save(buffer, format=formato)
    return buffer.getvalue()


def test_nombre_archivo_sanea_codigo():
    assert nombre_archivo("1001") == "1001.png"
    assert nombre_archivo("AB/12 34") == "AB_12_34.png"
    assert nombre_archivo("...") == "producto.png"


def test_guardar_bytes_convierte_y_achica(tmp_path):
    ruta = guardar_bytes(imagen_bytes(2000, 1000), "1001", destino=tmp_path)
    assert ruta.name == "1001.png"
    with Image.open(ruta) as final:
        assert final.format == "PNG"
        assert max(final.size) <= 800


def test_guardar_bytes_rechaza_basura(tmp_path):
    with pytest.raises(ErrorFoto):
        guardar_bytes(b"esto no es una imagen", "1", destino=tmp_path)


def test_descargar_bytes_desde_archivo(tmp_path):
    origen = tmp_path / "foto.png"
    origen.write_bytes(imagen_bytes())
    assert descargar_bytes(origen.as_uri()) == origen.read_bytes()


def test_descargar_bytes_falla_con_ruta_inexistente(tmp_path):
    with pytest.raises(ErrorFoto):
        descargar_bytes((tmp_path / "noexiste.png").as_uri())


def test_descargar_bytes_rechaza_pesadas(tmp_path, monkeypatch):
    pesada = tmp_path / "grande.png"
    pesada.write_bytes(imagen_bytes(3000, 3000))
    import services.fotos as fotos
    monkeypatch.setattr(fotos, "MAX_BYTES", 10)
    with pytest.raises(ErrorFoto):
        descargar_bytes(pesada.as_uri())


def test_descargar_foto_guarda_con_codigo(tmp_path):
    origen = tmp_path / "o.jpg"
    origen.write_bytes(imagen_bytes(formato="JPEG"))
    ruta = descargar_foto(origen.as_uri(), "AB/1", destino=tmp_path / "salida")
    assert ruta.name == "AB_1.png"
    assert ruta.is_file()


def _respuesta_off(productos):
    datos = json.dumps({"products": productos}).encode("utf-8")

    class Respuesta:
        headers = None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, _n=-1):
            return datos

    return Respuesta()


def test_proveedor_busca_y_filtra_sin_imagen(monkeypatch):
    productos = [
        {"code": "1", "product_name": "A", "image_url": "http://x/a.jpg",
         "image_small_url": "http://x/a-s.jpg"},
        {"code": "2", "product_name": "B"},
        {"code": "3", "product_name": "C", "image_url": "http://x/c.jpg"},
    ]
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *a, **k: _respuesta_off(productos))
    resultado = ProveedorOpenFoodFacts().buscar("algo")
    assert [c.titulo for c in resultado] == ["A", "C"]
    assert resultado[0].url_miniatura == "http://x/a-s.jpg"
    assert resultado[1].url_miniatura == "http://x/c.jpg"


def test_proveedor_limita_a_seis(monkeypatch):
    productos = [{"code": str(i), "product_name": f"P{i}",
                  "image_url": f"http://x/{i}.jpg"} for i in range(9)]
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *a, **k: _respuesta_off(productos))
    assert len(ProveedorOpenFoodFacts().buscar("algo")) == MAX_RESULTADOS


def test_proveedor_codigo_exact(monkeypatch):
    datos = json.dumps({"status": 1, "product": {
        "product_name": "Exacto", "image_url": "http://x/full.jpg",
        "image_small_url": "http://x/small.jpg"}}).encode("utf-8")

    class Respuesta:
        headers = None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, _n=-1):
            return datos

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *a, **k: Respuesta())
    resultado = ProveedorOpenFoodFacts().buscar("779123456789")
    assert len(resultado) == 1
    assert resultado[0].titulo == "Exacto"


def test_proveedor_vacio_devuelve_vacio():
    assert ProveedorOpenFoodFacts().buscar("   ") == []


def test_proveedor_es_abstracto():
    with pytest.raises(TypeError):
        ProveedorFotos()


def test_candidata_es_inmutable():
    candidata = Candidata(titulo="T", url_miniatura="m", url_completa="c")
    with pytest.raises(AttributeError):
        candidata.titulo = "otro"


def test_ruta_foto_encuentra_por_codigo(tmp_path):
    assert ruta_foto("1001", destino=tmp_path) == ""
    (tmp_path / "1001.jpg").write_bytes(imagen_bytes())
    assert ruta_foto("1001", destino=tmp_path) == str(tmp_path / "1001.jpg")
