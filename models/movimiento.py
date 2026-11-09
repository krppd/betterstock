from __future__ import annotations

from abc import abstractmethod
from datetime import date, datetime
from typing import ClassVar, Self

from models.entidad import Entidad
from utils.formato import cantidad_a_texto, formatear_cantidad, redondear_cantidad


MOTIVO_DEVOLUCION_PREFIJO = "Devolución venta"


class Movimiento(Entidad):
    COLUMNAS: ClassVar[tuple[str, ...]] = (
        "id_movimiento", "fecha", "codigo_producto", "tipo", "cantidad", "motivo",
    )
    FORMATO_FECHA: ClassVar[str] = "%d/%m/%Y"
    TIPO: ClassVar[str] = ""

    _tipos_registrados: ClassVar[dict[str, type[Movimiento]]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.TIPO:
            Movimiento._tipos_registrados[cls.TIPO] = cls

    def __init__(
        self,
        fecha: date,
        codigo_producto: str,
        cantidad: float,
        motivo: str = "",
        id_movimiento: int | None = None,
    ) -> None:
        self._id_movimiento = id_movimiento
        self._fecha = fecha
        self._codigo_producto = str(codigo_producto)
        self.cantidad = cantidad
        self._motivo = str(motivo)

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
    def codigo_producto(self) -> str:
        return self._codigo_producto

    @property
    def cantidad(self) -> float:
        return self._cantidad

    @cantidad.setter
    def cantidad(self, valor: float) -> None:
        valor = redondear_cantidad(valor)
        if valor < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        self._cantidad = valor

    @property
    def motivo(self) -> str:
        return self._motivo

    @property
    def tipo(self) -> str:
        return self.TIPO

    def asignar_id(self, id_movimiento: int) -> None:
        if self._id_movimiento is not None:
            raise ValueError("El movimiento ya tiene un número asignado.")
        self._id_movimiento = id_movimiento

    @abstractmethod
    def aplicar_a(self, stock_actual: float) -> float:
        pass

    @classmethod
    def tipos_disponibles(cls) -> list[str]:
        return list(Movimiento._tipos_registrados)

    @classmethod
    def crear(
        cls,
        tipo: str,
        fecha: date,
        codigo_producto: str,
        cantidad: float,
        motivo: str = "",
        id_movimiento: int | None = None,
    ) -> Movimiento:
        subclase = Movimiento._tipos_registrados.get(tipo)
        if subclase is None:
            raise ValueError(f"Tipo de movimiento desconocido: {tipo!r}")
        return subclase(fecha, codigo_producto, cantidad, motivo, id_movimiento)

    def to_dict(self) -> dict[str, str]:
        return {
            "id_movimiento": self.identificador,
            "fecha": self.fecha_texto,
            "codigo_producto": self._codigo_producto,
            "tipo": self.tipo,
            "cantidad": cantidad_a_texto(self._cantidad),
            "motivo": self._motivo,
        }

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        id_texto = datos.get("id_movimiento") or ""
        return cls.crear(
            tipo=datos.get("tipo") or "",
            fecha=datetime.strptime(datos.get("fecha") or "", cls.FORMATO_FECHA).date(),
            codigo_producto=datos.get("codigo_producto") or "",
            cantidad=cls._a_decimal(datos.get("cantidad")),
            motivo=datos.get("motivo") or "",
            id_movimiento=int(id_texto) if id_texto.isdigit() else None,
        )

    def __str__(self) -> str:
        return (f"{self.fecha_texto} {self.tipo} de {formatear_cantidad(self._cantidad)} u."
                f" del producto {self._codigo_producto}")


class MovimientoEntrada(Movimiento):
    TIPO = "Entrada"

    def aplicar_a(self, stock_actual: float) -> float:
        return redondear_cantidad(stock_actual + self.cantidad)


class MovimientoSalida(Movimiento):
    TIPO = "Salida"

    def aplicar_a(self, stock_actual: float) -> float:
        return max(0.0, redondear_cantidad(stock_actual - self.cantidad))


class MovimientoAjuste(Movimiento):
    TIPO = "Ajuste"

    def aplicar_a(self, stock_actual: float) -> float:
        return self.cantidad
