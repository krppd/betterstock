from __future__ import annotations

import sqlite3

from repositories.sqlite import conectar

COLUMNAS_PRODUCTOS = (
    "codigo", "codigo_barras", "nombre", "categoria", "unidad_medida", "precio_costo",
    "precio_venta", "stock_actual", "stock_minimo", "alicuota_iva",
    "precio_oferta", "promo_cantidad", "promo_precio", "fecha_vencimiento",
)

COLUMNAS_USUARIOS = ("usuario", "password_hash", "permiso", "permisos_extra")


def columnas(ruta, tabla: str) -> list[str]:
    conexion = sqlite3.connect(str(ruta))
    try:
        return [fila[1] for fila in conexion.execute(f"PRAGMA table_info({tabla})")]
    finally:
        conexion.close()


def test_una_base_nueva_nace_con_las_columnas_del_plan_pagado(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    conexion = conectar(ruta)
    conexion.close()
    assert columnas(ruta, "productos") == list(COLUMNAS_PRODUCTOS)
    assert columnas(ruta, "usuarios") == list(COLUMNAS_USUARIOS)


def test_una_base_vieja_recibe_las_columnas_que_faltan(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    conexion = sqlite3.connect(str(ruta))
    conexion.executescript(
        "CREATE TABLE productos(codigo TEXT PRIMARY KEY, nombre TEXT NOT NULL,"
        " categoria TEXT DEFAULT '', unidad_medida TEXT DEFAULT '',"
        " precio_costo REAL DEFAULT 0, precio_venta REAL DEFAULT 0,"
        " stock_actual INTEGER DEFAULT 0, stock_minimo INTEGER DEFAULT 0,"
        " alicuota_iva REAL DEFAULT 21.0, precio_oferta REAL DEFAULT 0,"
        " fecha_vencimiento TEXT DEFAULT '');"
        "CREATE TABLE usuarios(usuario TEXT PRIMARY KEY, password_hash TEXT NOT NULL,"
        " permiso TEXT DEFAULT 'vendedor');"
    )
    conexion.commit()
    conexion.close()

    conexion = conectar(ruta)
    conexion.close()

    assert sorted(columnas(ruta, "productos")) == sorted(COLUMNAS_PRODUCTOS)
    assert sorted(columnas(ruta, "usuarios")) == sorted(COLUMNAS_USUARIOS)


def test_una_base_sin_la_tabla_de_usuarios_tambien_las_crea(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    conexion = sqlite3.connect(str(ruta))
    conexion.execute("CREATE TABLE productos(codigo TEXT PRIMARY KEY, nombre TEXT NOT NULL)")
    conexion.commit()
    conexion.close()

    conexion = conectar(ruta)
    conexion.close()

    assert "permisos_extra" in columnas(ruta, "usuarios")


def test_la_migracion_es_idempotente(tmp_path) -> None:
    ruta = tmp_path / "betterstock.db"
    for _ in range(3):
        conexion = conectar(ruta)
        conexion.close()
    assert columnas(ruta, "productos") == list(COLUMNAS_PRODUCTOS)
    assert columnas(ruta, "usuarios") == list(COLUMNAS_USUARIOS)
