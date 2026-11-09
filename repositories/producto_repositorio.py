from __future__ import annotations

import unicodedata
from pathlib import Path

from config import DATA_DIR
from models.producto import Producto
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db


def _fila(fila) -> dict[str, str]:
    return {clave: "" if fila[clave] is None else str(fila[clave]) for clave in Producto.COLUMNAS}


def _escapar(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _normalizar(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).casefold()


_COLUMNAS = (
    "codigo, nombre, categoria, unidad_medida, precio_costo, precio_venta,"
    " stock_actual, stock_minimo, alicuota_iva, precio_oferta,"
    " fecha_vencimiento"
)

_COLUMNAS_CANTIDAD = ("stock_actual", "stock_minimo")


class ProductoRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "productos.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return Producto.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def listar(self) -> list[Producto]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM productos ORDER BY rowid"
            ).fetchall()
        finally:
            conexion.close()
        return [Producto.from_dict(_fila(fila)) for fila in filas]

    def buscar(self, codigo: str) -> Producto | None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                f"SELECT {_COLUMNAS} FROM productos WHERE codigo = ?", (codigo,)
            ).fetchone()
        finally:
            conexion.close()
        return Producto.from_dict(_fila(fila)) if fila is not None else None

    def buscar_por_texto(self, texto: str) -> list[Producto]:
        pares = [(crudo, _normalizar(crudo)) for crudo in texto.split()]
        pares = [(crudo, normal) for crudo, normal in pares if normal]
        if not pares:
            return self.listar()
        condicion = " AND ".join(
            "(normalizar(codigo) LIKE ? ESCAPE '\\' COLLATE NOCASE"
            " OR normalizar(nombre) LIKE ? ESCAPE '\\' COLLATE NOCASE)"
            for _ in pares
        )
        parametros: list[str] = []
        for _, normal in pares:
            patron = f"%{_escapar(normal)}%"
            parametros.extend((patron, patron))
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.create_function("normalizar", 1, _normalizar)
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM productos WHERE {condicion} ORDER BY rowid",
                parametros,
            ).fetchall()
        finally:
            conexion.close()
        candidatos = [Producto.from_dict(_fila(fila)) for fila in filas]
        return [
            producto
            for producto in candidatos
            if all(
                normal in _normalizar(producto.codigo)
                or normal in _normalizar(producto.nombre)
                for _, normal in pares
            )
        ][:50]

    def guardar(self, producto: Producto) -> None:
        datos = producto.to_dict()
        valores = [
            float(datos[columna]) if columna in _COLUMNAS_CANTIDAD else datos[columna]
            for columna in Producto.COLUMNAS
        ]
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute(
                "INSERT INTO productos(codigo, nombre, categoria, unidad_medida,"
                " precio_costo, precio_venta, stock_actual, stock_minimo,"
                " alicuota_iva, precio_oferta, fecha_vencimiento)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(codigo) DO UPDATE SET"
                " nombre=excluded.nombre, categoria=excluded.categoria,"
                " unidad_medida=excluded.unidad_medida,"
                " precio_costo=excluded.precio_costo,"
                " precio_venta=excluded.precio_venta,"
                " stock_actual=excluded.stock_actual,"
                " stock_minimo=excluded.stock_minimo,"
                " alicuota_iva=excluded.alicuota_iva,"
                " precio_oferta=excluded.precio_oferta,"
                " fecha_vencimiento=excluded.fecha_vencimiento",
                tuple(valores),
            )
            conexion.commit()
        finally:
            conexion.close()

    def eliminar(self, codigo: str) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute("DELETE FROM productos WHERE codigo = ?", (codigo,))
            conexion.commit()
        finally:
            conexion.close()

    def actualizar_precios(self, precios: dict[str, float]) -> None:
        if not precios:
            return
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.executemany(
                "UPDATE productos SET precio_venta = ? WHERE codigo = ?",
                [(float(precio), codigo) for codigo, precio in precios.items()],
            )
            conexion.commit()
        finally:
            conexion.close()
