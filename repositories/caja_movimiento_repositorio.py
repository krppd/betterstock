from __future__ import annotations

from datetime import date
from pathlib import Path

from config import DATA_DIR
from models.caja_movimiento import CajaMovimiento
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db

_COLUMNAS = (
    "id, fecha, hora, tipo, concepto, categoria, importe, usuario, "
    "anulado, anulado_por, motivo_anulacion"
)


def _fila(fila) -> dict[str, str]:
    datos = {clave: "" if fila[clave] is None else str(fila[clave])
             for clave in CajaMovimiento.COLUMNAS}
    datos["fecha"] = de_iso(datos["fecha"])
    return datos


class CajaMovimientoRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "caja_movimientos.db") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return CajaMovimiento.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def listar(self) -> list[CajaMovimiento]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM caja_movimientos ORDER BY id"
            ).fetchall()
        finally:
            conexion.close()
        movimientos: list[CajaMovimiento] = []
        for fila in filas:
            try:
                movimientos.append(CajaMovimiento.from_dict(_fila(fila)))
            except ValueError:
                continue
        return movimientos

    def listar_del_dia(self, dia: date) -> list[CajaMovimiento]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM caja_movimientos "
                "WHERE fecha = ? ORDER BY id",
                (a_iso(dia.strftime("%d/%m/%Y")),),
            ).fetchall()
        finally:
            conexion.close()
        movimientos: list[CajaMovimiento] = []
        for fila in filas:
            try:
                movimientos.append(CajaMovimiento.from_dict(_fila(fila)))
            except ValueError:
                continue
        return movimientos

    def obtener(self, id_movimiento: int) -> CajaMovimiento | None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                f"SELECT {_COLUMNAS} FROM caja_movimientos WHERE id = ?",
                (id_movimiento,),
            ).fetchone()
        finally:
            conexion.close()
        if fila is None:
            return None
        return CajaMovimiento.from_dict(_fila(fila))

    def agregar(self, movimiento: CajaMovimiento) -> CajaMovimiento:
        if movimiento.id_movimiento is not None:
            raise ValueError("El movimiento ya tiene un número asignado.")
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            cursor = conexion.execute(
                "INSERT INTO caja_movimientos("
                "fecha, hora, tipo, concepto, categoria, importe, usuario, "
                "anulado, anulado_por, motivo_anulacion) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    a_iso(movimiento.fecha_texto),
                    movimiento.hora,
                    movimiento.tipo,
                    movimiento.concepto,
                    movimiento.categoria,
                    movimiento.importe,
                    movimiento.usuario,
                    1 if movimiento.anulado else 0,
                    movimiento.anulado_por,
                    movimiento.motivo_anulacion,
                ),
            )
            movimiento.asignar_id(cursor.lastrowid)
            conexion.commit()
        finally:
            conexion.close()
        return movimiento

    def actualizar(self, movimiento: CajaMovimiento) -> None:
        if movimiento.id_movimiento is None:
            raise ValueError("El movimiento no tiene un número asignado.")
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute(
                "UPDATE caja_movimientos SET "
                "fecha = ?, hora = ?, tipo = ?, concepto = ?, categoria = ?, "
                "importe = ?, usuario = ?, anulado = ?, anulado_por = ?, "
                "motivo_anulacion = ? WHERE id = ?",
                (
                    a_iso(movimiento.fecha_texto),
                    movimiento.hora,
                    movimiento.tipo,
                    movimiento.concepto,
                    movimiento.categoria,
                    movimiento.importe,
                    movimiento.usuario,
                    1 if movimiento.anulado else 0,
                    movimiento.anulado_por,
                    movimiento.motivo_anulacion,
                    movimiento.id_movimiento,
                ),
            )
            conexion.commit()
        finally:
            conexion.close()

    def eliminar(self, id_movimiento: int) -> None:
        raise RuntimeError("No se pueden borrar movimientos de caja.")
