from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

DB_NOMBRE = "betterstock.db"

ESQUEMA = """CREATE TABLE IF NOT EXISTS productos(codigo TEXT PRIMARY KEY, nombre TEXT NOT NULL, categoria TEXT DEFAULT '', unidad_medida TEXT DEFAULT '', precio_costo REAL DEFAULT 0, precio_venta REAL DEFAULT 0, stock_actual INTEGER DEFAULT 0, stock_minimo INTEGER DEFAULT 0, alicuota_iva REAL DEFAULT 21.0, precio_oferta REAL DEFAULT 0, promo_cantidad INTEGER DEFAULT 0, promo_precio REAL DEFAULT 0, fecha_vencimiento TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS movimientos(id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, codigo_producto TEXT NOT NULL, tipo TEXT NOT NULL, cantidad INTEGER NOT NULL, motivo TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS categorias(nombre TEXT PRIMARY KEY COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS usuarios(usuario TEXT PRIMARY KEY, password_hash TEXT NOT NULL, permiso TEXT DEFAULT 'vendedor', permisos_extra TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS comercio(nombre TEXT NOT NULL, direccion TEXT DEFAULT '', cuit TEXT DEFAULT '', telefono TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS clientes(codigo INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE COLLATE NOCASE, telefono TEXT DEFAULT '', limite REAL DEFAULT 0, activo INTEGER DEFAULT 1, doc_tipo INTEGER DEFAULT 99, doc_nro TEXT DEFAULT '', cond_iva INTEGER DEFAULT 5, email TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS cuenta_movimientos(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, cliente TEXT NOT NULL, tipo TEXT NOT NULL, importe REAL NOT NULL, detalle TEXT DEFAULT '', medio TEXT DEFAULT '', usuario TEXT DEFAULT '', hora TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS ventas(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, hora TEXT NOT NULL, total REAL DEFAULT 0, detalle TEXT DEFAULT '', descuento_global REAL DEFAULT 0, recargo REAL DEFAULT 0, monto_recibido REAL DEFAULT 0, vuelto REAL DEFAULT 0, estado TEXT DEFAULT 'activa', medio_pago TEXT DEFAULT '', datos_pago TEXT DEFAULT '', usuario TEXT DEFAULT '', cliente TEXT DEFAULT '', pagos TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS cierres(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, hora TEXT NOT NULL, cantidad_ventas INTEGER DEFAULT 0, total_esperado REAL DEFAULT 0, efectivo_esperado REAL DEFAULT 0, declarado REAL DEFAULT 0, diferencia REAL DEFAULT 0, sobrante REAL DEFAULT 0, faltante REAL DEFAULT 0, notas TEXT DEFAULT '', medios TEXT DEFAULT '', usuario TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS turnos(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_apertura TEXT NOT NULL, hora_apertura TEXT NOT NULL, usuario_apertura TEXT DEFAULT '', fondo_inicial REAL DEFAULT 0, fecha_cierre TEXT DEFAULT '', hora_cierre TEXT DEFAULT '', usuario_cierre TEXT DEFAULT '', cantidad_ventas INTEGER DEFAULT 0, total_esperado REAL DEFAULT 0, efectivo_esperado REAL DEFAULT 0, declarado REAL DEFAULT 0, diferencia REAL DEFAULT 0, sobrante REAL DEFAULT 0, faltante REAL DEFAULT 0, medios TEXT DEFAULT '', notas TEXT DEFAULT '', estado TEXT DEFAULT 'abierto');
CREATE TABLE IF NOT EXISTS importaciones(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, archivo TEXT NOT NULL, creados INTEGER DEFAULT 0, actualizados INTEGER DEFAULT 0, omitidos INTEGER DEFAULT 0, errores INTEGER DEFAULT 0, backup TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS codigos_anulacion(id INTEGER PRIMARY KEY AUTOINCREMENT, etiqueta TEXT DEFAULT '', hash_codigo TEXT NOT NULL, salt TEXT NOT NULL, creado TEXT NOT NULL, activo INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS proveedores(id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE COLLATE NOCASE, cuit TEXT DEFAULT '', telefono TEXT DEFAULT '', email TEXT DEFAULT '', notas TEXT DEFAULT '', activo INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS compras(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, proveedor_id INTEGER NOT NULL, tipo_comprobante TEXT DEFAULT 'remito', numero_comprobante TEXT DEFAULT '', ajuste REAL DEFAULT 0, total REAL DEFAULT 0, usuario TEXT DEFAULT '', anulada INTEGER DEFAULT 0, anulada_por TEXT DEFAULT '', motivo_anulacion TEXT DEFAULT '', notas TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS compra_items(id INTEGER PRIMARY KEY AUTOINCREMENT, compra_id INTEGER NOT NULL, codigo_producto TEXT NOT NULL, cantidad REAL NOT NULL, costo_unitario REAL NOT NULL, alicuota_iva REAL DEFAULT 21, costo_anterior REAL DEFAULT 0, subtotal REAL NOT NULL);
CREATE TABLE IF NOT EXISTS caja_movimientos(id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, hora TEXT NOT NULL, tipo TEXT NOT NULL, concepto TEXT NOT NULL, categoria TEXT DEFAULT '', importe REAL NOT NULL, usuario TEXT DEFAULT '', anulado INTEGER DEFAULT 0, anulado_por TEXT DEFAULT '', motivo_anulacion TEXT DEFAULT '');
CREATE TRIGGER IF NOT EXISTS impedir_borrado_caja_movimientos BEFORE DELETE ON caja_movimientos BEGIN SELECT RAISE(ABORT, 'No se pueden borrar movimientos de caja'); END;
CREATE TABLE IF NOT EXISTS devoluciones(id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER NOT NULL, fecha TEXT NOT NULL, hora TEXT NOT NULL, usuario TEXT DEFAULT '', total REAL DEFAULT 0, anulada INTEGER DEFAULT 0, motivo TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS devolucion_items(id INTEGER PRIMARY KEY AUTOINCREMENT, devolucion_id INTEGER NOT NULL, codigo_producto TEXT NOT NULL, cantidad REAL NOT NULL, precio_unitario REAL NOT NULL, subtotal REAL NOT NULL);"""


def a_iso(fecha_ddmmaaaa: str) -> str:
    return datetime.strptime(fecha_ddmmaaaa, "%d/%m/%Y").strftime("%Y-%m-%d")


def de_iso(fecha_iso: str) -> str:
    return datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")


def ruta_db(origen: str | Path) -> Path:
    texto = str(origen)
    if texto.endswith(".db"):
        return Path(texto)
    ruta = Path(origen)
    if ruta.is_dir():
        return ruta / DB_NOMBRE
    return ruta.parent / DB_NOMBRE


def conectar(origen: str | Path) -> sqlite3.Connection:
    ruta = ruta_db(origen)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(str(ruta))
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA journal_mode=WAL")
    conexion.executescript(ESQUEMA)
    _migrar_usuarios(conexion)
    _migrar_cierres(conexion)
    _migrar_productos(conexion)
    _migrar_ventas(conexion)
    _migrar_clientes(conexion)
    _migrar_cuenta(conexion)
    return conexion


def _migrar_usuarios(conexion: sqlite3.Connection) -> None:
    columnas = [fila["name"] for fila in conexion.execute("PRAGMA table_info(usuarios)")]
    if "permiso" not in columnas:
        conexion.execute("ALTER TABLE usuarios ADD COLUMN permiso TEXT DEFAULT 'vendedor'")
        conexion.execute("UPDATE usuarios SET permiso = 'administrador' WHERE usuario = 'admin'")
        conexion.commit()
    if "permisos_extra" not in columnas:
        conexion.execute("ALTER TABLE usuarios ADD COLUMN permisos_extra TEXT DEFAULT ''")
        conexion.commit()


def _migrar_cierres(conexion: sqlite3.Connection) -> None:
    columnas = [fila["name"] for fila in conexion.execute("PRAGMA table_info(cierres)")]
    if "usuario" not in columnas:
        conexion.execute("ALTER TABLE cierres ADD COLUMN usuario TEXT DEFAULT ''")
        conexion.commit()


def _migrar_productos(conexion: sqlite3.Connection) -> None:
    columnas = [fila["name"] for fila in conexion.execute("PRAGMA table_info(productos)")]
    cambios = (
        ("fecha_vencimiento", "TEXT DEFAULT ''"),
        ("promo_cantidad", "INTEGER DEFAULT 0"),
        ("promo_precio", "REAL DEFAULT 0"),
    )
    for columna, definicion in cambios:
        if columna not in columnas:
            conexion.execute(f"ALTER TABLE productos ADD COLUMN {columna} {definicion}")
    conexion.commit()


def _migrar_ventas(conexion: sqlite3.Connection) -> None:
    columnas = [fila["name"] for fila in conexion.execute("PRAGMA table_info(ventas)")]
    if "pagos" not in columnas:
        conexion.execute("ALTER TABLE ventas ADD COLUMN pagos TEXT DEFAULT ''")
        conexion.commit()


def _migrar_cuenta(conexion: sqlite3.Connection) -> None:
    columnas = [fila["name"] for fila in conexion.execute("PRAGMA table_info(cuenta_movimientos)")]
    if "hora" not in columnas:
        conexion.execute("ALTER TABLE cuenta_movimientos ADD COLUMN hora TEXT DEFAULT ''")
        conexion.commit()


def _migrar_clientes(conexion: sqlite3.Connection) -> None:
    columnas = [fila["name"] for fila in conexion.execute("PRAGMA table_info(clientes)")]
    cambios = (
        ("doc_tipo", "INTEGER DEFAULT 99"),
        ("doc_nro", "TEXT DEFAULT ''"),
        ("cond_iva", "INTEGER DEFAULT 5"),
        ("email", "TEXT DEFAULT ''"),
    )
    for columna, definicion in cambios:
        if columna not in columnas:
            conexion.execute(
                f"ALTER TABLE clientes ADD COLUMN {columna} {definicion}")
    conexion.commit()
