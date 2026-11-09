from __future__ import annotations

METODO_EFECTIVO = "efectivo"
METODO_DEBITO = "debito"
METODO_CREDITO = "credito"
METODO_MP = "mercadopago"
METODO_TRANSFERENCIA = "transferencia"
METODO_FIADO = "fiado"
METODO_MIXTO = "mixto"

MEDIOS: tuple[tuple[str, str], ...] = (
    ("Efectivo", METODO_EFECTIVO),
    ("Débito", METODO_DEBITO),
    ("Crédito", METODO_CREDITO),
    ("MercadoPago", METODO_MP),
    ("Transferencia", METODO_TRANSFERENCIA),
    ("Fiado", METODO_FIADO),
)

MEDIO_DESCONOCIDO = "desconocido"


def nombre_de(codigo: str) -> str:
    if codigo == METODO_MIXTO:
        return "Mixto"
    for etiqueta, valor in MEDIOS:
        if valor == codigo:
            return etiqueta
    return MEDIO_DESCONOCIDO


def es_efectivo(codigo: str) -> bool:
    return codigo == METODO_EFECTIVO


def pedir_datos(codigo: str) -> tuple[str, bool]:
    if codigo == METODO_DEBITO:
        return "Últimos 4 dígitos de la tarjeta (opcional):", True
    if codigo == METODO_CREDITO:
        return "Últimos 4 dígitos de la tarjeta (opcional):", True
    if codigo == METODO_TRANSFERENCIA:
        return "Referencia o alias de la transferencia (opcional):", True
    return "", False


def descripcion_de(codigo: str, datos: str = "") -> str:
    nombre = nombre_de(codigo)
    return f"{nombre} — {datos}" if datos else nombre