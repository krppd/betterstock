from __future__ import annotations

import os
import shutil
import sqlite3
import warnings
from datetime import datetime
from pathlib import Path

from config import DATA_DIR, OUTPUT_DIR
from repositories.sqlite import ruta_db

PREFIJO = "betterstock_"
SUFIJO = ".db"
PATRON = f"{PREFIJO}*{SUFIJO}"
CANTIDAD_POR_DEFECTO = 15
NOMBRE_CARPETA = "backups"


class ErrorBackup(RuntimeError):
    pass


class ServicioBackup:

    def __init__(self, base: str | Path | None = None, directorio: str | Path | None = None) -> None:
        self._ruta_db = ruta_db(base if base is not None else DATA_DIR)
        self._directorio = Path(directorio) if directorio is not None else None
        self._mensajes: list[str] = []

    @property
    def ruta_db(self) -> Path:
        return self._ruta_db

    @property
    def mensajes(self) -> list[str]:
        return list(self._mensajes)

    def sacar_mensajes(self) -> list[str]:
        mensajes = list(dict.fromkeys(self._mensajes))
        self._mensajes.clear()
        return mensajes

    def directorio_backups(self) -> Path:
        return self._directorio if self._directorio is not None else OUTPUT_DIR / NOMBRE_CARPETA

    def generar(self) -> Path:
        destino = self._nombre_disponible()
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not self._ruta_db.is_file():
            raise ErrorBackup(f"No se encontró la base de datos en {self._ruta_db}.")

        origen = self._abrir_lectura()
        copia = sqlite3.connect(str(destino))
        try:
            origen.backup(copia)
        except sqlite3.Error as error:
            copia.close()
            destino.unlink(missing_ok=True)
            origen.close()
            raise ErrorBackup(f"No se pudo copiar la base de datos: {error}") from error
        copia.close()
        origen.close()
        self._avisar_copia(destino)
        return destino

    def rotar(self, cantidad: int = CANTIDAD_POR_DEFECTO) -> list[Path]:
        if cantidad < 0:
            raise ErrorBackup("La cantidad de copias a conservar no puede ser negativa.")
        self.directorio_backups().mkdir(parents=True, exist_ok=True)
        for viejo in self.listar()[cantidad:]:
            try:
                viejo.unlink()
            except OSError as error:
                warnings.warn(f"No se pudo borrar la copia {viejo.name}: {error}", RuntimeWarning)
        copias = self.listar()[:cantidad]
        if copias:
            self._avisar_copia(copias[0])
        return copias

    def listar(self) -> list[Path]:
        carpeta = self.directorio_backups()
        if not carpeta.is_dir():
            return []
        encontradas = [ruta for ruta in carpeta.glob(PATRON) if ruta.is_file()]
        return sorted(encontradas, key=lambda ruta: ruta.stat().st_mtime, reverse=True)

    def restaurar(self, origen: str | Path) -> None:
        origen = Path(origen)
        if not origen.is_file():
            raise ErrorBackup(f"No se encontró la copia {origen}.")
        self._validar(origen)

        if self._ruta_db.is_file():
            try:
                self.generar()
            except ErrorBackup as error:
                raise ErrorBackup(
                    f"No se pudo respaldar la base actual, se aborta la restauración: {error}"
                ) from error

        destino = self._ruta_db
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_name(destino.name + ".restaurando")
        temporal.unlink(missing_ok=True)
        try:
            shutil.copy2(origen, temporal)
            os.replace(temporal, destino)
        except OSError as error:
            temporal.unlink(missing_ok=True)
            raise ErrorBackup(f"No se pudo restaurar la copia: {error}") from error
        for auxiliar in self._auxiliares(destino):
            auxiliar.unlink(missing_ok=True)

    def total(self) -> int:
        return len(self.listar())

    @staticmethod
    def _auxiliares(destino: Path) -> list[Path]:
        return [Path(f"{destino}-wal"), Path(f"{destino}-shm")]

    def _avisar_copia(self, ruta: Path) -> None:
        return

    def _abrir_lectura(self) -> sqlite3.Connection:
        uri = f"file:{self._ruta_db.as_posix()}?mode=ro"
        try:
            conexion = sqlite3.connect(uri, uri=True)
            conexion.execute("SELECT 1 FROM sqlite_master LIMIT 1")
            return conexion
        except sqlite3.Error:
            return sqlite3.connect(str(self._ruta_db))

    @staticmethod
    def _validar(origen: Path) -> None:
        conexion = None
        try:
            conexion = sqlite3.connect(f"file:{origen.as_posix()}?mode=ro", uri=True)
            conexion.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
            resultado = conexion.execute("PRAGMA integrity_check").fetchone()
        except sqlite3.Error as error:
            raise ErrorBackup(f"La copia {origen.name} no es una base de datos válida: {error}") from error
        finally:
            if conexion is not None:
                conexion.close()
        if not resultado or str(resultado[0]).lower() != "ok":
            raise ErrorBackup(f"La copia {origen.name} está dañada y no se puede restaurar.")

    def _nombre_disponible(self) -> Path:
        carpeta = self.directorio_backups()
        momento = datetime.now()
        base = f"{PREFIJO}{momento:%Y%m%d}"
        if not (carpeta / f"{base}{SUFIJO}").exists():
            return carpeta / f"{base}{SUFIJO}"
        con_hora = carpeta / f"{base}_{momento:%H%M%S}{SUFIJO}"
        if not con_hora.exists():
            return con_hora
        numero = 2
        while (carpeta / f"{base}_{momento:%H%M%S}_{numero}{SUFIJO}").exists():
            numero += 1
        return carpeta / f"{base}_{momento:%H%M%S}_{numero}{SUFIJO}"


def tamano_legible(ruta: Path) -> str:
    try:
        bytes_totales = max(ruta.stat().st_size, 0)
    except OSError:
        return "-"
    if bytes_totales < 1024:
        return f"{bytes_totales} B"
    if bytes_totales < 1024 * 1024:
        return f"{bytes_totales / 1024:.0f} KB"
    return f"{bytes_totales / (1024 * 1024):.1f} MB"