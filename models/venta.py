from __future__ import annotations

import math

from models.producto import Producto
from utils.formato import es_cantidad, formatear_cantidad, formatear_dinero, redondear_cantidad

PREFIJO_COMODIN = "COMODIN"

SEPARADORES_DETALLE = (";", "|")


def tiene_separadores_detalle(texto: str) -> bool:
    return any(separador in str(texto) for separador in SEPARADORES_DETALLE)


def validar_texto_sin_separadores(texto: str, descripcion: str) -> str:
    for separador in SEPARADORES_DETALLE:
        if separador in str(texto):
            raise ValueError(f"{descripcion} no puede llevar {separador!r}.")
    return str(texto)


def es_codigo_comodin(codigo: str) -> bool:
    return str(codigo).startswith(f"{PREFIJO_COMODIN}-")


def validar_descripcion_comodin(descripcion: str) -> str:
    nombre = str(descripcion).strip()
    if not nombre:
        raise ValueError("La descripción del comodín no puede estar vacía.")
    return validar_texto_sin_separadores(nombre, "La descripción del comodín")


def _cantidad_de_texto(texto: str) -> float | None:
    if not es_cantidad(texto):
        return None
    try:
        valor = float(str(texto).strip().replace(",", "."))
    except ValueError:
        return None
    if not math.isfinite(valor):
        return None
    return valor


def candidatos_de_cantidad(texto: str) -> list[tuple[str, float]]:
    partes = str(texto).split("*")
    if len(partes) != 2:
        return [(str(texto), 1.0)]
    izquierda, derecha = partes
    cantidad_izquierda = _cantidad_de_texto(izquierda)
    cantidad_derecha = _cantidad_de_texto(derecha)
    if cantidad_izquierda is None and cantidad_derecha is None:
        return [(str(texto), 1.0)]
    if cantidad_derecha is None:
        return [(derecha, cantidad_izquierda)] if derecha else [(str(texto), 1.0)]
    if cantidad_izquierda is None:
        return [(izquierda, cantidad_derecha)] if izquierda else [(str(texto), 1.0)]
    if cantidad_izquierda <= cantidad_derecha:
        return [(derecha, cantidad_izquierda), (izquierda, cantidad_derecha)]
    return [(izquierda, cantidad_derecha), (derecha, cantidad_izquierda)]


class ItemVenta:
    def __init__(
        self,
        codigo: str,
        nombre: str,
        precio_unitario: float,
        cantidad: float = 1.0,
        alicuota_iva: float = Producto.ALICUOTA_POR_DEFECTO,
        descuento: float = 0.0,
        en_oferta: bool = False,
        es_comodin: bool = False,
    ) -> None:
        if precio_unitario < 0:
            raise ValueError("El precio no puede ser negativo.")
        if alicuota_iva < 0:
            raise ValueError("La alícuota no puede ser negativa.")
        if not 0 <= descuento <= 100:
            raise ValueError("El descuento debe estar entre 0 y 100.")
        self._codigo = codigo
        self._nombre = nombre
        self._precio_unitario = precio_unitario
        self._alicuota_iva = alicuota_iva
        self._descuento = descuento
        self._en_oferta = en_oferta
        self._es_comodin = es_comodin or es_codigo_comodin(codigo)
        self._cantidad = 0.0
        self.cantidad = cantidad

    @property
    def codigo(self) -> str:
        return self._codigo

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def precio_unitario(self) -> float:
        return self._precio_unitario

    @property
    def cantidad(self) -> float:
        return self._cantidad

    @cantidad.setter
    def cantidad(self, valor: float) -> None:
        valor = redondear_cantidad(valor)
        if valor <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        self._cantidad = valor

    @property
    def subtotal(self) -> float:
        return self._precio_unitario * self._cantidad * (1 - self._descuento / 100)

    @property
    def descuento(self) -> float:
        return self._descuento

    @property
    def en_oferta(self) -> bool:
        return self._en_oferta

    @property
    def es_comodin(self) -> bool:
        return self._es_comodin

    @property
    def texto_ambiguo(self) -> bool:
        return tiene_separadores_detalle(self._codigo) or tiene_separadores_detalle(self._nombre)

    @property
    def alicuota_iva(self) -> float:
        return self._alicuota_iva

    @property
    def iva(self) -> float:
        if not self._alicuota_iva:
            return 0.0
        return self.subtotal - self.subtotal / (1 + self._alicuota_iva / 100)

    @property
    def neto(self) -> float:
        return self.subtotal - self.iva

    def aplicar_descuento(self, descuento: float) -> None:
        if not 0 <= descuento <= 100:
            raise ValueError("El descuento debe estar entre 0 y 100.")
        self._descuento = float(descuento)

    def __str__(self) -> str:
        return (f"{formatear_cantidad(self._cantidad)} x {self._nombre}"
                f" = {formatear_dinero(self.subtotal)}")


class Venta:
    def __init__(self) -> None:
        self._items: dict[str, ItemVenta] = {}
        self._descuento_global = 0.0
        self._recargo = 0.0
        self._comodines = 0

    @staticmethod
    def _validar_porcentaje(valor: float, descripcion: str) -> float:
        if not 0 <= valor <= 100:
            raise ValueError(f"{descripcion} debe estar entre 0 y 100.")
        return float(valor)

    @property
    def items(self) -> tuple[ItemVenta, ...]:
        return tuple(self._items.values())

    @property
    def descuento_global(self) -> float:
        return self._descuento_global

    @descuento_global.setter
    def descuento_global(self, valor: float) -> None:
        self._descuento_global = self._validar_porcentaje(float(valor), "El descuento global")

    @property
    def recargo(self) -> float:
        return self._recargo

    @recargo.setter
    def recargo(self, valor: float) -> None:
        self._recargo = self._validar_porcentaje(float(valor), "El recargo")

    @property
    def subtotal(self) -> float:
        return sum(item.subtotal for item in self._items.values())

    @property
    def monto_descuento_global(self) -> float:
        return self.subtotal * self._descuento_global / 100

    @property
    def monto_recargo(self) -> float:
        return (self.subtotal - self.monto_descuento_global) * self._recargo / 100

    @property
    def total(self) -> float:
        return round(self.subtotal - self.monto_descuento_global + self.monto_recargo, 2)

    def esta_vacia(self) -> bool:
        return not self._items

    def cantidad_de(self, codigo: str) -> float:
        item = self._items.get(codigo)
        return item.cantidad if item else 0.0

    def agregar_unidad(self, producto: Producto) -> ItemVenta:
        return self.agregar_cantidad(producto, 1.0)

    def agregar_cantidad(self, producto: Producto, cantidad: float) -> ItemVenta:
        item = self._items.get(producto.codigo)
        if item is None:
            item = ItemVenta(producto.codigo, producto.nombre, producto.precio_vigente(),
                             cantidad=cantidad,
                             alicuota_iva=producto.alicuota_iva,
                             en_oferta=producto.en_oferta())
            self._items[producto.codigo] = item
        else:
            item.cantidad = item.cantidad + cantidad
        return item

    def agregar_comodin(self, descripcion: str, cantidad: float,
                        precio_unitario: float) -> ItemVenta:
        nombre = validar_descripcion_comodin(descripcion)
        self._comodines += 1
        codigo = f"{PREFIJO_COMODIN}-{self._comodines}"
        item = ItemVenta(codigo, nombre, precio_unitario, cantidad=cantidad,
                         es_comodin=True)
        self._items[codigo] = item
        return item

    def vaciar(self) -> None:
        self._items.clear()
        self._descuento_global = 0.0
        self._recargo = 0.0
        self._comodines = 0

    def quitar(self, codigo: str, toda_linea: bool = False) -> None:
        item = self._items.get(codigo)
        if item is None:
            raise ValueError(f"El producto {codigo} no está en la venta.")
        if toda_linea or item.cantidad - 1 <= 0:
            del self._items[codigo]
        else:
            item.cantidad = item.cantidad - 1

    def __len__(self) -> int:
        return len(self._items)

    def __str__(self) -> str:
        return f"Venta de {len(self._items)} producto(s) por {formatear_dinero(self.total)}"
