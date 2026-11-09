from __future__ import annotations

from pathlib import Path

from config import DATA_DIR
from models.cliente import Cliente
from repositories.sqlite import a_iso, conectar, de_iso, ruta_db


def _fila(fila) -> dict[str, str]:
    return {clave: "" if fila[clave] is None else str(fila[clave]) for clave in Cliente.COLUMNAS}


_COLUMNAS = (
    "codigo, nombre, telefono, limite, activo,"
    " doc_tipo, doc_nro, cond_iva, email"
)


class ClienteRepositorio:
    def __init__(self, ruta_archivo: str | Path = DATA_DIR / "clientes.csv") -> None:
        self._ruta_archivo = Path(ruta_archivo)

    @property
    def ruta_archivo(self) -> Path:
        return self._ruta_archivo

    @property
    def columnas(self) -> tuple[str, ...]:
        return Cliente.COLUMNAS

    def inicializar(self) -> None:
        conexion = conectar(ruta_db(self._ruta_archivo))
        conexion.close()

    def listar(self) -> list[Cliente]:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            filas = conexion.execute(
                f"SELECT {_COLUMNAS} FROM clientes ORDER BY codigo"
            ).fetchall()
        finally:
            conexion.close()
        clientes: list[Cliente] = []
        for fila in filas:
            try:
                clientes.append(Cliente.from_dict(_fila(fila)))
            except ValueError:
                continue
        return clientes

    def buscar(self, codigo: str) -> Cliente | None:
        buscado = str(codigo).strip()
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                f"SELECT {_COLUMNAS} FROM clientes WHERE codigo = ?", (buscado,)
            ).fetchone()
        finally:
            conexion.close()
        if fila is None:
            return None
        try:
            return Cliente.from_dict(_fila(fila))
        except ValueError:
            return None

    def existe_nombre(self, nombre: str, excluir: str = "") -> bool:
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            fila = conexion.execute(
                "SELECT 1 FROM clientes"
                " WHERE nombre = ? COLLATE NOCASE AND codigo != ?",
                (nombre.strip(), str(excluir).strip()),
            ).fetchone()
        finally:
            conexion.close()
        return fila is not None

    def agregar(self, cliente: Cliente) -> Cliente:
        if cliente.codigo is not None:
            raise ValueError("El cliente ya tiene un código asignado.")
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            cursor = conexion.execute(
                "INSERT INTO clientes(nombre, telefono, limite, activo,"
                " doc_tipo, doc_nro, cond_iva, email)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    cliente.nombre,
                    cliente.telefono,
                    cliente.limite,
                    1 if cliente.activo else 0,
                    cliente.doc_tipo,
                    cliente.doc_nro,
                    cliente.cond_iva,
                    cliente.email,
                ),
            )
            cliente.asignar_codigo(cursor.lastrowid)
            conexion.commit()
        finally:
            conexion.close()
        return cliente

    def actualizar(self, cliente: Cliente) -> None:
        if cliente.codigo is None:
            self.agregar(cliente)
            return
        conexion = conectar(ruta_db(self._ruta_archivo))
        try:
            conexion.execute(
                "INSERT INTO clientes(codigo, nombre, telefono, limite, activo,"
                " doc_tipo, doc_nro, cond_iva, email)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(codigo) DO UPDATE SET"
                " nombre=excluded.nombre, telefono=excluded.telefono,"
                " limite=excluded.limite, activo=excluded.activo,"
                " doc_tipo=excluded.doc_tipo, doc_nro=excluded.doc_nro,"
                " cond_iva=excluded.cond_iva, email=excluded.email",
                (
                    cliente.codigo,
                    cliente.nombre,
                    cliente.telefono,
                    cliente.limite,
                    1 if cliente.activo else 0,
                    cliente.doc_tipo,
                    cliente.doc_nro,
                    cliente.cond_iva,
                    cliente.email,
                ),
            )
            conexion.commit()
        finally:
            conexion.close()
