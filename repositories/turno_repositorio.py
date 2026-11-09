from __future__ import annotations

from datetime import date
from pathlib import Path

from config import DATA_DIR
from models.turno import Turno
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db


def _fila(fila) -> dict[str, str]:
    datos = {clave: "" if fila[clave] is None else str(fila[clave])
             for clave in Turno.COLUMNAS}
    datos["fecha_apertura"] = de_iso(datos["fecha_apertura"])
    if datos["fecha_cierre"]:
        datos["fecha_cierre"] = de_iso(datos["fecha_cierre"])
    return datos


_COLUMNAS = (
    "id, fecha_apertura, hora_apertura, usuario_apertura, fondo_inicial,"
    " fecha_cierre, hora_cierre, usuario_cierre, cantidad_ventas,"
    " total_esperado, efectivo_esperado, declarado, diferencia, sobrante,"
    " faltante, medios, notas, estado"
)

_COLUMNAS_INSERT = tuple(
    columna for columna in Turno.COLUMNAS if columna != "id")


class TurnoRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "turnos.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return Turno.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def listar(self) -> list[Turno]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM turnos ORDER BY id"
            ).fetchall()
        finally:
            conexion.close()
        turnos: list[Turno] = []
        for fila in filas:
            try:
                turnos.append(Turno.from_dict(_fila(fila)))
            except ValueError:
                continue
        return turnos

    def buscar(self, id_turno: int) -> Turno | None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                f"SELECT {_COLUMNAS} FROM turnos WHERE id = ?",
                (int(id_turno),),
            ).fetchone()
        finally:
            conexion.close()
        if fila is None:
            return None
        try:
            return Turno.from_dict(_fila(fila))
        except ValueError:
            return None

    def abierto(self) -> Turno | None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                f"SELECT {_COLUMNAS} FROM turnos"
                " WHERE estado = ? ORDER BY id DESC LIMIT 1",
                (Turno.ESTADO_ABIERTO,),
            ).fetchone()
        finally:
            conexion.close()
        if fila is None:
            return None
        try:
            return Turno.from_dict(_fila(fila))
        except ValueError:
            return None

    def agregar(self, turno: Turno) -> None:
        if turno.id_turno is not None:
            raise ValueError("El turno ya tiene un número asignado.")
        datos = turno.to_dict()
        datos["fecha_apertura"] = a_iso(datos["fecha_apertura"])
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            marcadores = ", ".join("?" for _ in _COLUMNAS_INSERT)
            cursor = conexion.execute(
                f"INSERT INTO turnos({', '.join(_COLUMNAS_INSERT)})"
                f" VALUES ({marcadores})",
                tuple(datos[columna] for columna in _COLUMNAS_INSERT),
            )
            turno.asignar_id(cursor.lastrowid)
            conexion.commit()
        finally:
            conexion.close()

    def actualizar(self, turno: Turno) -> None:
        if turno.id_turno is None:
            raise ValueError("El turno no tiene un número asignado.")
        datos = turno.to_dict()
        datos["fecha_apertura"] = a_iso(datos["fecha_apertura"])
        if datos["fecha_cierre"]:
            datos["fecha_cierre"] = a_iso(datos["fecha_cierre"])
        asignaciones = ", ".join(
            f"{columna} = ?" for columna in _COLUMNAS_INSERT)
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute(
                f"UPDATE turnos SET {asignaciones} WHERE id = ?",
                (*tuple(datos[columna] for columna in _COLUMNAS_INSERT),
                 turno.id_turno),
            )
            conexion.commit()
        finally:
            conexion.close()

    def historial(self, limite: int | None = None) -> list[Turno]:
        turnos = list(reversed(self.listar()))
        if limite is not None:
            turnos = turnos[:max(limite, 0)]
        return turnos

    def del_dia(self, dia: date) -> list[Turno]:
        return [turno for turno in reversed(self.listar())
                if turno.fecha_apertura == dia]
