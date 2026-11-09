from __future__ import annotations

import hashlib
import hmac
from typing import Self

import bcrypt

from models.entidad import Entidad

COSTOS_BCRYPT = 12


class Usuario(Entidad):
    COLUMNAS: tuple[str, ...] = ("usuario", "password_hash", "permiso")

    PREFIJO_BCRYPT = "$2b$"
    LONGITUD_SHA256 = 64

    PERMISO_ADMIN = "administrador"
    PERMISO_VENDEDOR = "vendedor"
    ETIQUETAS_PERMISO: dict[str, str] = {
        PERMISO_ADMIN: "Administrador",
        PERMISO_VENDEDOR: "Vendedor",
    }

    def __init__(self, nombre: str, password_hash: str, permiso: str = "") -> None:
        if not nombre:
            raise ValueError("El nombre de usuario es obligatorio.")
        self._nombre = nombre
        self._password_hash = password_hash
        self._permiso = permiso or self.PERMISO_VENDEDOR

    @classmethod
    def crear(cls, nombre: str, password: str, permiso: str = "") -> Usuario:
        return cls(nombre, cls.hashear_password(password), permiso)

    @staticmethod
    def hashear_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=COSTOS_BCRYPT)).decode("utf-8")

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def permiso(self) -> str:
        return self._permiso

    @permiso.setter
    def permiso(self, valor: str) -> None:
        self._permiso = (valor if valor in self.ETIQUETAS_PERMISO
                         else self.PERMISO_VENDEDOR)

    def etiqueta_permiso(self) -> str:
        return self.ETIQUETAS_PERMISO.get(self._permiso, "Vendedor")

    @property
    def identificador(self) -> str:
        return self._nombre

    @classmethod
    def es_admin(cls, permiso: str) -> bool:
        return permiso == cls.PERMISO_ADMIN

    def verificar_password(self, password: str) -> bool:
        if self._password_hash.startswith(self.PREFIJO_BCRYPT):
            try:
                return bcrypt.checkpw(password.encode("utf-8"), self._password_hash.encode("utf-8"))
            except ValueError:
                return False
        return hmac.compare_digest(self.hashear_password_viejo(password), self._password_hash)

    def necesita_rehash(self) -> bool:
        return not self._password_hash.startswith(self.PREFIJO_BCRYPT)

    def actualizar_password(self, password: str) -> None:
        self._password_hash = self.hashear_password(password)

    @staticmethod
    def hashear_password_viejo(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, str]:
        return {"usuario": self._nombre, "password_hash": self._password_hash,
                "permiso": self._permiso}

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        return cls(datos.get("usuario") or "", datos.get("password_hash") or "",
                   datos.get("permiso") or "")

    def __str__(self) -> str:
        return self._nombre

    def __repr__(self) -> str:
        return f"Usuario({self._nombre!r})"