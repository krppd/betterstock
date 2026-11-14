from __future__ import annotations

import sqlite3

from models.producto import Producto
from repositories.producto_repositorio import ProductoRepositorio
from repositories.sqlite import conectar

CODIGO = "1001"
CODIGO_BARRAS = "7791234567890"


def test_el_producto_guarda_y_lee_el_codigo_de_barras(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    repo = ProductoRepositorio(ruta)
    repo.inicializar()
    repo.guardar(Producto(codigo=CODIGO, nombre="Gaseosa", codigo_barras=CODIGO_BARRAS))

    guardado = repo.buscar(CODIGO)
    assert guardado is not None
    assert guardado.codigo_barras == CODIGO_BARRAS


def test_el_codigo_de_barras_se_normaliza_al_guardar(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    repo = ProductoRepositorio(ruta)
    repo.inicializar()
    repo.guardar(Producto(codigo=CODIGO, nombre="Gaseosa", codigo_barras="  7791234567890  "))

    guardado = repo.buscar(CODIGO)
    assert guardado is not None
    assert guardado.codigo_barras == CODIGO_BARRAS


def test_un_producto_sin_codigo_de_barras_guarda_vacio(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    repo = ProductoRepositorio(ruta)
    repo.inicializar()
    repo.guardar(Producto(codigo=CODIGO, nombre="Gaseosa"))

    guardado = repo.buscar(CODIGO)
    assert guardado is not None
    assert guardado.codigo_barras == ""


def test_la_busqueda_por_texto_encuentra_por_codigo_de_barras(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    repo = ProductoRepositorio(ruta)
    repo.inicializar()
    repo.guardar(Producto(codigo=CODIGO, nombre="Gaseosa", codigo_barras=CODIGO_BARRAS))

    encontrados = repo.buscar_por_texto(CODIGO_BARRAS)
    assert len(encontrados) == 1
    assert encontrados[0].codigo == CODIGO


def test_la_busqueda_por_texto_encuentra_por_prefijo_del_codigo_de_barras(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    repo = ProductoRepositorio(ruta)
    repo.inicializar()
    repo.guardar(Producto(codigo=CODIGO, nombre="Gaseosa", codigo_barras=CODIGO_BARRAS))

    encontrados = repo.buscar_por_texto("77912")
    assert len(encontrados) == 1


def test_una_base_vieja_recibe_la_columna_del_codigo_de_barras(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    conexion = sqlite3.connect(str(ruta))
    conexion.execute(
        "CREATE TABLE productos(codigo TEXT PRIMARY KEY, nombre TEXT NOT NULL)")
    conexion.commit()
    conexion.close()

    conexion = conectar(ruta)
    conexion.close()

    columnas = [f[1] for f in sqlite3.connect(str(ruta)).execute("PRAGMA table_info(productos)")]
    assert "codigo_barras" in columnas


def test_el_to_dict_incluye_el_codigo_de_barras() -> None:
    producto = Producto(codigo=CODIGO, nombre="Gaseosa", codigo_barras=CODIGO_BARRAS)
    assert producto.to_dict()["codigo_barras"] == CODIGO_BARRAS


def test_el_from_dict_lee_el_codigo_de_barras() -> None:
    datos = {"codigo": CODIGO, "nombre": "Gaseosa", "codigo_barras": CODIGO_BARRAS}
    producto = Producto.from_dict(datos)
    assert producto.codigo_barras == CODIGO_BARRAS


def test_el_from_dict_tolera_la_falta_de_codigo_de_barras() -> None:
    datos = {"codigo": CODIGO, "nombre": "Gaseosa"}
    producto = Producto.from_dict(datos)
    assert producto.codigo_barras == ""
