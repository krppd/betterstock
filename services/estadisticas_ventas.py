from __future__ import annotations

import logging
import sys
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, timedelta

from models.venta_registrada import VentaRegistrada
from repositories.sqlite import conectar, ruta_db
from repositories.venta_repositorio import VentaRepositorio

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResumenPeriodo:
    desde: date
    hasta: date
    cantidad_ventas: int = 0
    unidades: float = 0.0
    total: float = 0.0
    ticket_promedio: float = 0.0
    devoluciones_total: float = 0.0

    @property
    def vacio(self) -> bool:
        return self.cantidad_ventas == 0


@dataclass(frozen=True)
class ProductoVendido:
    codigo: str
    nombre: str
    unidades: float = 0.0
    total: float = 0.0


@dataclass(frozen=True)
class Comparacion:
    actual: ResumenPeriodo
    anterior: ResumenPeriodo
    variacion_total: float | None = None
    variacion_unidades: float | None = None
    variacion_ticket_promedio: float | None = None


def _variacion(actual: float, anterior: float) -> float | None:
    if anterior == 0:
        return None
    return (actual - anterior) / anterior * 100


@dataclass
class _Acumulador:
    cantidad: int = 0
    unidades: float = 0.0
    total: float = 0.0
    devoluciones_total: float = 0.0
    productos: dict[str, ProductoVendido] = field(default_factory=dict)

    def sumar(self, venta: VentaRegistrada) -> None:
        self.cantidad += 1
        self.unidades += venta.unidades
        self.total += venta.total
        for renglon in venta.detalle:
            actual = self.productos.get(renglon.codigo)
            if actual is None:
                self.productos[renglon.codigo] = ProductoVendido(
                    codigo=renglon.codigo,
                    nombre=renglon.nombre,
                    unidades=renglon.cantidad,
                    total=renglon.subtotal,
                )
            else:
                self.productos[renglon.codigo] = ProductoVendido(
                    codigo=actual.codigo,
                    nombre=actual.nombre,
                    unidades=actual.unidades + renglon.cantidad,
                    total=actual.total + renglon.subtotal,
                )

    def resumen(self, desde: date, hasta: date) -> ResumenPeriodo:
        promedio = self.total / self.cantidad if self.cantidad else 0.0
        return ResumenPeriodo(
            desde, hasta, self.cantidad, self.unidades, self.total, promedio,
            devoluciones_total=self.devoluciones_total,
        )


class EstadisticasVentas:
    def __init__(self, ventas: VentaRepositorio) -> None:
        self._ventas = ventas

    def inicializar(self) -> None:
        self._ventas.inicializar()

    @staticmethod
    def del_dia(dia: date) -> tuple[date, date]:
        return dia, dia

    @staticmethod
    def del_mes(anio: int, mes: int) -> tuple[date, date]:
        ultimo = monthrange(anio, mes)[1]
        return date(anio, mes, 1), date(anio, mes, ultimo)

    @staticmethod
    def del_periodo_anterior(desde: date, hasta: date) -> tuple[date, date]:
        dias = (hasta - desde).days + 1
        return desde - timedelta(days=dias), desde - timedelta(days=1)

    @staticmethod
    def ultimos_dias(dias: int, hoy: date | None = None) -> tuple[date, date]:
        fin = hoy or date.today()
        return fin - timedelta(days=dias - 1), fin

    def todo_el_historial(self, hoy: date | None = None) -> tuple[date, date]:
        fin = hoy or date.today()
        fechas = [venta.fecha for venta in self._ventas.listar() if not venta.anulada]
        if not fechas:
            return fin, fin
        return min(fechas), fin

    def _acumular(self, desde: date, hasta: date) -> _Acumulador:
        acumulado = _Acumulador()
        for venta in self._ventas.listar():
            if venta.anulada:
                continue
            if desde <= venta.fecha <= hasta:
                acumulado.sumar(venta)
        try:
            conexion = conectar(ruta_db(self._ventas.ruta_archivo))
            try:
                filas = conexion.execute(
                    """
                    SELECT d.id, d.fecha, d.total
                    FROM devoluciones d
                    WHERE d.anulada = 0 AND d.fecha >= ? AND d.fecha <= ?
                    """,
                    (desde.strftime("%Y-%m-%d"), hasta.strftime("%Y-%m-%d")),
                ).fetchall()
                for fila in filas:
                    d_id = fila["id"]
                    d_tot = float(fila["total"])
                    acumulado.total = max(0.0, round(acumulado.total - d_tot, 2))
                    acumulado.devoluciones_total += d_tot
                    item_filas = conexion.execute(
                        "SELECT codigo_producto, cantidad, subtotal FROM devolucion_items WHERE devolucion_id = ?",
                        (d_id,),
                    ).fetchall()
                    for ifila in item_filas:
                        c_prod = str(ifila["codigo_producto"])
                        c_cant = float(ifila["cantidad"])
                        c_sub = float(ifila["subtotal"])
                        acumulado.unidades = max(0.0, round(acumulado.unidades - c_cant, 4))
                        prod_actual = acumulado.productos.get(c_prod)
                        if prod_actual is not None:
                            acumulado.productos[c_prod] = ProductoVendido(
                                codigo=prod_actual.codigo,
                                nombre=prod_actual.nombre,
                                unidades=max(0.0, round(prod_actual.unidades - c_cant, 4)),
                                total=max(0.0, round(prod_actual.total - c_sub, 2)),
                            )
            finally:
                conexion.close()
        except Exception:
            logger.warning(
                "No se pudieron leer las devoluciones para la estadística: %s",
                sys.exc_info()[1],
            )
        return acumulado

    def resumen(self, desde: date, hasta: date) -> ResumenPeriodo:
        return self._acumular(desde, hasta).resumen(desde, hasta)

    def comparar(self, desde: date, hasta: date) -> Comparacion:
        raise PermissionError(
            "La comparación con el período anterior es una función de BetterStock Pro."
        )

    def mas_vendidos(self, desde: date, hasta: date, limite: int = 10) -> list[ProductoVendido]:
        productos = list(self._acumular(desde, hasta).productos.values())
        return sorted(productos, key=lambda p: p.unidades, reverse=True)[:limite]

    def ventas_del_dia(self, dia: date) -> list[VentaRegistrada]:
        return self._ventas.del_dia(dia)

    def todas_las_ventas(self) -> list[VentaRegistrada]:
        return sorted(self._ventas.listar(), key=lambda v: (v.fecha, v.hora), reverse=True)

    def ventas_del_periodo(self, desde: date, hasta: date) -> list[VentaRegistrada]:
        ventas = [v for v in self._ventas.listar() if desde <= v.fecha <= hasta]
        return sorted(ventas, key=lambda v: (v.fecha, v.hora), reverse=True)

    def total_por_dia(self, desde: date, hasta: date) -> list[tuple[date, float]]:
        por_dia: dict[date, float] = {desde + timedelta(days=i): 0.0 for i in range((hasta - desde).days + 1)}
        for venta in self._ventas.listar():
            if not venta.anulada and desde <= venta.fecha <= hasta:
                por_dia[venta.fecha] = por_dia.get(venta.fecha, 0.0) + venta.total
        try:
            conexion = conectar(ruta_db(self._ventas.ruta_archivo))
            try:
                filas = conexion.execute(
                    """
                    SELECT fecha, SUM(total) as tot
                    FROM devoluciones
                    WHERE anulada = 0 AND fecha >= ? AND fecha <= ?
                    GROUP BY fecha
                    """,
                    (desde.strftime("%Y-%m-%d"), hasta.strftime("%Y-%m-%d")),
                ).fetchall()
                for f in filas:
                    try:
                        f_fecha = date.fromisoformat(f["fecha"])
                        if f_fecha in por_dia:
                            por_dia[f_fecha] = max(0.0, round(por_dia[f_fecha] - float(f["tot"]), 2))
                    except ValueError:
                        continue
            finally:
                conexion.close()
        except Exception:
            logger.warning(
                "No se pudieron leer las devoluciones para la estadística: %s",
                sys.exc_info()[1],
            )
        return sorted(por_dia.items())

    def total_por_mes(self, desde: date, hasta: date) -> list[tuple[date, float]]:
        raise PermissionError(
            "Las estadísticas por mes son una función de BetterStock Pro."
        )

    def registrar(self, venta: VentaRegistrada) -> None:
        self._ventas.agregar(venta)

    def errores_lectura(self) -> list[dict[str, str]]:
        return self._ventas.errores_lectura

    def buscar(self, identificador: str) -> VentaRegistrada | None:
        return self._ventas.buscar(identificador)

    def actualizar(self, venta: VentaRegistrada) -> None:
        self._ventas.actualizar(venta)