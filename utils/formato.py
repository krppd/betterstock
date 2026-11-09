from __future__ import annotations

import math
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

SIMBOLO = "$"
SEPARADOR_MILES = "."
SEPARADOR_DECIMAL = ","
CENTAVOS = Decimal("0.01")
CERO = Decimal("0.00")
DECIMALES_CANTIDAD = 3
MILESIMA = Decimal("0.001")


def a_decimal(valor: int | float | Decimal | str | None) -> Decimal:
    if valor is None:
        return CERO
    if isinstance(valor, Decimal):
        return _a_centavos(valor)
    if isinstance(valor, bool):
        return CERO
    if isinstance(valor, int):
        return _a_centavos(Decimal(valor))
    if isinstance(valor, float):
        if not math.isfinite(valor):
            return CERO
        return _a_centavos(Decimal(repr(valor)))
    try:
        return _a_centavos(Decimal(str(valor).strip()))
    except (InvalidOperation, ValueError):
        return CERO


def _a_centavos(valor: Decimal) -> Decimal:
    if not valor.is_finite():
        return CERO
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def diferencia(declarado: int | float | Decimal | None,
               esperado: int | float | Decimal | None) -> Decimal:
    return a_decimal(declarado) - a_decimal(esperado)


def formatear_dinero(valor: int | float | Decimal | None) -> str:
    enteros, decimales = _redondear(valor).split(".")
    negativo = enteros.startswith("-")
    enteros = enteros.lstrip("-")
    if negativo and int(enteros) == 0 and int(decimales) == 0:
        negativo = False
    signo = "-" if negativo else ""
    return f"{signo}{SIMBOLO} {_agrupar_miles(enteros)}{SEPARADOR_DECIMAL}{decimales}"


def _redondear(valor: int | float | Decimal | None) -> str:
    if valor is None:
        return "0.00"
    if isinstance(valor, Decimal):
        if not valor.is_finite():
            return "0.00"
        return f"{valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP):f}"
    if isinstance(valor, float) and not math.isfinite(valor):
        return "0.00"
    return f"{valor:.2f}"


def _agrupar_miles(enteros: str) -> str:
    grupos = []
    while len(enteros) > 3:
        grupos.insert(0, enteros[-3:])
        enteros = enteros[:-3]
    grupos.insert(0, enteros)
    return SEPARADOR_MILES.join(grupos)


def redondear_cantidad(valor: int | float | Decimal | str | None) -> float:
    if valor is None:
        return 0.0
    if isinstance(valor, Decimal):
        numero = valor
    else:
        try:
            numero = Decimal(str(valor).strip().replace(",", "."))
        except (InvalidOperation, ValueError, ArithmeticError):
            return 0.0
    if not numero.is_finite():
        return 0.0
    try:
        redondeado = numero.quantize(MILESIMA, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, ArithmeticError):
        return 0.0
    return float(redondeado)


def cantidad_a_texto(valor: int | float | Decimal | str | None) -> str:
    numero = redondear_cantidad(valor)
    if numero == 0:
        return "0"
    return f"{numero:.{DECIMALES_CANTIDAD}f}".rstrip("0").rstrip(".")


def formatear_cantidad(valor: int | float | Decimal | str | None) -> str:
    return cantidad_a_texto(valor).replace(".", SEPARADOR_DECIMAL)


def es_cantidad(valor: object) -> bool:
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        return False
    try:
        numero = Decimal(texto)
    except (InvalidOperation, ValueError, ArithmeticError):
        return False
    return numero.is_finite() and numero >= 0


def parsear_fecha(valor: object) -> date | None:
    texto = str(valor or "").strip()
    if not texto:
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None
