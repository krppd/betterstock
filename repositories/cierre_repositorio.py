from __future__ import annotations

from datetime import date
from pathlib import Path

from config import DATA_DIR
from models.cierre import CierreRegistrado
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db


def _fila(fila) -> dict[str, str]:
    datos = {clave: "" if fila[clave] is None else str(fila[clave]) for clave in CierreRegistrado.COLUMNAS}
    datos["fecha"] = de_iso(datos["fecha"])
    return datos


_COLUMNAS = (
    "fecha, hora, cantidad_ventas, total_esperado, efectivo_esperado, declarado,"
    " diferencia, sobrante, faltante, notas, medios, usuario"
)


class CierreRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "cierres.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return CierreRegistrado.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def listar(self) -> list[CierreRegistrado]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM cierres ORDER BY id"
            ).fetchall()
        finally:
            conexion.close()
        cierres: list[CierreRegistrado] = []
        for fila in filas:
            try:
                cierres.append(CierreRegistrado.from_dict(_fila(fila)))
            except ValueError:
                continue
        return sorted(cierres, key=lambda c: (c.fecha, c.hora))

    def agregar(self, cierre: CierreRegistrado) -> None:
        datos = cierre.to_dict()
        datos["fecha"] = a_iso(datos["fecha"])
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute(
                f"INSERT INTO cierres({_COLUMNAS})"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tuple(datos[columna] for columna in CierreRegistrado.COLUMNAS),
            )
            conexion.commit()
        finally:
            conexion.close()

    def del_dia(self, dia: date) -> list[CierreRegistrado]:
        return [c for c in reversed(self.listar()) if c.fecha == dia]

    def ya_cerrado(self, dia: date) -> bool:
        return any(c.fecha == dia for c in self.listar())
