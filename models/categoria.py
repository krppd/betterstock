"""Entidad Categoria: el rubro con el que se agrupan los productos."""

from __future__ import annotations

from typing import Self

from models.entidad import Entidad


class Categoria(Entidad):
    """Categoría de productos. Los productos la guardan por su nombre."""

    COLUMNAS: tuple[str, ...] = ("nombre",)

    def __init__(self, nombre: str) -> None:
        """Crea la categoría. El nombre es obligatorio y se guarda sin espacios a los costados."""
        if not nombre.strip():
            raise ValueError("El nombre de la categoría es obligatorio.")
        self._nombre = nombre.strip()

    @property
    def nombre(self) -> str:
        """Nombre de la categoría."""
        return self._nombre

    @property
    def identificador(self) -> str:
        """El nombre identifica a la categoría."""
        return self._nombre

    def to_dict(self) -> dict[str, str]:
        """Convierte la categoría en una fila de ``categorias.csv``."""
        return {"nombre": self._nombre}

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        """Crea una categoría a partir de una fila de ``categorias.csv``."""
        return cls(datos.get("nombre") or "")

    def __str__(self) -> str:
        return self._nombre
