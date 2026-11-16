from __future__ import annotations

import logging
import sys
from datetime import date, datetime

from models.cierre import ResumenMedios
from models.medio_pago import MEDIOS, es_efectivo
from models.movimiento_cuenta import MovimientoCuenta
from models.turno import ArqueoTurno, Turno
from models.usuario import Usuario
from models.venta_registrada import leer_pagos
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.sqlite import conectar, ruta_db
from repositories.turno_repositorio import TurnoRepositorio
from repositories.venta_repositorio import VentaRepositorio
from utils.formato import diferencia as diferencia_montos

logger = logging.getLogger(__name__)


class ErrorTurno(ValueError):
    pass


class ServicioTurnos:
    def __init__(self, turnos: TurnoRepositorio, ventas: VentaRepositorio,
                 cuenta: CuentaRepositorio, caja=None) -> None:
        self._turnos = turnos
        self._ventas = ventas
        self._cuenta = cuenta
        self._caja = caja

    @property
    def caja(self):
        return self._caja

    @caja.setter
    def caja(self, valor):
        self._caja = valor

    def inicializar(self) -> None:
        self._turnos.inicializar()

    def abierto(self) -> Turno | None:
        return self._turnos.abierto()

    def abrir(self, fondo_inicial: float, usuario: str,
             notas: str = "") -> Turno:
        turno_abierto = self.abierto()
        if turno_abierto is not None:
            raise ErrorTurno(
                "Ya hay un turno abierto por "
                f"{turno_abierto.usuario_apertura or 'otro usuario'}.")
        if fondo_inicial < 0:
            raise ErrorTurno("El fondo inicial no puede ser negativo.")
        momento = datetime.now()
        turno = Turno(
            momento.date(), momento.strftime("%H:%M:%S"), usuario,
            fondo_inicial, notas=notas)
        self._turnos.agregar(turno)
        return turno

    def arqueo(self, turno: Turno | None = None) -> ArqueoTurno:
        turno = turno if turno is not None else self.abierto()
        if turno is None:
            raise ErrorTurno("No hay un turno abierto.")
        inicio = (turno.fecha_apertura, turno.hora_apertura)
        if turno.cerrado and turno.fecha_cierre is not None:
            fin = (turno.fecha_cierre, turno.hora_cierre)
            incluir_fin = False
        else:
            ahora = datetime.now()
            fin = (ahora.date(), ahora.strftime("%H:%M:%S"))
            incluir_fin = True

        def dentro(fecha: date, hora: str) -> bool:
            if not hora:
                return False
            punto = (fecha, hora)
            return punto >= inicio and (punto <= fin if incluir_fin
                                        else punto < fin)

        medios = ResumenMedios()
        ventas = [
            venta for venta in self._ventas.listar()
            if not venta.anulada and dentro(venta.fecha, venta.hora)
        ]
        for venta in ventas:
            medios.sumar(venta)
        ventas_efectivo = medios.efectivo

        validos = {codigo for _, codigo in MEDIOS}
        cobros_fiado = 0.0
        for movimiento in self._cuenta.listar():
            if (movimiento.tipo == MovimientoCuenta.TIPO_PAGO
                    and movimiento.medio in validos
                    and dentro(movimiento.fecha, movimiento.hora)):
                medios.sumar_ingreso(movimiento.medio, movimiento.importe)
                if movimiento.medio == "efectivo":
                    cobros_fiado += movimiento.importe

        egresos = 0.0
        ingresos = 0.0
        if self._caja is not None:
            movimientos = [
                m for m in self._caja.listar()
                if not m.anulado and dentro(m.fecha, m.hora)
            ]
            for m in movimientos:
                if m.es_egreso:
                    egresos += m.importe
                elif m.es_ingreso:
                    cat_l = (m.categoria or "").casefold()
                    conc_l = (m.concepto or "").casefold()
                    if turno.fondo_inicial > 0 and (cat_l == "apertura" or "fondo" in conc_l):
                        continue
                    ingresos += m.importe

            if egresos > 0:
                medios.restar_egreso("efectivo", egresos)
            if ingresos > 0:
                medios.sumar_ingreso("efectivo", ingresos)

        devoluciones_total = 0.0
        devoluciones_efectivo = 0.0
        try:
            conexion = conectar(ruta_db(self._turnos.ruta_archivo))
            try:
                filas = conexion.execute(
                    """
                    SELECT d.id, d.fecha, d.hora, d.total, v.medio_pago, v.pagos
                    FROM devoluciones d
                    JOIN ventas v ON v.id = d.venta_id
                    WHERE d.anulada = 0
                    """
                ).fetchall()
                for fila in filas:
                    try:
                        f_dev = date.fromisoformat(fila["fecha"])
                        h_dev = fila["hora"]
                        if dentro(f_dev, h_dev):
                            tot = float(fila["total"])
                            devoluciones_total += tot
                            medio = fila["medio_pago"] or ""
                            pagos = fila["pagos"] or ""
                            if es_efectivo(medio):
                                devoluciones_efectivo += tot
                            elif medio == "mixto":
                                pagado_cash = sum(
                                    p.importe for p in leer_pagos(pagos) if es_efectivo(p.medio)
                                )
                                devoluciones_efectivo += min(tot, pagado_cash)
                    except Exception:
                        continue
            finally:
                conexion.close()
        except Exception:
            logger.warning(
                "No se pudieron leer las devoluciones para el arqueo de turno: %s",
                sys.exc_info()[1],
            )

        if devoluciones_efectivo > 0:
            medios.restar_egreso("efectivo", devoluciones_efectivo)

        return ArqueoTurno(
            turno, medios, len(ventas),
            ventas_efectivo_brutas=ventas_efectivo,
            cobros_fiado=cobros_fiado,
            egresos=egresos,
            ingresos=ingresos,
            devoluciones_total=devoluciones_total,
        )

    def cerrar(self, declarado: float, usuario: str, permiso: str,
               notas: str = "") -> Turno:
        turno = self.abierto()
        if turno is None:
            raise ErrorTurno("No hay un turno abierto.")
        if (turno.usuario_apertura
                and not Usuario.es_admin(permiso)
                and turno.usuario_apertura.casefold() != usuario.strip().casefold()):
            raise ErrorTurno(
                "Solo quien abrió el turno o un administrador puede cerrarlo.")
        arqueo = self.arqueo(turno)
        diferencia = float(diferencia_montos(
            declarado, arqueo.efectivo_esperado))
        turno.cerrar(datetime.now(), usuario, arqueo, declarado, diferencia, notas)
        self._turnos.actualizar(turno)
        return turno

    def historial(self, limite: int | None = 30) -> list[Turno]:
        return self._turnos.historial(limite)

    def sugerir_fondo(self) -> float:
        cerrados = [turno for turno in self._turnos.listar() if turno.cerrado]
        return cerrados[-1].declarado if cerrados else 0.0
