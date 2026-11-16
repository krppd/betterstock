from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from models.caja_movimiento import CajaMovimiento
from repositories.caja_movimiento_repositorio import CajaMovimientoRepositorio
from services.excepciones import ErrorValidacion

if TYPE_CHECKING:
    from models.turno import Turno


class ErrorCaja(ErrorValidacion):
    pass


class ServicioCaja:
    def __init__(
        self,
        repositorio: CajaMovimientoRepositorio,
        cierres=None,
        turnos=None,
        codigos=None,
        gestor_anulaciones=None,
    ) -> None:
        self._repositorio = repositorio
        self._cierres = cierres
        self._turnos = turnos
        self._codigos = codigos
        self._gestor_anulaciones = gestor_anulaciones

    def inicializar(self) -> None:
        self._repositorio.inicializar()

    def listar(self) -> list[CajaMovimiento]:
        return self._repositorio.listar()

    def listar_del_dia(self, dia: date | None = None) -> list[CajaMovimiento]:
        dia_consulta = dia if dia is not None else date.today()
        return self._repositorio.listar_del_dia(dia_consulta)

    def listar_del_turno(self, turno: Turno | None = None) -> list[CajaMovimiento]:
        if turno is None and self._turnos is not None:
            turno = self._turnos.abierto()
        if turno is None:
            return []

        inicio = (turno.fecha_apertura, turno.hora_apertura)
        if turno.cerrado and turno.fecha_cierre is not None:
            fin = (turno.fecha_cierre, turno.hora_cierre)
            incluir_fin = False
        else:
            ahora = datetime.now()
            fin = (ahora.date(), ahora.strftime("%H:%M:%S"))
            incluir_fin = True
            if fin < inicio or ahora.date() <= turno.fecha_apertura:
                fin = (turno.fecha_apertura, "23:59:59")

        def dentro(fecha: date, hora: str) -> bool:
            if not hora:
                return False
            punto = (fecha, hora)
            return punto >= inicio and (punto <= fin if incluir_fin else punto < fin)

        return [m for m in self._repositorio.listar() if dentro(m.fecha, m.hora)]

    def registrar(
        self,
        tipo: str,
        concepto: str,
        importe: float,
        categoria: str = "",
        usuario: str = "",
        fecha: date | None = None,
        hora: str | None = None,
        turno: Turno | None = None,
    ) -> CajaMovimiento:
        dia_registro = fecha if fecha is not None else date.today()
        hora_registro = hora if hora is not None else datetime.now().strftime("%H:%M:%S")

        if self._cierres is not None and self._cierres.ya_cerrado(dia_registro):
            raise ErrorCaja("No se pueden registrar movimientos: el día está cerrado.")

        if turno is not None and turno.cerrado:
            raise ErrorCaja("No se pueden registrar movimientos: el turno está cerrado.")

        movimiento = CajaMovimiento(
            fecha=dia_registro,
            hora=hora_registro,
            tipo=tipo,
            concepto=concepto,
            importe=importe,
            categoria=categoria,
            usuario=usuario,
        )
        return self._repositorio.agregar(movimiento)

    def anular(
        self,
        id_movimiento: int,
        codigo: str,
        motivo: str,
        anulado_por: str = "",
        turno: Turno | None = None,
    ) -> CajaMovimiento:
        movimiento = self._repositorio.obtener(id_movimiento)
        if movimiento is None:
            raise ErrorCaja("Movimiento de caja no encontrado.")
        if movimiento.anulado:
            raise ErrorCaja("El movimiento ya está anulado.")

        if self._cierres is not None and self._cierres.ya_cerrado(movimiento.fecha):
            raise ErrorCaja("No se puede anular: el día está cerrado.")

        if turno is not None and turno.cerrado:
            raise ErrorCaja("No se puede anular: el turno está cerrado.")

        if self._turnos is not None:
            punto = (movimiento.fecha, movimiento.hora)
            for t in self._turnos.historial(limite=None):
                if t.cerrado and t.fecha_cierre is not None:
                    inicio = (t.fecha_apertura, t.hora_apertura)
                    fin = (t.fecha_cierre, t.hora_cierre)
                    if inicio <= punto < fin:
                        raise ErrorCaja("No se puede anular: el turno está cerrado.")

        motivo_limpio = (motivo or "").strip()
        if not motivo_limpio:
            raise ErrorCaja("Escribí el motivo de la anulación.")

        supervisor = anulado_por.strip()
        if self._codigos is not None:
            encontrado = self._codigos.buscar_activo_por_codigo((codigo or "").strip())
            if encontrado is None:
                raise ErrorCaja("El código no es válido.")
            supervisor = encontrado.etiqueta or supervisor
        elif self._gestor_anulaciones is not None:
            if not self._gestor_anulaciones.codigo_valido(codigo):
                raise ErrorCaja("El código no es válido.")
        else:
            if not (codigo or "").strip():
                raise ErrorCaja("El código no es válido.")

        movimiento.anular(supervisor or "supervisor", motivo_limpio)
        self._repositorio.actualizar(movimiento)
        return movimiento

    def eliminar(self, id_movimiento: int) -> None:
        raise ErrorCaja("No se pueden borrar movimientos de caja.")
