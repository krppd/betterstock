from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from models.entidad import Entidad
from models.medio_pago import MEDIOS, nombre_de
from models.venta_registrada import VentaRegistrada
from utils.formato import a_decimal

FORMATO_FECHA = "%d/%m/%Y"


@dataclass
class ResumenMedios:

    importes: dict[str, Decimal] = field(default_factory=dict)

    def sumar(self, venta: VentaRegistrada) -> None:
        pagos = venta.pagos
        if pagos:
            for pago in pagos:
                self.sumar_ingreso(pago.medio or "sin_registrar", pago.importe)
            return
        medio = venta.medio_pago or "sin_registrar"
        self.sumar_ingreso(medio, venta.total)

    def sumar_ingreso(self, medio: str, importe: float) -> None:
        actual = a_decimal(self.importes.get(medio))
        self.importes[medio] = actual + a_decimal(importe)

    def restar_egreso(self, medio: str, importe: float) -> None:
        actual = a_decimal(self.importes.get(medio))
        self.importes[medio] = actual - a_decimal(importe)

    def total(self) -> float:
        return float(self.total_exacto())

    def total_exacto(self) -> Decimal:
        return sum((a_decimal(importe) for importe in self.importes.values()),
                   a_decimal(0))

    def de(self, medio: str) -> float:
        return float(self.de_exacto(medio))

    def de_exacto(self, medio: str) -> Decimal:
        return a_decimal(self.importes.get(medio))

    @property
    def efectivo(self) -> float:
        return self.de("efectivo")

    def filas(self) -> list[tuple[str, str, float]]:
        filas = [
            (nombre_de(codigo), codigo, self.de(codigo))
            for _, codigo in MEDIOS
            if self.de(codigo) > 0
        ]
        otros = {
            codigo: importe
            for codigo, importe in self.importes.items()
            if a_decimal(importe) > 0 and codigo not in {c for _, c in MEDIOS}
        }
        filas.extend((nombre_de(codigo), codigo, float(a_decimal(importe)))
                     for codigo, importe in sorted(otros.items()))
        return filas


@dataclass(frozen=True)
class Cierre:

    fecha: date
    esperado_por_medio: ResumenMedios
    efectivo_declarado: float
    sobrante: float = 0.0
    faltante: float = 0.0
    diferencia: float = 0.0
    notas: str = ""
    cantidad_ventas: int = 0
    hora: str = ""
    ventas_efectivo: float = 0.0
    cobros_fiado_efectivo: float = 0.0
    egresos: float = 0.0
    ingresos: float = 0.0
    devoluciones_total: float = 0.0

    @property
    def efectivo_esperado(self) -> float:
        return self.esperado_por_medio.efectivo

    @property
    def esperado(self) -> float:
        return self.esperado_por_medio.total()

    @property
    def cuadra(self) -> bool:
        return abs(self.diferencia) < 0.01


class CierreRegistrado(Entidad):

    COLUMNAS = ("fecha", "hora", "cantidad_ventas", "total_esperado", "efectivo_esperado",
                "declarado", "diferencia", "sobrante", "faltante", "notas", "medios",
                "usuario")

    def __init__(self, fecha: date, hora: str, cantidad_ventas: int, total_esperado: float,
                 efectivo_esperado: float, declarado: float, diferencia: float,
                 sobrante: float, faltante: float, notas: str = "", medios: str = "",
                 usuario: str = "") -> None:
        self._fecha = fecha
        self._hora = hora
        self._cantidad_ventas = cantidad_ventas
        self._total_esperado = total_esperado
        self._efectivo_esperado = efectivo_esperado
        self._declarado = declarado
        self._diferencia = diferencia
        self._sobrante = sobrante
        self._faltante = faltante
        self._notas = notas
        self._medios = medios
        self._usuario = usuario.strip()

    @property
    def fecha(self) -> date:
        return self._fecha

    @property
    def hora(self) -> str:
        return self._hora

    @property
    def cantidad_ventas(self) -> int:
        return self._cantidad_ventas

    @property
    def total_esperado(self) -> float:
        return self._total_esperado

    @property
    def efectivo_esperado(self) -> float:
        return self._efectivo_esperado

    @property
    def declarado(self) -> float:
        return self._declarado

    @property
    def diferencia(self) -> float:
        return self._diferencia

    @property
    def sobrante(self) -> float:
        return self._sobrante

    @property
    def faltante(self) -> float:
        return self._faltante

    @property
    def notas(self) -> str:
        return self._notas

    @property
    def usuario(self) -> str:
        return self._usuario

    @property
    def cuadra(self) -> bool:
        return abs(self._diferencia) < 0.01

    @classmethod
    def desde_cierre(cls, cierre: Cierre, usuario: str = "") -> CierreRegistrado:
        medios = ";".join(
            f"{codigo}:{importe:.2f}"
            for _, codigo, importe in cierre.esperado_por_medio.filas()
        )
        return cls(cierre.fecha, cierre.hora or datetime.now().strftime("%H:%M:%S"),
                   cierre.cantidad_ventas, cierre.esperado, cierre.esperado_por_medio.efectivo,
                   cierre.efectivo_declarado, cierre.diferencia,
                   cierre.sobrante, cierre.faltante, cierre.notas, medios, usuario)

    @property
    def identificador(self) -> str:
        return f"{self._fecha.isoformat()} {self._hora}"

    @property
    def fecha_texto(self) -> str:
        return self._fecha.strftime(FORMATO_FECHA)

    def to_dict(self) -> dict[str, str]:
        return {
            "fecha": self.fecha_texto,
            "hora": self._hora,
            "cantidad_ventas": str(self._cantidad_ventas),
            "total_esperado": f"{self._total_esperado:.2f}",
            "efectivo_esperado": f"{self._efectivo_esperado:.2f}",
            "declarado": f"{self._declarado:.2f}",
            "diferencia": f"{self._diferencia:.2f}",
            "sobrante": f"{self._sobrante:.2f}",
            "faltante": f"{self._faltante:.2f}",
            "notas": self._notas,
            "medios": self._medios,
            "usuario": self._usuario,
        }

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> CierreRegistrado:
        fecha = datetime.strptime(datos.get("fecha") or "", FORMATO_FECHA).date()
        return cls(
            fecha,
            datos.get("hora") or "",
            cls._a_entero(datos.get("cantidad_ventas")),
            cls._a_decimal(datos.get("total_esperado")),
            cls._a_decimal(datos.get("efectivo_esperado")),
            cls._a_decimal(datos.get("declarado")),
            cls._a_decimal(datos.get("diferencia")),
            cls._a_decimal(datos.get("sobrante")),
            cls._a_decimal(datos.get("faltante")),
            datos.get("notas") or "",
            datos.get("medios") or "",
            datos.get("usuario") or "",
        )