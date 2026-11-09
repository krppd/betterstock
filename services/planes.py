from __future__ import annotations

from typing import Any

PLAN_GRATIS: dict[str, Any] = {
    "id": "gratis",
    "titulo": "Gratis",
    "limites": {
        "productos": 50,
        "dias_estadisticas": 365,
        "importaciones": 1,
    },
}

CONTACTO: str = "hola@betterstock.tech"

CLAVES_LIMITES: tuple[str, ...] = ("productos", "dias_estadisticas", "importaciones")


def plan_activo(registro) -> dict[str, Any]:
    if registro is not None:
        obtener = getattr(registro, "plan_activo", None)
        if callable(obtener):
            plan = obtener()
            if isinstance(plan, dict) and plan:
                return dict(plan)
    return dict(PLAN_GRATIS)


def limite(registro, clave: str) -> int | None:
    plan = plan_activo(registro)
    limites = plan.get("limites") or {}
    valor = limites.get(clave)
    if valor is None:
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def excedido(registro, clave: str, valor: int) -> bool:
    maximo = limite(registro, clave)
    if maximo is None:
        return False
    return valor > maximo


def admite(registro, clave: str) -> bool:
    plan = plan_activo(registro)
    funciones = plan.get("funciones") or {}
    if isinstance(funciones, dict) and bool(funciones.get(clave, False)):
        return True
    return False


def texto_limites(registro) -> str:
    plan = plan_activo(registro)
    limites = plan.get("limites") or {}
    partes = []
    for clave in CLAVES_LIMITES:
        valor = limites.get(clave)
        if valor is None:
            continue
        partes.append(_etiqueta(clave, valor))
    return " · ".join(partes)


def _etiqueta(clave: str, valor: Any) -> str:
    if clave == "productos":
        return f"Hasta {valor} productos"
    if clave == "dias_estadisticas":
        return f"Estadísticas de {valor} días"
    if clave == "importaciones":
        return f"{valor} importación" if valor == 1 else f"{valor} importaciones"
    return f"{clave}: {valor}"
