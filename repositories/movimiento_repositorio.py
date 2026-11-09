from __future__ import annotations

from pathlib import Path

from config import DATA_DIR
from models.movimiento import Movimiento
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db


def _fila(fila) -> dict[str, str]:
    datos = {clave: "" if fila[clave] is None else str(fila[clave]) for clave in Movimiento.COLUMNAS}
    datos["fecha"] = de_iso(datos["fecha"])
    return datos


_COLUMNAS = "id_movimiento, fecha, codigo_producto, tipo, cantidad, motivo"


class MovimientoRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "movimientos.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return Movimiento.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def listar(self) -> list[Movimiento]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM movimientos ORDER BY id_movimiento"
            ).fetchall()
        finally:
            conexion.close()
        movimientos: list[Movimiento] = []
        for fila in filas:
            try:
                movimientos.append(Movimiento.from_dict(_fila(fila)))
            except ValueError:
                continue
        return movimientos

    def agregar(self, movimiento: Movimiento) -> Movimiento:
        if movimiento.id_movimiento is not None:
            raise ValueError("El movimiento ya tiene un número asignado.")
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            cursor = conexion.execute(
                "INSERT INTO movimientos(fecha, codigo_producto, tipo, cantidad, motivo)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    a_iso(movimiento.fecha_texto),
                    movimiento.codigo_producto,
                    movimiento.tipo,
                    movimiento.cantidad,
                    movimiento.motivo,
                ),
            )
            movimiento.asignar_id(cursor.lastrowid)
            conexion.commit()
        finally:
            conexion.close()
        return movimiento
