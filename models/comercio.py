from __future__ import annotations

from typing import Self

from models.entidad import Entidad
from models.validacion_identificador import es_cuit_valido, normalizar_cuit


class Comercio(Entidad):
    COLUMNAS: tuple[str, ...] = ("nombre", "direccion", "cuit", "telefono")

    def __init__(self, nombre: str, direccion: str, cuit: str, telefono: str) -> None:
        if not nombre.strip():
            raise ValueError("El nombre del comercio es obligatorio.")
        cuit = normalizar_cuit(cuit)
        if cuit and not es_cuit_valido(cuit):
            raise ValueError("El CUIT no es válido: revisá los dígitos.")
        self._nombre = nombre.strip()
        self._direccion = direccion.strip()
        self._cuit = cuit
        self._telefono = telefono.strip()

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def direccion(self) -> str:
        return self._direccion

    @property
    def cuit(self) -> str:
        return self._cuit

    @property
    def telefono(self) -> str:
        return self._telefono

    @property
    def identificador(self) -> str:
        return self._nombre

    def to_dict(self) -> dict[str, str]:
        return {
            "nombre": self._nombre,
            "direccion": self._direccion,
            "cuit": self._cuit,
            "telefono": self._telefono,
        }

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        return cls(
            datos.get("nombre") or "",
            datos.get("direccion") or "",
            datos.get("cuit") or "",
            datos.get("telefono") or "",
        )

    def __str__(self) -> str:
        return self._nombre