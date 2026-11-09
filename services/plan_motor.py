from __future__ import annotations

from services.planes import (
    CLAVES_LIMITES,
    CONTACTO,
    PLAN_GRATIS,
    texto_limites as _texto_limites_planes,
)


def motor_degradado() -> tuple:
    return ()


def licencia_activa() -> bool:
    return False


def plan_actual() -> dict:
    return dict(PLAN_GRATIS)


def limite(clave: str) -> int | None:
    limites = PLAN_GRATIS.get("limites") or {}
    valor = limites.get(clave)
    if valor is None:
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def excedido(clave: str, valor: int) -> bool:
    maximo = limite(clave)
    if maximo is None:
        return False
    return valor > maximo


def admite(clave: str) -> bool:
    return False


def texto_limites() -> str:
    return _texto_limites_planes(None)


def reposicion_permitida(stock_actual: float, cantidad: float) -> bool:
    return not excedido("productos", (stock_actual or 0.0) + (cantidad or 0.0))


def machine_id_hash() -> str:
    return ""


__all__ = (
    "CLAVES_LIMITES",
    "CONTACTO",
    "PLAN_GRATIS",
    "licencia_activa",
    "machine_id_hash",
    "motor_degradado",
    "plan_actual",
    "limite",
    "excedido",
    "reposicion_permitida",
    "admite",
    "texto_limites",
)
