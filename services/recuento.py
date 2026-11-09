from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from models.movimiento import Movimiento
from services.excepciones import ErrorValidacion
from services.gestor_stock import GestorStock
from utils.formato import redondear_cantidad


def motivo_recuento(fecha: date) -> str:
    return f"Recuento {fecha.strftime('%d/%m/%Y')}"


class ServicioRecuento:
    def __init__(self, gestor_stock: GestorStock) -> None:
        self._gestor_stock = gestor_stock

    def aplicar(self, conteos: dict[str, float], fecha: date | None = None) -> list[Movimiento]:
        dia = fecha or date.today()
        motivo = motivo_recuento(dia)
        normalizados = self._normalizar(conteos)
        movimientos: list[Movimiento] = []
        for codigo, cantidad in normalizados:
            producto = self._gestor_stock.buscar_producto(codigo)
            if producto is None:
                continue
            if redondear_cantidad(producto.stock_actual) == cantidad:
                continue
            movimientos.append(
                self._gestor_stock.registrar_ajuste(codigo, cantidad, dia, motivo))
        return movimientos

    def _normalizar(self, conteos: dict[str, float]) -> list[tuple[str, float]]:
        productos = self._gestor_stock.productos_por_codigo()
        normalizados: list[tuple[str, float]] = []
        for codigo, cantidad in conteos.items():
            clave = str(codigo).strip()
            if not clave:
                raise ErrorValidacion("El código del producto es obligatorio.")
            if clave not in productos:
                raise ErrorValidacion(f"No existe un producto con código {clave}.")
            normalizados.append((clave, self._cantidad(clave, cantidad)))
        return normalizados

    @staticmethod
    def _cantidad(codigo: str, cantidad: float) -> float:
        try:
            numero = Decimal(str(cantidad).strip().replace(",", "."))
        except (InvalidOperation, ValueError, ArithmeticError) as error:
            raise ErrorValidacion(
                f"El conteo del producto {codigo} no es un número válido.") from error
        if not numero.is_finite():
            raise ErrorValidacion(f"El conteo del producto {codigo} no es un número válido.")
        if numero < 0:
            raise ErrorValidacion(f"El conteo del producto {codigo} no puede ser negativo.")
        return redondear_cantidad(numero)
