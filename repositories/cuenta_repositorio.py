from __future__ import annotations

from datetime import date
from pathlib import Path

from config import DATA_DIR
from models.movimiento_cuenta import MovimientoCuenta
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db


def _fila(fila) -> dict[str, str]:
    datos = {clave: "" if fila[clave] is None else str(fila[clave]) for clave in MovimientoCuenta.COLUMNAS}
    datos["fecha"] = de_iso(datos["fecha"])
    return datos


_COLUMNAS = "id, fecha, cliente, tipo, importe, detalle, medio, usuario, hora"


class CuentaRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "cuenta_movimientos.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return MovimientoCuenta.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def listar(self) -> list[MovimientoCuenta]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM cuenta_movimientos ORDER BY id"
            ).fetchall()
        finally:
            conexion.close()
        movimientos: list[MovimientoCuenta] = []
        for fila in filas:
            try:
                movimientos.append(MovimientoCuenta.from_dict(_fila(fila)))
            except ValueError:
                continue
        return movimientos

    def por_cliente(self, codigo: str) -> list[MovimientoCuenta]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM cuenta_movimientos"
                " WHERE cliente = ? ORDER BY id",
                (str(codigo).strip(),),
            ).fetchall()
        finally:
            conexion.close()
        movimientos: list[MovimientoCuenta] = []
        for fila in filas:
            try:
                movimientos.append(MovimientoCuenta.from_dict(_fila(fila)))
            except ValueError:
                continue
        return movimientos

    def movimientos_del_dia(self, dia: date) -> list[MovimientoCuenta]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM cuenta_movimientos"
                " WHERE fecha = ? ORDER BY id",
                (a_iso(dia.strftime("%d/%m/%Y")),),
            ).fetchall()
        finally:
            conexion.close()
        movimientos: list[MovimientoCuenta] = []
        for fila in filas:
            try:
                movimientos.append(MovimientoCuenta.from_dict(_fila(fila)))
            except ValueError:
                continue
        return movimientos

    def agregar(self, movimiento: MovimientoCuenta) -> MovimientoCuenta:
        if movimiento.id_movimiento is not None:
            raise ValueError("El movimiento ya tiene un número asignado.")
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            cursor = conexion.execute(
                "INSERT INTO cuenta_movimientos(fecha, cliente, tipo, importe,"
                " detalle, medio, usuario, hora) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    a_iso(movimiento.fecha_texto),
                    movimiento.cliente,
                    movimiento.tipo,
                    movimiento.importe,
                    movimiento.detalle,
                    movimiento.medio,
                    movimiento.usuario,
                    movimiento.hora,
                ),
            )
            movimiento.asignar_id(cursor.lastrowid)
            conexion.commit()
        finally:
            conexion.close()
        return movimiento

    def agregar_varios(self, movimientos: list[MovimientoCuenta]) -> list[MovimientoCuenta]:
        """Inserta todos en una sola transacción: si uno falla, no queda ninguno."""
        for movimiento in movimientos:
            if movimiento.id_movimiento is not None:
                raise ValueError("El movimiento ya tiene un número asignado.")
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            for movimiento in movimientos:
                cursor = conexion.execute(
                    "INSERT INTO cuenta_movimientos(fecha, cliente, tipo, importe,"
                    " detalle, medio, usuario, hora) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        a_iso(movimiento.fecha_texto),
                        movimiento.cliente,
                        movimiento.tipo,
                        movimiento.importe,
                        movimiento.detalle,
                        movimiento.medio,
                        movimiento.usuario,
                        movimiento.hora,
                    ),
                )
                movimiento.asignar_id(cursor.lastrowid)
            conexion.commit()
        finally:
            conexion.close()
        return movimientos
