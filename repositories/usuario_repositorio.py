from __future__ import annotations

from pathlib import Path

from config import DATA_DIR
from models.usuario import Usuario
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db


def _fila(fila) -> dict[str, str]:
    return {clave: "" if fila[clave] is None else str(fila[clave]) for clave in Usuario.COLUMNAS}


_COLUMNAS = "usuario, password_hash, permiso"


class UsuarioRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "usuarios.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return Usuario.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def listar(self) -> list[Usuario]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM usuarios ORDER BY rowid"
            ).fetchall()
        finally:
            conexion.close()
        return [Usuario.from_dict(_fila(fila)) for fila in filas]

    def buscar(self, nombre: str) -> Usuario | None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                f"SELECT {_COLUMNAS} FROM usuarios WHERE usuario = ?", (nombre,)
            ).fetchone()
        finally:
            conexion.close()
        return Usuario.from_dict(_fila(fila)) if fila is not None else None

    def agregar(self, usuario: Usuario) -> None:
        if self.buscar(usuario.nombre) is not None:
            raise ValueError(f"Ya existe el usuario {usuario.nombre!r}.")
        datos = usuario.to_dict()
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute(
                "INSERT INTO usuarios(usuario, password_hash, permiso) VALUES (?, ?, ?)",
                (usuario.nombre, datos["password_hash"], datos["permiso"]),
            )
            conexion.commit()
        finally:
            conexion.close()

    def guardar(self, usuario: Usuario) -> None:
        datos = usuario.to_dict()
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute(
                "INSERT INTO usuarios(usuario, password_hash, permiso) VALUES (?, ?, ?)"
                " ON CONFLICT(usuario) DO UPDATE SET"
                " password_hash=excluded.password_hash,"
                " permiso=excluded.permiso",
                (usuario.nombre, datos["password_hash"], datos["permiso"]),
            )
            conexion.commit()
        finally:
            conexion.close()
