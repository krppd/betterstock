from __future__ import annotations

import math
import warnings
from typing import Self

from models.entidad import Entidad
from utils.formato import formatear_dinero


class Cliente(Entidad):
    COLUMNAS: tuple[str, ...] = (
        "codigo", "nombre", "telefono", "limite", "activo",
        "doc_tipo", "doc_nro", "cond_iva", "email",
    )

    LIMITE_MAXIMO: float = 99_999_999.00

    def __init__(self, nombre: str, telefono: str = "", limite: float = 0.0,
                 activo: bool = True, codigo: int | None = None,
                 doc_tipo: int = 99, doc_nro: str = "", cond_iva: int = 5,
                 email: str = "") -> None:
        if not nombre.strip():
            raise ValueError("El nombre del cliente es obligatorio.")
        if not math.isfinite(float(limite)):
            raise ValueError("El límite de crédito no es un monto válido.")
        if limite < 0:
            raise ValueError("El límite de crédito no puede ser negativo.")
        if limite > self.LIMITE_MAXIMO:
            raise ValueError(
                f"El límite de crédito no puede superar "
                f"{formatear_dinero(self.LIMITE_MAXIMO)}.")
        self._codigo = codigo
        self._nombre = nombre.strip()
        self._telefono = telefono.strip()
        self._limite = round(float(limite), 2)
        self._activo = bool(activo)
        self._doc_tipo = int(doc_tipo) if int(doc_tipo) in (80, 86, 96, 99) else 99
        self._doc_nro = str(doc_nro or "").strip()
        self._cond_iva = int(cond_iva) if int(cond_iva) in (1, 4, 5, 6) else 5
        self._email = str(email or "").strip()

    @property
    def codigo(self) -> int | None:
        return self._codigo

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def telefono(self) -> str:
        return self._telefono

    @property
    def limite(self) -> float:
        return self._limite

    @property
    def activo(self) -> bool:
        return self._activo

    @property
    def doc_tipo(self) -> int:
        return self._doc_tipo

    @property
    def doc_nro(self) -> str:
        return self._doc_nro

    @property
    def cond_iva(self) -> int:
        return self._cond_iva

    @property
    def email(self) -> str:
        return self._email

    @property
    def identificador(self) -> str:
        return str(self._codigo or "")

    def asignar_codigo(self, codigo: int) -> None:
        if self._codigo is not None:
            raise ValueError("El cliente ya tiene un código asignado.")
        self._codigo = codigo

    def to_dict(self) -> dict[str, str]:
        return {
            "codigo": self.identificador,
            "nombre": self._nombre,
            "telefono": self._telefono,
            "limite": f"{self._limite:.2f}",
            "activo": "1" if self._activo else "0",
            "doc_tipo": str(self._doc_tipo),
            "doc_nro": self._doc_nro,
            "cond_iva": str(self._cond_iva),
            "email": self._email,
        }

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        cliente = cls.__new__(cls)
        cliente._cargar_fila(datos)
        return cliente

    def _cargar_fila(self, datos: dict[str, str]) -> None:
        codigo_texto = datos.get("codigo") or ""
        self._codigo = int(codigo_texto) if codigo_texto.isdigit() else None
        self._nombre = str(datos.get("nombre") or "").strip()
        if not self._nombre:
            raise ValueError("El nombre del cliente es obligatorio.")
        self._telefono = str(datos.get("telefono") or "").strip()
        self._limite = round(self._a_decimal(datos.get("limite")), 2)
        self._activo = (datos.get("activo") or "1") == "1"
        self._doc_tipo = self._a_entero(datos.get("doc_tipo"), 99)
        if self._doc_tipo not in (80, 86, 96, 99):
            self._doc_tipo = 99
        self._doc_nro = str(datos.get("doc_nro") or "").strip()
        self._cond_iva = self._a_entero(datos.get("cond_iva"), 5)
        if self._cond_iva not in (1, 4, 5, 6):
            self._cond_iva = 5
        self._email = str(datos.get("email") or "").strip()
        if self._limite > self.LIMITE_MAXIMO:
            warnings.warn(
                f"El límite de crédito de {self._nombre} supera el máximo "
                f"permitido ({self._limite} > {self.LIMITE_MAXIMO}).",
                RuntimeWarning,
                stacklevel=3,
            )

    def __str__(self) -> str:
        return self._nombre
