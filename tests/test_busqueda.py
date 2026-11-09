from __future__ import annotations

from models.producto import Producto
from repositories.producto_repositorio import ProductoRepositorio


def _repositorio(tmp_path, pares):
    repo = ProductoRepositorio(tmp_path / "productos.csv")
    for codigo, nombre in pares:
        repo.guardar(Producto(codigo=codigo, nombre=nombre))
    return repo


def _semilla():
    return [
        ("B001", "Bulón hexagonal 2 x 1/4"),
        ("B002", "Bulón hexagonal 3 x 3/8"),
        ("T010", "Tornillo autorroscante 4 x 40"),
        ("C100", "Café torrado 500 g 100% arábica"),
        ("M200", "Martillo carpintero 16 oz"),
        ("L300", "Lámpara LED 9W E27"),
    ]


def _codigos(productos):
    return [p.codigo for p in productos]


def test_terminos_en_cualquier_orden(tmp_path):
    repo = _repositorio(tmp_path, _semilla())
    assert _codigos(repo.buscar_por_texto("bulon 1/4")) == ["B001"]
    assert _codigos(repo.buscar_por_texto("1/4 bulon")) == ["B001"]
    assert _codigos(repo.buscar_por_texto("2 X 1/4 HEXAGONAL Bulón")) == ["B001"]


def test_insensible_a_acentos_y_mayusculas(tmp_path):
    repo = _repositorio(tmp_path, _semilla())
    assert set(_codigos(repo.buscar_por_texto("bulon"))) == {"B001", "B002"}
    assert set(_codigos(repo.buscar_por_texto("bulón"))) == {"B001", "B002"}
    assert set(_codigos(repo.buscar_por_texto("BULON"))) == {"B001", "B002"}
    assert _codigos(repo.buscar_por_texto("cafe arabica")) == ["C100"]
    assert _codigos(repo.buscar_por_texto("lampara led")) == ["L300"]
    assert _codigos(repo.buscar_por_texto("martíllo")) == ["M200"]


def test_codigo_parcial_mas_nombre(tmp_path):
    repo = _repositorio(tmp_path, _semilla())
    assert _codigos(repo.buscar_por_texto("B001 hexagonal")) == ["B001"]
    assert _codigos(repo.buscar_por_texto("t01 autorroscante")) == ["T010"]
    assert set(_codigos(repo.buscar_por_texto("b00 bulon"))) == {"B001", "B002"}


def test_texto_vacio_devuelve_todo(tmp_path):
    repo = _repositorio(tmp_path, _semilla())
    assert len(repo.buscar_por_texto("")) == 6
    assert len(repo.buscar_por_texto("   ")) == 6


def test_porcentaje_y_guion_bajo_son_literales(tmp_path):
    repo = _repositorio(tmp_path, _semilla())
    assert _codigos(repo.buscar_por_texto("100%")) == ["C100"]
    assert _codigos(repo.buscar_por_texto("%")) == ["C100"]
    assert repo.buscar_por_texto("_") == []
    assert repo.buscar_por_texto("100_") == []


def test_limite_cincuenta(tmp_path):
    repo = _repositorio(
        tmp_path, [(f"K{i:03d}", f"Tuerca M8 paso {i}") for i in range(60)]
    )
    assert len(repo.buscar_por_texto("tuerca")) == 50
