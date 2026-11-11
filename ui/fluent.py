"""Tokens de color y helpers adaptativos al tema para la migración Fluent.

Centraliza los colores que dependen del modo claro/oscuro para que las vistas
migradas no repitan literales hexadecimales en cada archivo.

Uso:
    from ui.fluent import color
    label.setStyleSheet(f"color: {color('texto')};")
"""
from __future__ import annotations

from qfluentwidgets import isDarkTheme, qconfig


CLARO = {
    "texto": "#1A1A1A",
    "texto_suave": "#6B7280",
    "texto_secundario": "#6B7280",
    "fondo": "#FFFFFF",
    "fondo_suave": "#F8FAFC",
    "fondo_tarjeta": "#FFFFFF",
    "borde": "#E2E8F0",
    "borde_suave": "#E2E8F0",
    "acento": "#2DBC66",
    "primario": "#2DBC66",
    "exito": "#15803D",
    "error": "#B42318",
    "alerta": "#B26A00",
    "informacion": "#0284C7",
    "pastilla_positiva": "#DCFCE7",
    "pastilla_negativa": "#FEE2E2",
    "pastilla_alerta": "#FEF3C7",
    "gris_medio": "#64748B",
    "gris_apagado": "#94A3B8",
    "gris_linea": "#475569",
}

OSCURO = {
    "texto": "#E6E6E6",
    "texto_suave": "#B3B3B3",
    "texto_secundario": "#A0A0A0",
    "fondo": "#181818",
    "fondo_suave": "#1F1F1F",
    "fondo_tarjeta": "#232323",
    "borde": "#3A3A3A",
    "borde_suave": "#333333",
    "acento": "#4FE389",
    "primario": "#4FE389",
    "exito": "#4CAF50",
    "error": "#FF6B6B",
    "alerta": "#FFB74D",
    "informacion": "#64B5F6",
    "pastilla_positiva": "rgba(76, 175, 80, 0.22)",
    "pastilla_negativa": "rgba(255, 107, 107, 0.22)",
    "pastilla_alerta": "rgba(255, 183, 77, 0.22)",
    "gris_medio": "#9CA3AF",
    "gris_apagado": "#6B7280",
    "gris_linea": "#6B7280",
}


def es_oscuro() -> bool:
    try:
        return bool(isDarkTheme())
    except Exception:
        return False


def color(nombre: str) -> str:
    """Devuelve el valor del token `nombre` según el tema activo."""
    paleta = OSCURO if es_oscuro() else CLARO
    if nombre in paleta:
        return paleta[nombre]
    if nombre in CLARO:
        return CLARO[nombre]
    if nombre in OSCURO:
        return OSCURO[nombre]
    return nombre


def conectar_tema(callback) -> None:
    """Llama `callback` ahora y cada vez que cambia el tema Fluent."""
    try:
        qconfig.themeChanged.connect(lambda *_: callback())
    except Exception:
        pass
    try:
        callback()
    except Exception:
        pass
