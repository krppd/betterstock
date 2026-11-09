from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Self

from models.cierre import ResumenMedios
from models.entidad import Entidad

FORMATO_FECHA = "%d/%m/%Y"


class Turno(Entidad):
    COLUMNAS: tuple[str, ...] = (
        "id", "fecha_apertura", "hora_apertura", "usuario_apertura",
        "fondo_inicial", "fecha_cierre", "hora_cierre", "usuario_cierre",
        "cantidad_ventas", "total_esperado", "efectivo_esperado", "declarado",
        "diferencia", "sobrante", "faltante", "medios", "notas", "estado",
    )

    ESTADO_ABIERTO = "abierto"
    ESTADO_CERRADO = "cerrado"

    def __init__(
        self,
        fecha_apertura: date,
        hora_apertura: str,
        usuario_apertura: str = "",
        fondo_inicial: float = 0.0,
        fecha_cierre: date | None = None,
        hora_cierre: str = "",
        usuario_cierre: str = "",
        cantidad_ventas: int = 0,
        total_esperado: float = 0.0,
        efectivo_esperado: float = 0.0,
        declarado: float = 0.0,
        diferencia: float = 0.0,
        sobrante: float = 0.0,
        faltante: float = 0.0,
        medios: str = "",
        notas: str = "",
        estado: str = ESTADO_ABIERTO,
        id_turno: int | None = None,
    ) -> None:
        self._id_turno = id_turno
        self._fecha_apertura = fecha_apertura
        self._hora_apertura = hora_apertura
        self._usuario_apertura = usuario_apertura.strip()
        self._fondo_inicial = round(float(fondo_inicial), 2)
        self._fecha_cierre = fecha_cierre
        self._hora_cierre = hora_cierre
        self._usuario_cierre = usuario_cierre.strip()
        self._cantidad_ventas = int(cantidad_ventas)
        self._total_esperado = round(float(total_esperado), 2)
        self._efectivo_esperado = round(float(efectivo_esperado), 2)
        self._declarado = round(float(declarado), 2)
        self._diferencia = round(float(diferencia), 2)
        self._sobrante = round(float(sobrante), 2)
        self._faltante = round(float(faltante), 2)
        self._medios = medios
        self._notas = notas.strip()
        self._estado = estado

    @property
    def id_turno(self) -> int | None:
        return self._id_turno

    @property
    def identificador(self) -> str:
        return str(self._id_turno or "")

    @property
    def fecha_apertura(self) -> date:
        return self._fecha_apertura

    @property
    def hora_apertura(self) -> str:
        return self._hora_apertura

    @property
    def usuario_apertura(self) -> str:
        return self._usuario_apertura

    @property
    def fondo_inicial(self) -> float:
        return self._fondo_inicial

    @property
    def fecha_cierre(self) -> date | None:
        return self._fecha_cierre

    @property
    def hora_cierre(self) -> str:
        return self._hora_cierre

    @property
    def usuario_cierre(self) -> str:
        return self._usuario_cierre

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
    def medios(self) -> str:
        return self._medios

    @property
    def notas(self) -> str:
        return self._notas

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def abierto(self) -> bool:
        return self._estado == self.ESTADO_ABIERTO

    @property
    def cerrado(self) -> bool:
        return self._estado == self.ESTADO_CERRADO

    @property
    def cuadra(self) -> bool:
        return abs(self._diferencia) < 0.01

    @property
    def apertura_texto(self) -> str:
        return f"{self._fecha_apertura.strftime(FORMATO_FECHA)} {self._hora_apertura[:5]}"

    @property
    def cierre_texto(self) -> str:
        if self._fecha_cierre is None:
            return ""
        return f"{self._fecha_cierre.strftime(FORMATO_FECHA)} {self._hora_cierre[:5]}"

    def asignar_id(self, id_turno: int) -> None:
        if self._id_turno is not None:
            raise ValueError("El turno ya tiene un número asignado.")
        self._id_turno = id_turno

    def cerrar(self, momento: datetime, usuario: str, arqueo: ArqueoTurno,
               declarado: float, diferencia: float, notas: str = "") -> None:
        self._fecha_cierre = momento.date()
        self._hora_cierre = momento.strftime("%H:%M:%S")
        self._usuario_cierre = usuario.strip()
        self._cantidad_ventas = arqueo.cantidad_ventas
        self._total_esperado = arqueo.total_esperado
        self._efectivo_esperado = arqueo.efectivo_esperado
        self._declarado = round(float(declarado), 2)
        self._diferencia = round(float(diferencia), 2)
        self._sobrante = max(self._diferencia, 0.0)
        self._faltante = max(-self._diferencia, 0.0)
        self._medios = arqueo.medios_texto()
        self._notas = notas.strip()
        self._estado = self.ESTADO_CERRADO

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.identificador,
            "fecha_apertura": self._fecha_apertura.strftime(FORMATO_FECHA),
            "hora_apertura": self._hora_apertura,
            "usuario_apertura": self._usuario_apertura,
            "fondo_inicial": f"{self._fondo_inicial:.2f}",
            "fecha_cierre": (self._fecha_cierre.strftime(FORMATO_FECHA)
                             if self._fecha_cierre is not None else ""),
            "hora_cierre": self._hora_cierre,
            "usuario_cierre": self._usuario_cierre,
            "cantidad_ventas": str(self._cantidad_ventas),
            "total_esperado": f"{self._total_esperado:.2f}",
            "efectivo_esperado": f"{self._efectivo_esperado:.2f}",
            "declarado": f"{self._declarado:.2f}",
            "diferencia": f"{self._diferencia:.2f}",
            "sobrante": f"{self._sobrante:.2f}",
            "faltante": f"{self._faltante:.2f}",
            "medios": self._medios,
            "notas": self._notas,
            "estado": self._estado,
        }

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        id_texto = datos.get("id") or ""
        apertura = datetime.strptime(
            datos.get("fecha_apertura") or "", FORMATO_FECHA).date()
        cierre_texto = datos.get("fecha_cierre") or ""
        cierre = (datetime.strptime(cierre_texto, FORMATO_FECHA).date()
                  if cierre_texto else None)
        return cls(
            apertura,
            datos.get("hora_apertura") or "",
            datos.get("usuario_apertura") or "",
            cls._a_decimal(datos.get("fondo_inicial")),
            cierre,
            datos.get("hora_cierre") or "",
            datos.get("usuario_cierre") or "",
            cls._a_entero(datos.get("cantidad_ventas")),
            cls._a_decimal(datos.get("total_esperado")),
            cls._a_decimal(datos.get("efectivo_esperado")),
            cls._a_decimal(datos.get("declarado")),
            cls._a_decimal(datos.get("diferencia")),
            cls._a_decimal(datos.get("sobrante")),
            cls._a_decimal(datos.get("faltante")),
            datos.get("medios") or "",
            datos.get("notas") or "",
            datos.get("estado") or cls.ESTADO_ABIERTO,
            int(id_texto) if id_texto.isdigit() else None,
        )


@dataclass(frozen=True)
class ArqueoTurno:
    turno: Turno
    esperado_por_medio: ResumenMedios
    cantidad_ventas: int
    ventas_efectivo_brutas: float = 0.0
    cobros_fiado: float = 0.0
    egresos: float = 0.0
    ingresos: float = 0.0
    devoluciones_total: float = 0.0

    @property
    def efectivo_ventas(self) -> float:
        return self.esperado_por_medio.efectivo

    @property
    def efectivo_esperado(self) -> float:
        return round(self.turno.fondo_inicial + self.efectivo_ventas, 2)

    @property
    def total_esperado(self) -> float:
        return round(self.turno.fondo_inicial + self.esperado_por_medio.total(), 2)

    def medios_texto(self) -> str:
        return ";".join(
            f"{codigo}:{importe:.2f}"
            for _, codigo, importe in self.esperado_por_medio.filas()
        )
