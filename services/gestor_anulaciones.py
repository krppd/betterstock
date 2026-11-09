from __future__ import annotations

from collections.abc import Callable
from datetime import date
import logging

from models.codigo_anulacion import CodigoAnulacion
from repositories.codigo_repositorio import CodigoRepositorio
from services.excepciones import ErrorValidacion
from services.gestor_ventas import GestorVentas

MENSAJE_CODIGO_INVALIDO = "El código no es válido."
MENSAJE_SIN_MOTIVO = "Escribí el motivo de la anulación."
MENSAJE_SIN_SERVICIO = "El servicio de anulación no está disponible."

logger = logging.getLogger(__name__)

_SERVICIO: GestorAnulaciones | None = None


class GestorAnulaciones:
    def __init__(
        self,
        gestor_ventas: GestorVentas,
        codigos: CodigoRepositorio,
        al_anular: Callable[[str], None] | None = None,
    ) -> None:
        self._gestor_ventas = gestor_ventas
        self._codigos = codigos
        self._al_anular = al_anular
        self._ultimos_faltantes: list[str] = []

    @property
    def ultimos_faltantes(self) -> list[str]:
        return list(self._ultimos_faltantes)

    def inicializar(self) -> None:
        self._codigos.inicializar()

    def generar_codigo(self, etiqueta: str = "") -> tuple[CodigoAnulacion, str]:
        return self._codigos.generar(etiqueta)

    def listar_codigos(self) -> list[CodigoAnulacion]:
        return self._codigos.listar()

    def codigo_valido(self, codigo: str) -> bool:
        return self._codigos.buscar_activo_por_codigo((codigo or "").strip()) is not None

    def revocar_codigo(self, identificador: int) -> bool:
        return self._codigos.revocar(identificador)

    def anular_con_codigo(self, identificador: str, fecha: date, codigo: str,
                          motivo: str) -> str:
        encontrado = self._codigos.buscar_activo_por_codigo((codigo or "").strip())
        if encontrado is None:
            raise ErrorValidacion(MENSAJE_CODIGO_INVALIDO)
        limpio = (motivo or "").strip()
        if not limpio:
            raise ErrorValidacion(MENSAJE_SIN_MOTIVO)
        self._ultimos_faltantes = self._gestor_ventas.anular(identificador, fecha, limpio)
        if self._al_anular is not None:
            try:
                self._al_anular(identificador)
            except Exception:
                logger.exception(
                    "Falló el aviso de anulación para la venta %s", identificador
                )
        return encontrado.etiqueta

    def motivo_bloqueo(self, venta) -> str:
        return self._gestor_ventas.motivo_bloqueo_anulacion(venta)


def registrar_servicio(servicio: GestorAnulaciones | None) -> None:
    global _SERVICIO
    _SERVICIO = servicio


def servicio_actual() -> GestorAnulaciones | None:
    return _SERVICIO
