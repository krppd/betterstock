from __future__ import annotations

from datetime import date
from pathlib import Path

from config import DATA_DIR
from models.codigo_anulacion import (
    CodigoAnulacion,
    generar_codigo,
    generar_salt,
    hashear_codigo,
)
from repositories.sqlite import conectar, ruta_db

_COLUMNAS = "id, etiqueta, hash_codigo, salt, creado, activo"


def _a_modelo(fila) -> CodigoAnulacion:
    creado = date.fromisoformat(str(fila["creado"])[:10])
    return CodigoAnulacion(
        identificador=int(fila["id"]),
        etiqueta=str(fila["etiqueta"] or ""),
        hash_codigo=str(fila["hash_codigo"] or ""),
        salt=str(fila["salt"] or ""),
        creado=creado,
        activo=bool(fila["activo"]),
    )


class CodigoRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "betterstock.db") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def generar(self, etiqueta: str = "") -> tuple[CodigoAnulacion, str]:
        codigo = generar_codigo()
        salt = generar_salt()
        hash_codigo = hashear_codigo(codigo, salt)
        creado = date.today()
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            cursor = conexion.execute(
                "INSERT INTO codigos_anulacion(etiqueta, hash_codigo, salt, creado, activo)"
                " VALUES (?, ?, ?, ?, 1)",
                (etiqueta.strip(), hash_codigo, salt, creado.isoformat()),
            )
            conexion.commit()
            identificador = int(cursor.lastrowid)
        finally:
            conexion.close()
        modelo = CodigoAnulacion(
            identificador=identificador,
            etiqueta=etiqueta.strip(),
            hash_codigo=hash_codigo,
            salt=salt,
            creado=creado,
            activo=True,
        )
        return modelo, codigo

    def listar(self) -> list[CodigoAnulacion]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM codigos_anulacion ORDER BY id"
            ).fetchall()
        finally:
            conexion.close()
        return [_a_modelo(fila) for fila in filas]

    def buscar_activo_por_codigo(self, codigo: str) -> CodigoAnulacion | None:
        limpio = (codigo or "").strip()
        if not limpio:
            return None
        for modelo in self.listar():
            if modelo.activo and modelo.verificar(limpio):
                return modelo
        return None

    def revocar(self, identificador: int) -> bool:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            cursor = conexion.execute(
                "UPDATE codigos_anulacion SET activo = 0 WHERE id = ?",
                (int(identificador),),
            )
            conexion.commit()
            return cursor.rowcount > 0
        finally:
            conexion.close()

    def eliminar(self, identificador: int) -> bool:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            cursor = conexion.execute(
                "DELETE FROM codigos_anulacion WHERE id = ?",
                (int(identificador),),
            )
            conexion.commit()
            return cursor.rowcount > 0
        finally:
            conexion.close()
