from __future__ import annotations

import math
import warnings
from datetime import date
from typing import Self

from models.entidad import Entidad
from utils.formato import (
    cantidad_a_texto,
    formatear_dinero,
    parsear_fecha,
    redondear_cantidad,
)


def _miles(valor: float) -> str:
    return f"{valor:,.3f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


class Producto(Entidad):
    COLUMNAS: tuple[str, ...] = (
        "codigo", "codigo_barras", "nombre", "categoria", "unidad_medida",
        "precio_costo", "precio_venta", "stock_actual", "stock_minimo",
        "alicuota_iva", "precio_oferta", "fecha_vencimiento",
    )

    ALICUOTA_POR_DEFECTO: float = 21.0
    PRECIO_MAXIMO: float = 99_999_999.99
    STOCK_MAXIMO: float = 999_999.999

    def __init__(
        self,
        codigo: str,
        nombre: str,
        categoria: str = "",
        unidad_medida: str = "",
        precio_costo: float = 0.0,
        precio_venta: float = 0.0,
        stock_actual: float = 0.0,
        stock_minimo: float = 0.0,
        alicuota_iva: float = ALICUOTA_POR_DEFECTO,
        precio_oferta: float = 0.0,
        fecha_vencimiento: date | None = None,
        codigo_barras: str = "",
    ) -> None:
        self._codigo = str(codigo)
        self.nombre = nombre
        self.categoria = categoria
        self.unidad_medida = unidad_medida
        self.precio_costo = precio_costo
        self.precio_venta = precio_venta
        self.stock_actual = stock_actual
        self.stock_minimo = stock_minimo
        self.alicuota_iva = alicuota_iva
        self.precio_oferta = precio_oferta
        self.fecha_vencimiento = fecha_vencimiento
        self.codigo_barras = codigo_barras

    @property
    def codigo(self) -> str:
        return self._codigo

    @property
    def identificador(self) -> str:
        return self._codigo

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = str(valor)

    @property
    def categoria(self) -> str:
        return self._categoria

    @categoria.setter
    def categoria(self, valor: str) -> None:
        self._categoria = str(valor)

    @property
    def unidad_medida(self) -> str:
        return self._unidad_medida

    @unidad_medida.setter
    def unidad_medida(self, valor: str) -> None:
        self._unidad_medida = str(valor)

    @property
    def precio_costo(self) -> float:
        return self._precio_costo

    @precio_costo.setter
    def precio_costo(self, valor: float) -> None:
        self._precio_costo = self._validar_precio(float(valor), "El precio de costo")

    @property
    def precio_venta(self) -> float:
        return self._precio_venta

    @precio_venta.setter
    def precio_venta(self, valor: float) -> None:
        self._precio_venta = self._validar_precio(float(valor), "El precio de venta")

    @property
    def precio_oferta(self) -> float:
        return self._precio_oferta

    @precio_oferta.setter
    def precio_oferta(self, valor: float) -> None:
        self._precio_oferta = self._validar_precio(float(valor), "El precio de oferta")

    @property
    def fecha_vencimiento(self) -> date | None:
        return self._fecha_vencimiento

    @fecha_vencimiento.setter
    def fecha_vencimiento(self, valor: date | None) -> None:
        self._fecha_vencimiento = valor

    @property
    def codigo_barras(self) -> str:
        return self._codigo_barras

    @codigo_barras.setter
    def codigo_barras(self, valor: str) -> None:
        self._codigo_barras = str(valor or "").strip()

    def precio_vigente(self) -> float:
        return self._precio_oferta if self._precio_oferta > 0 else self._precio_venta

    def en_oferta(self) -> bool:
        return self._precio_oferta > 0

    @property
    def stock_actual(self) -> float:
        return self._stock_actual

    @stock_actual.setter
    def stock_actual(self, valor: float) -> None:
        self._stock_actual = self._validar_cantidad(float(valor), "El stock actual")

    @property
    def stock_minimo(self) -> float:
        return self._stock_minimo

    @stock_minimo.setter
    def stock_minimo(self, valor: float) -> None:
        self._stock_minimo = self._validar_cantidad(float(valor), "El stock mínimo")

    @property
    def alicuota_iva(self) -> float:
        return self._alicuota_iva

    @alicuota_iva.setter
    def alicuota_iva(self, valor: float) -> None:
        valor = float(valor)
        if valor < 0:
            raise ValueError("La alícuota del IVA no puede ser negativa.")
        self._alicuota_iva = valor

    def esta_en_stock_critico(self) -> bool:
        return self._stock_actual <= self._stock_minimo

    def validar(self) -> None:
        self._validar_precio(self._precio_costo, "El precio de costo")
        self._validar_precio(self._precio_venta, "El precio de venta")
        self._validar_precio(self._precio_oferta, "El precio de oferta")
        self._validar_cantidad(self._stock_actual, "El stock actual")
        self._validar_cantidad(self._stock_minimo, "El stock mínimo")

    def tiene_stock(self) -> bool:
        return self._stock_actual > 0

    def valor_stock(self) -> float:
        return self._precio_costo * self._stock_actual

    def iva_unitario(self) -> float:
        if not self._alicuota_iva:
            return 0.0
        return self._precio_venta - self._precio_venta / (1 + self._alicuota_iva / 100)

    def to_dict(self) -> dict[str, str]:
        return {
            "codigo": self._codigo,
            "nombre": self._nombre,
            "categoria": self._categoria,
            "unidad_medida": self._unidad_medida,
            "precio_costo": str(self._precio_costo),
            "precio_venta": str(self._precio_venta),
            "stock_actual": cantidad_a_texto(self._stock_actual),
            "stock_minimo": cantidad_a_texto(self._stock_minimo),
            "alicuota_iva": str(self._alicuota_iva),
            "precio_oferta": str(self._precio_oferta),
            "codigo_barras": self._codigo_barras,
            "fecha_vencimiento": (
                self._fecha_vencimiento.isoformat()
                if self._fecha_vencimiento is not None else ""
            ),
        }

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> Self:
        producto = cls.__new__(cls)
        producto._cargar_fila(datos)
        return producto

    def _cargar_fila(self, datos: dict[str, str]) -> None:
        texto_alicuota = datos.get("alicuota_iva")
        texto_oferta = datos.get("precio_oferta")
        self._codigo = str(datos.get("codigo") or "")
        self._nombre = str(datos.get("nombre") or "")
        self._categoria = str(datos.get("categoria") or "")
        self._unidad_medida = str(datos.get("unidad_medida") or "")
        self._codigo_barras = str(datos.get("codigo_barras") or "").strip()
        self._precio_costo = max(0.0, self._a_decimal(datos.get("precio_costo")))
        self._precio_venta = max(0.0, self._a_decimal(datos.get("precio_venta")))
        self._stock_actual = max(0.0, redondear_cantidad(self._a_decimal(datos.get("stock_actual"))))
        self._stock_minimo = max(0.0, redondear_cantidad(self._a_decimal(datos.get("stock_minimo"))))
        self._alicuota_iva = (
            self.ALICUOTA_POR_DEFECTO
            if texto_alicuota in (None, "")
            else max(0.0, self._a_decimal(texto_alicuota))
        )
        self._precio_oferta = (
            0.0
            if texto_oferta in (None, "")
            else max(0.0, self._a_decimal(texto_oferta))
        )
        self._fecha_vencimiento = parsear_fecha(datos.get("fecha_vencimiento"))
        self._avisar_precios_fuera_de_rango()

    def _avisar_precios_fuera_de_rango(self) -> None:
        fuera_de_rango = (
            ("el precio de costo", self._precio_costo, self.PRECIO_MAXIMO),
            ("el precio de venta", self._precio_venta, self.PRECIO_MAXIMO),
            ("el precio de oferta", self._precio_oferta, self.PRECIO_MAXIMO),
            ("el stock actual", self._stock_actual, self.STOCK_MAXIMO),
            ("el stock mínimo", self._stock_minimo, self.STOCK_MAXIMO),
        )
        for descripcion, valor, maximo in fuera_de_rango:
            if valor > maximo:
                warnings.warn(
                    f"{descripcion} del producto {self._codigo} supera el máximo "
                    f"permitido ({valor} > {maximo}).",
                    RuntimeWarning,
                    stacklevel=3,
                )

    @staticmethod
    def _validar_precio(valor: float, descripcion: str) -> float:
        if not math.isfinite(valor):
            raise ValueError(f"{descripcion} no es un monto válido.")
        if valor < 0:
            raise ValueError(f"{descripcion} no puede ser negativo.")
        if valor > Producto.PRECIO_MAXIMO:
            raise ValueError(
                f"{descripcion} no puede superar "
                f"{formatear_dinero(Producto.PRECIO_MAXIMO)}.")
        return valor

    @staticmethod
    def _validar_cantidad(valor: float, descripcion: str) -> float:
        if not math.isfinite(valor):
            raise ValueError(f"{descripcion} no es una cantidad válida.")
        if valor < 0:
            raise ValueError(f"{descripcion} no puede ser negativa.")
        if valor > Producto.STOCK_MAXIMO:
            raise ValueError(
                f"{descripcion} no puede superar "
                f"{_miles(Producto.STOCK_MAXIMO)} unidades.")
        return redondear_cantidad(valor)

    def __str__(self) -> str:
        return f"{self._codigo} - {self._nombre}"
