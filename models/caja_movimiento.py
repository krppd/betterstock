from __future__ import annotations

from datetime import date, datetime
from typing import Self

from models.entidad import Entidad


class CajaMovimiento(Entidad):
    COLUMNAS: tuple[str, ...] = (
        "id", "fecha", "hora", "tipo", "concepto", "categoria",
        "importe", "usuario", "anulado", "anulado_por", "motivo_anulacion",
    )
    FORMATO_FECHA = "%d/%m/%Y"
    TIPO_EGRESO = "egreso"
    TIPO_INGRESO = "ingreso"
    TIPOS = (TIPO_EGRESO, TIPO_INGRESO)

    def __init__(
        self,
        fecha: date,
        hora: str,
        tipo: str,
        concepto: str,
        importe: float,
        categoria: str = "",
        usuario: str = "",
        anulado: bool = False,
        anulado_por: str = "",
        motivo_anulacion: str = "",
        id_movimiento: int | None = None,
    ) -> None:
        if tipo not in self.TIPOS:
            raise ValueError(f"Tipo de movimiento inválido: {tipo!r}")
        if not str(concepto).strip():
            raise ValueError("El concepto es obligatorio.")
        if importe <= 0:
            raise ValueError("El importe debe ser mayor a cero.")

        self._id_movimiento = id_movimiento
        self._fecha = fecha
        self._hora = (hora or datetime.now().strftime("%H:%M:%S")).strip()
        self._tipo = tipo
        self._concepto = str(concepto).strip()
        self._categoria = str(categoria).strip()
        self._importe = round(float(importe), 2)
        self._usuario = str(usuario).strip()
        self._anulado = bool(anulado)
        self._anulado_por = str(anulado_por).strip()
        self._motivo_anulacion = str(motivo_anulacion).strip()

    @property
    def id_movimiento(self) -> int | None:
        return self._id_movimiento

    @property
    def identificador(self) -> str:
        return str(self._id_movimiento or "")

    @property
    def fecha(self) -> date:
        return self._fecha

    @property
    def fecha_texto(self) -> str:
        return self._fecha.strftime(self.FORMATO_FECHA)

    @property
    def hora(self) -> str:
        return self._hora

    @property
    def tipo(self) -> str:
        return self._tipo

    @property
    def concepto(self) -> str:
        return self._concepto

    @property
    def categoria(self) -> str:
        return self._categoria

    @property
    def importe(self) -> float:
        return self._importe

    @property
    def usuario(self) -> str:
        return self._usuario

    @property
    def anulado(self) -> bool:
        return self._anulado

    @property
    def anulado_por(self) -> str:
        return self._anulado_por

    @property
    def motivo_anulacion(self) -> str:
        return self._motivo_anulacion

    @property
    def es_egreso(self) -> bool:
        return self._tipo == self.TIPO_EGRESO

    @property
    def es_ingreso(self) -> bool:
        return self._tipo == self.TIPO_INGRESO

    def asignar_id(self, id_movimiento: int) -> None:
        if self._id_movimiento is not None:
            raise ValueError("El movimiento ya tiene un número asignado.")
        self._id_movimiento = id_movimiento

    def anular(self, anulado_por: str, motivo: str) -> None:
        self._anulado = True
        self._anulado_por = str(anulado_por).strip()
        self._motivo_anulacion = str(motivo).strip()

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.identificador,
            "fecha": self.fecha_texto,
            "hora": self._hora,
            "tipo": self._tipo,
            "concepto": self._concepto,
            "categoria": self._categoria,
            "importe": f"{self._importe:.2f}",
            "usuario": self._usuario,
            "anulado": "1" if self._anulado else "0",
            "anulado_por": self._anulado_por,
            "motivo_anulacion": self._motivo_anulacion,
        }

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        id_texto = datos.get("id") or ""
        anulado_raw = datos.get("anulado") or "0"
        anulado = anulado_raw in ("1", "True", "true")
        return cls(
            datetime.strptime(datos.get("fecha") or "", cls.FORMATO_FECHA).date(),
            datos.get("hora") or "",
            datos.get("tipo") or "",
            datos.get("concepto") or "",
            cls._a_decimal(datos.get("importe")),
            categoria=datos.get("categoria") or "",
            usuario=datos.get("usuario") or "",
            anulado=anulado,
            anulado_por=datos.get("anulado_por") or "",
            motivo_anulacion=datos.get("motivo_anulacion") or "",
            id_movimiento=int(id_texto) if id_texto.isdigit() else None,
        )
