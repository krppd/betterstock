from __future__ import annotations

from datetime import date, datetime
from typing import Self

from models.entidad import Entidad


class MovimientoCuenta(Entidad):
    COLUMNAS: tuple[str, ...] = ("id", "fecha", "cliente", "tipo", "importe", "detalle", "medio", "usuario", "hora")
    FORMATO_FECHA = "%d/%m/%Y"
    TIPO_CARGO = "cargo"
    TIPO_PAGO = "pago"

    def __init__(self, fecha: date, cliente: str, tipo: str, importe: float,
                 detalle: str = "", medio: str = "", usuario: str = "",
                 hora: str | None = None, id_movimiento: int | None = None) -> None:
        if tipo not in (self.TIPO_CARGO, self.TIPO_PAGO):
            raise ValueError(f"Tipo de movimiento de cuenta inválido: {tipo!r}")
        if not str(cliente).strip():
            raise ValueError("El movimiento de cuenta necesita un cliente.")
        if importe <= 0:
            raise ValueError("El importe del movimiento debe ser mayor a cero.")
        self._id_movimiento = id_movimiento
        self._fecha = fecha
        self._cliente = str(cliente).strip()
        self._tipo = tipo
        self._importe = round(float(importe), 2)
        self._detalle = detalle.strip()
        self._medio = medio.strip()
        self._usuario = usuario.strip()
        self._hora = (hora if hora is not None
                      else datetime.now().strftime("%H:%M:%S"))

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
    def cliente(self) -> str:
        return self._cliente

    @property
    def tipo(self) -> str:
        return self._tipo

    @property
    def importe(self) -> float:
        return self._importe

    @property
    def detalle(self) -> str:
        return self._detalle

    @property
    def medio(self) -> str:
        return self._medio

    @property
    def usuario(self) -> str:
        return self._usuario

    @property
    def hora(self) -> str:
        return self._hora

    @property
    def signo(self) -> int:
        return 1 if self._tipo == self.TIPO_CARGO else -1

    def asignar_id(self, id_movimiento: int) -> None:
        if self._id_movimiento is not None:
            raise ValueError("El movimiento ya tiene un número asignado.")
        self._id_movimiento = id_movimiento

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.identificador,
            "fecha": self.fecha_texto,
            "cliente": self._cliente,
            "tipo": self._tipo,
            "importe": f"{self._importe:.2f}",
            "detalle": self._detalle,
            "medio": self._medio,
            "usuario": self._usuario,
            "hora": self._hora,
        }

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        id_texto = datos.get("id") or ""
        return cls(
            datetime.strptime(datos.get("fecha") or "", cls.FORMATO_FECHA).date(),
            datos.get("cliente") or "",
            datos.get("tipo") or "",
            cls._a_decimal(datos.get("importe")),
            detalle=datos.get("detalle") or "",
            medio=datos.get("medio") or "",
            usuario=datos.get("usuario") or "",
            hora=datos.get("hora") or "",
            id_movimiento=int(id_texto) if id_texto.isdigit() else None,
        )
