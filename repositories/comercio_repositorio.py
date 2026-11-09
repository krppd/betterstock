from __future__ import annotations

from pathlib import Path

from config import DATA_DIR
from models.comercio import Comercio
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db


def _fila(fila) -> dict[str, str]:
    return {clave: "" if fila[clave] is None else str(fila[clave]) for clave in Comercio.COLUMNAS}


_COLUMNAS = "nombre, direccion, cuit, telefono"


class ComercioRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "comercio.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return Comercio.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def guardar(self, comercio: Comercio) -> None:
        datos = comercio.to_dict()
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute("DELETE FROM comercio")
            conexion.execute(
                "INSERT INTO comercio(nombre, direccion, cuit, telefono)"
                " VALUES (?, ?, ?, ?)",
                tuple(datos[columna] for columna in Comercio.COLUMNAS),
            )
            conexion.commit()
        finally:
            conexion.close()

    def obtener(self) -> Comercio | None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM comercio ORDER BY rowid"
            ).fetchall()
        finally:
            conexion.close()
        for fila in filas:
            datos = _fila(fila)
            if datos["nombre"]:
                return Comercio.from_dict(datos)
        return None

    def esta_configurado(self) -> bool:
        return self.obtener() is not None
