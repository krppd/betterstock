from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from config import DATA_DIR
from repositories.sqlite import conectar, ruta_db

_COLUMNAS = "id, fecha, archivo, creados, actualizados, omitidos, errores, backup"


class ImportacionRepositorio:

    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "importaciones.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def registrar(
        self,
        archivo: str,
        creados: int = 0,
        actualizados: int = 0,
        omitidos: int = 0,
        errores: int = 0,
        backup: str = "",
        fecha: str | None = None,
        conexion: sqlite3.Connection | None = None,
    ) -> int:
        momento = fecha or datetime.now().isoformat(timespec="seconds")
        if conexion is not None:
            cursor = conexion.execute(
                "INSERT INTO importaciones(fecha, archivo, creados, actualizados,"
                " omitidos, errores, backup) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (momento, str(archivo), int(creados), int(actualizados),
                 int(omitidos), int(errores), str(backup)),
            )
            return int(cursor.lastrowid or 0)
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            cursor = conexion.execute(
                "INSERT INTO importaciones(fecha, archivo, creados, actualizados,"
                " omitidos, errores, backup) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (momento, str(archivo), int(creados), int(actualizados),
                 int(omitidos), int(errores), str(backup)),
            )
            conexion.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conexion.close()

    def historial(self) -> list[dict]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM importaciones ORDER BY id DESC").fetchall()
        finally:
            conexion.close()
        return [dict(fila) for fila in filas]

    def ultima(self) -> dict | None:
        registros = self.historial()
        return registros[0] if registros else None

    def obtener(self, id_importacion: int) -> dict | None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                f"SELECT {_COLUMNAS} FROM importaciones WHERE id = ?",
                (int(id_importacion),),
            ).fetchone()
        finally:
            conexion.close()
        return dict(fila) if fila is not None else None

    def total(self) -> int:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute("SELECT COUNT(*) FROM importaciones").fetchone()
        finally:
            conexion.close()
        return int(fila[0]) if fila else 0

    def eliminar(self, id_importacion: int) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute("DELETE FROM importaciones WHERE id = ?", (int(id_importacion),))
            conexion.commit()
        finally:
            conexion.close()
