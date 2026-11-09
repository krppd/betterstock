
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Self


class Entidad(ABC):

    @property
    @abstractmethod
    def identificador(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, str]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        pass

    @staticmethod
    def _a_entero(valor: Any, defecto: int = 0) -> int:
        try:
            return int(float(valor))
        except (TypeError, ValueError):
            return defecto

    @staticmethod
    def _a_decimal(valor: Any, defecto: float = 0.0) -> float:
        try:
            return float(valor)
        except (TypeError, ValueError):
            return defecto

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.to_dict()!r})"
