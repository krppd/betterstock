from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from config import DATA_DIR
from models.venta_registrada import VentaRegistrada
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db

logger = logging.getLogger(__name__)


def _fila(fila) -> dict[str, str]:
    datos = {clave: "" if fila[clave] is None else str(fila[clave]) for clave in VentaRegistrada.COLUMNAS}
    datos["fecha"] = de_iso(datos["fecha"])
    return datos


_COLUMNAS = (
    "fecha, hora, total, detalle, descuento_global, recargo, monto_recibido,"
    " vuelto, estado, medio_pago, datos_pago, usuario, cliente, pagos"
)

_COLUMNAS_VALORES = _COLUMNAS

_SELECCION = f"id, {_COLUMNAS}"


def _valores(venta: VentaRegistrada) -> tuple:
    datos = venta.to_dict()
    datos["fecha"] = a_iso(datos["fecha"])
    return tuple(datos[columna] for columna in VentaRegistrada.COLUMNAS)


class VentaRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "ventas.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)
        self._errores_lectura: dict[str, dict[str, str]] = {}

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return VentaRegistrada.COLUMNAS

    @property
    def errores_lectura(self) -> list[dict[str, str]]:
        return [dict(error) for error in self._errores_lectura.values()]

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def _leer_filas(self, filas) -> list[VentaRegistrada]:
        ventas: list[VentaRegistrada] = []
        for fila in filas:
            datos = _fila(fila)
            try:
                ventas.append(VentaRegistrada.from_dict(datos))
            except ValueError as error:
                clave = str(fila["id"]) if "id" in fila.keys() else f"{datos['fecha']} {datos['hora']}"
                self._errores_lectura[clave] = {
                    "id": clave,
                    "fecha": datos["fecha"],
                    "hora": datos["hora"],
                    "total": datos["total"],
                    "detalle": datos["detalle"],
                    "motivo": str(error),
                }
                logger.error(
                    "No se pudo leer la venta %s %s (total %s): %s",
                    datos["fecha"], datos["hora"], datos["total"], error,
                )
        return ventas

    def listar(self) -> list[VentaRegistrada]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_SELECCION} FROM ventas ORDER BY id"
            ).fetchall()
        finally:
            conexion.close()
        return self._leer_filas(filas)

    def listar_rango(self, desde: date, hasta: date) -> list[VentaRegistrada]:
        """Lista solo las ventas cuyo fecha cae en [desde, hasta] (fechas ISO)."""
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_SELECCION} FROM ventas"
                " WHERE fecha BETWEEN ? AND ? ORDER BY id",
                (desde.isoformat(), hasta.isoformat()),
            ).fetchall()
        finally:
            conexion.close()
        return self._leer_filas(filas)

    def agregar(self, venta: VentaRegistrada) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute(
                f"INSERT INTO ventas({_COLUMNAS_VALORES})"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                _valores(venta),
            )
            conexion.commit()
        finally:
            conexion.close()

    def buscar(self, identificador: str) -> VentaRegistrada | None:
        fecha_iso, separador, hora = identificador.partition(" ")
        if not separador:
            return None
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                f"SELECT {_SELECCION} FROM ventas"
                " WHERE fecha = ? AND hora = ? ORDER BY id LIMIT 1",
                (fecha_iso, hora),
            ).fetchone()
        finally:
            conexion.close()
        if fila is None:
            return None
        ventas = self._leer_filas([fila])
        return ventas[0] if ventas else None

    def actualizar(self, venta: VentaRegistrada) -> None:
        datos = venta.to_dict()
        fecha_iso = a_iso(datos["fecha"])
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                "SELECT id FROM ventas WHERE fecha = ? AND hora = ?"
                " ORDER BY id LIMIT 1",
                (fecha_iso, datos["hora"]),
            ).fetchone()
            if fila is None:
                conexion.execute(
                    f"INSERT INTO ventas({_COLUMNAS_VALORES})"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    _valores(venta),
                )
            else:
                valores = _valores(venta)
                conexion.execute(
                    "UPDATE ventas SET fecha=?, hora=?, total=?, detalle=?,"
                    " descuento_global=?, recargo=?, monto_recibido=?, vuelto=?,"
                    " estado=?, medio_pago=?, datos_pago=?, usuario=?, cliente=?,"
                    " pagos=?"
                    " WHERE id=?",
                    (*valores, fila["id"]),
                )
            conexion.commit()
        finally:
            conexion.close()

    def del_dia(self, dia: date) -> list[VentaRegistrada]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_SELECCION} FROM ventas"
                " WHERE fecha = ? ORDER BY hora DESC",
                (a_iso(dia.strftime("%d/%m/%Y")),),
            ).fetchall()
        finally:
            conexion.close()
        return self._leer_filas(filas)
