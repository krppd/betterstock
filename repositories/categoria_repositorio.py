from __future__ import annotations

from pathlib import Path

from config import DATA_DIR
from models.categoria import Categoria
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db


class CategoriaRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "categorias.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return Categoria.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def listar(self) -> list[Categoria]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute("SELECT nombre FROM categorias ORDER BY rowid").fetchall()
        finally:
            conexion.close()
        categorias: list[Categoria] = []
        for fila in filas:
            nombre = "" if fila["nombre"] is None else str(fila["nombre"])
            if nombre.strip():
                categorias.append(Categoria.from_dict({"nombre": nombre}))
        return categorias

    def existe(self, nombre: str) -> bool:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                "SELECT 1 FROM categorias WHERE nombre = ? COLLATE NOCASE",
                (nombre.strip(),),
            ).fetchone()
        finally:
            conexion.close()
        return fila is not None

    def agregar(self, categoria: Categoria) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute(
                "INSERT INTO categorias(nombre) VALUES (?)", (categoria.nombre,)
            )
            conexion.commit()
        finally:
            conexion.close()
