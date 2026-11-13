#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

VERDE_SIDEBAR = "#1E8149"
VERDE_ANTERIOR = "#17703F"
FONDO_TOOLTIP = "#111827"

REQUISITOS = (
    ("blanco sobre el verde del sidebar y del header", "#FFFFFF", VERDE_SIDEBAR, 1.0),
    ("valor del tooltip", "#FFFFFF", FONDO_TOOLTIP, 1.0),
    ("detalle del tooltip", "#E5E7EB", FONDO_TOOLTIP, 1.0),
    ("nota del tooltip", "#9CA3AF", FONDO_TOOLTIP, 1.0),
    ("variación positiva", "#4ADE80", FONDO_TOOLTIP, 1.0),
    ("variación negativa", "#F87171", FONDO_TOOLTIP, 1.0),
    ("variación neutra", "#D1D5DB", FONDO_TOOLTIP, 1.0),
)

REFERENCIAS = (
    ("blanco sobre el verde anterior", "#FFFFFF", VERDE_ANTERIOR, 1.0),
    ("etiqueta del sidebar al 85% sobre el verde nuevo", "#FFFFFF", VERDE_SIDEBAR, 0.85),
    ("etiqueta del sidebar al 85% sobre el verde anterior", "#FFFFFF", VERDE_ANTERIOR, 0.85),
)


def _componentes(hexa: str) -> tuple[float, float, float]:
    limpio = hexa.lstrip("#")
    return tuple(int(limpio[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _luminancia(hexa: str) -> float:
    canales = []
    for valor in _componentes(hexa):
        if valor <= 0.03928:
            canales.append(valor / 12.92)
        else:
            canales.append(((valor + 0.055) / 1.055) ** 2.4)
    rojo, verde, azul = canales
    return 0.2126 * rojo + 0.7152 * verde + 0.0722 * azul


def _mezclar(frente: str, fondo: str, alfa: float) -> str:
    canales_frente = _componentes(frente)
    canales_fondo = _componentes(fondo)
    mezclado = tuple(
        round((a * alfa + b * (1 - alfa)) * 255) for a, b in zip(canales_frente, canales_fondo)
    )
    return "#{:02X}{:02X}{:02X}".format(*mezclado)


def contraste(frente: str, fondo: str) -> float:
    lum_frente = _luminancia(frente)
    lum_fondo = _luminancia(fondo)
    claro, oscuro = max(lum_frente, lum_fondo), min(lum_frente, lum_fondo)
    return (claro + 0.05) / (oscuro + 0.05)


def _reporte(par, obligatorio: bool) -> bool:
    nombre, frente, fondo, alfa = par
    color_real = _mezclar(frente, fondo, alfa) if alfa < 1.0 else frente
    ratio = contraste(color_real, fondo)
    cumple = ratio >= 4.5
    if not cumple and obligatorio:
        print(f"FALLA {ratio:5.2f}:1  {nombre} ({color_real} sobre {fondo})")
    else:
        print(f"{'OK   ' if cumple else 'AVISO'} {ratio:5.2f}:1  {nombre} ({color_real} sobre {fondo})")
    return cumple


def main() -> int:
    problemas = 0
    print("Exigido (AA 4.5:1):")
    for par in REQUISITOS:
        if not _reporte(par, True):
            problemas += 1
    print("\nReferencias:")
    for par in REFERENCIAS:
        _reporte(par, False)
    if problemas:
        print(f"\n{problemas} par(es) por debajo de 4.5:1 (AA)")
        return 1
    print("\nTodos los pares exigidos cumplen AA (4.5:1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
