
from __future__ import annotations

import logging
import sys
import warnings
from datetime import date
from pathlib import Path

from models.cierre import Cierre, CierreRegistrado, ResumenMedios
from models.medio_pago import MEDIOS, es_efectivo
from models.venta_registrada import leer_pagos
from repositories.cierre_repositorio import CierreRepositorio
from repositories.sqlite import conectar, ruta_db
from services.backup import ServicioBackup
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_fiado import GestorFiado
from utils.formato import diferencia as diferencia_montos

logger = logging.getLogger(__name__)


class ErrorCierre(ValueError):
    pass


class ServicioCierre:

    CANTIDAD_BACKUPS = 15

    def __init__(self, estadisticas: EstadisticasVentas, cierres: CierreRepositorio,
                 fiado: GestorFiado | None = None, backup: ServicioBackup | None = None,
                 caja=None) -> None:
        self._estadisticas = estadisticas
        self._cierres = cierres
        self._fiado = fiado
        self._backup = backup if backup is not None else ServicioBackup()
        self._caja = caja
        self.ultimo_backup: Path | None = None

    @property
    def caja(self):
        return self._caja

    @caja.setter
    def caja(self, valor):
        self._caja = valor

    def inicializar(self) -> None:
        self._cierres.inicializar()

    def ya_cerrado(self, dia: date) -> bool:
        return self._cierres.ya_cerrado(dia)

    def arqueo(self, dia: date) -> Cierre:
        ventas = [v for v in self._estadisticas.ventas_del_dia(dia) if not v.anulada]
        medios = ResumenMedios()
        for venta in ventas:
            medios.sumar(venta)
        ventas_efectivo = medios.efectivo

        cobros_fiado_efectivo = 0.0
        if self._fiado is not None:
            validos = {codigo for _, codigo in MEDIOS}
            for pago in self._fiado.pagos_del_dia(dia):
                if pago.medio in validos:
                    medios.sumar_ingreso(pago.medio, pago.importe)
                    if pago.medio == "efectivo":
                        cobros_fiado_efectivo += pago.importe

        egresos = 0.0
        ingresos = 0.0
        if self._caja is not None:
            movimientos = [m for m in self._caja.listar_del_dia(dia) if not m.anulado]
            for m in movimientos:
                if m.es_egreso:
                    egresos += m.importe
                elif m.es_ingreso:
                    ingresos += m.importe

            if egresos > 0:
                medios.restar_egreso("efectivo", egresos)
            if ingresos > 0:
                medios.sumar_ingreso("efectivo", ingresos)

        devoluciones_total = 0.0
        devoluciones_efectivo = 0.0
        try:
            conexion = conectar(ruta_db(self._cierres.ruta_archivo))
            try:
                filas = conexion.execute(
                    """
                    SELECT d.id, d.total, v.medio_pago, v.pagos
                    FROM devoluciones d
                    JOIN ventas v ON v.id = d.venta_id
                    WHERE d.anulada = 0 AND d.fecha = ?
                    """,
                    (dia.strftime("%Y-%m-%d"),),
                ).fetchall()
                for fila in filas:
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
            finally:
                conexion.close()
        except Exception:
            logger.warning(
                "No se pudieron leer las devoluciones para el arqueo: %s",
                sys.exc_info()[1],
            )

        if devoluciones_efectivo > 0:
            medios.restar_egreso("efectivo", devoluciones_efectivo)

        efectivo = medios.efectivo
        return Cierre(
            fecha=dia,
            esperado_por_medio=medios,
            efectivo_declarado=efectivo,
            cantidad_ventas=len(ventas),
            ventas_efectivo=ventas_efectivo,
            cobros_fiado_efectivo=cobros_fiado_efectivo,
            egresos=egresos,
            ingresos=ingresos,
            devoluciones_total=devoluciones_total,
        )

    def cerrar(self, dia: date, efectivo_declarado: float, notas: str = "",
               usuario: str = "") -> CierreRegistrado:
        if self._cierres.ya_cerrado(dia):
            raise ErrorCierre("Ese día ya tiene un cierre guardado.")

        base = self.arqueo(dia)
        diferencia = float(diferencia_montos(efectivo_declarado, base.esperado_por_medio.efectivo))
        cierre = Cierre(
            fecha=dia,
            esperado_por_medio=base.esperado_por_medio,
            efectivo_declarado=efectivo_declarado,
            sobrante=max(diferencia, 0.0),
            faltante=max(-diferencia, 0.0),
            diferencia=diferencia,
            notas=notas.strip(),
            cantidad_ventas=base.cantidad_ventas,
        )
        registro = CierreRegistrado.desde_cierre(cierre, usuario)
        self._cierres.agregar(registro)
        self.ultimo_backup = self._guardar_backup()
        return registro

    def _guardar_backup(self) -> Path | None:
        try:
            archivo = self._backup.generar()
            self._backup.rotar(self.CANTIDAD_BACKUPS)
            return archivo
        except Exception as error:
            mensaje = f"No se pudo guardar la copia de seguridad del cierre: {error}"
            warnings.warn(mensaje, RuntimeWarning)
            print(mensaje, file=sys.stderr)
            return None

    def historial(self) -> list[CierreRegistrado]:
        return self._cierres.listar()

    def total_backups(self) -> int:
        try:
            return self._backup.total()
        except OSError:
            return 0