from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Protocol

from services.excepciones import ErrorValidacion

LIMITE_HORAS = 24
MENSAJE_DIA_CERRADO = "Esta venta ya no se puede anular: el día está cerrado."
MENSAJE_PLAZO = "Esta venta ya no se puede anular: pasaron más de 24 horas."


class ConsultaCierres(Protocol):
    def ya_cerrado(self, dia) -> bool: ...


def _momento_de(venta) -> datetime:
    hora = str(venta.hora or "")
    try:
        momento_hora = datetime.strptime(hora, "%H:%M:%S").time()
    except ValueError:
        momento_hora = time(0, 0)
    return datetime.combine(venta.fecha, momento_hora)


class PlazoAnulacion:
    def __init__(self, cierres: ConsultaCierres | None = None) -> None:
        self._cierres = cierres

    def dia_cerrado(self, dia) -> bool:
        if self._cierres is None:
            return False
        return bool(self._cierres.ya_cerrado(dia))

    def fuera_de_plazo(self, venta) -> bool:
        ahora = datetime.now()
        momento = _momento_de(venta)
        if momento.date() != ahora.date():
            return momento < ahora
        return ahora - momento > timedelta(hours=LIMITE_HORAS)

    def motivo_bloqueo(self, venta) -> str:
        if self.dia_cerrado(venta.fecha):
            return MENSAJE_DIA_CERRADO
        if self.fuera_de_plazo(venta):
            return MENSAJE_PLAZO
        return ""

    def verificar(self, venta) -> None:
        motivo = self.motivo_bloqueo(venta)
        if motivo:
            raise ErrorValidacion(motivo)
