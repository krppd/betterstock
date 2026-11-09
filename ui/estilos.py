from __future__ import annotations

import re

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

from ui.tema import (
    AMBAR_TEXTO,
    BLANCO,
    BORDE,
    BOTONES_DESTRUCTIVOS,
    BOTONES_PRIMARIOS,
    ESPACIO_BODY,
    ESPACIO_DISPLAY,
    ESPACIO_HERO,
    ESPACIO_MICRO,
    ESPACIO_POR_TAMANO,
    ESPACIO_SMALL,
    ESPACIO_SUBTITLE,
    ESPACIO_TITLE,
    FAMILIA_FUENTE,
    FONDO_DESHABILITADO,
    FONDO_FILA,
    GRILLA,
    GRIS_BOTON,
    GRIS_DESHABILITADO,
    GRIS_HOVER,
    GRIS_PRESIONADO,
    GRIS_TEXTO,
    LINEA_BODY,
    LINEA_DISPLAY,
    LINEA_HERO,
    LINEA_MICRO,
    LINEA_POR_TAMANO,
    LINEA_SMALL,
    LINEA_SUBTITLE,
    LINEA_TITLE,
    PULGAR_SCROLL,
    PULGAR_SCROLL_HOVER,
    PULGAR_SCROLL_PRESIONADO,
    ROJO,
    ROJO_PRESIONADO,
    ROJO_SUAVE,
    ROJO_TEXTO,
    ROLES,
    SELECCION,
    TAG_TABULAR,
    TAMANO_BODY,
    TAMANO_DISPLAY,
    TAMANO_HERO,
    TAMANO_MICRO,
    TAMANO_SMALL,
    TAMANO_SUBTITLE,
    TAMANO_TITLE,
    TEMA_APP,
    TEXTO,
    TEXTO_SUAVE,
    VERDE,
    VERDE_OSCURO,
    VERDE_PRESIONADO,
    VERDE_TEXTO,
)

__all__ = [
    "AMBAR_TEXTO",
    "BLANCO",
    "BORDE",
    "BOTONES_DESTRUCTIVOS",
    "BOTONES_PRIMARIOS",
    "ESCALA_NORMAL",
    "ESPACIO_BODY",
    "ESPACIO_DISPLAY",
    "ESPACIO_HERO",
    "ESPACIO_MICRO",
    "ESPACIO_POR_TAMANO",
    "ESPACIO_SMALL",
    "ESPACIO_SUBTITLE",
    "ESPACIO_TITLE",
    "FAMILIA_FUENTE",
    "FONDO_DESHABILITADO",
    "FONDO_FILA",
    "GRILLA",
    "GRIS_BOTON",
    "GRIS_DESHABILITADO",
    "GRIS_HOVER",
    "GRIS_PRESIONADO",
    "GRIS_TEXTO",
    "LINEA_BODY",
    "LINEA_DISPLAY",
    "LINEA_HERO",
    "LINEA_MICRO",
    "LINEA_POR_TAMANO",
    "LINEA_SMALL",
    "LINEA_SUBTITLE",
    "LINEA_TITLE",
    "PULGAR_SCROLL",
    "PULGAR_SCROLL_HOVER",
    "PULGAR_SCROLL_PRESIONADO",
    "ROJO",
    "ROJO_PRESIONADO",
    "ROJO_SUAVE",
    "ROJO_TEXTO",
    "ROLES",
    "SELECCION",
    "TAG_TABULAR",
    "TAMANO_BODY",
    "TAMANO_DISPLAY",
    "TAMANO_HERO",
    "TAMANO_MICRO",
    "TAMANO_SMALL",
    "TAMANO_SUBTITLE",
    "TAMANO_TITLE",
    "TEMA_APP",
    "TEXTO",
    "TEXTO_SUAVE",
    "VERDE",
    "VERDE_OSCURO",
    "VERDE_PRESIONADO",
    "VERDE_TEXTO",
    "alto_linea",
    "aplicar_escala",
    "aplicar_tema",
    "escala",
    "fuente",
    "fuente_de_rol",
]


ESCALA_NORMAL = 1.0
PUNTO_MINIMO = 8

_escala_activa = ESCALA_NORMAL
_PATRON_PUNTO = re.compile(r"(font-size:\s*)(\d+(?:\.\d+)?)(\s*pt)")
_PATRON_PX = re.compile(r"((?:min-height|min-width):\s*)(\d+(?:\.\d+)?)(\s*px)")


def _anotar_fuentes(lineas: list[str]) -> None:
    """Write a diagnostic log to output/fuentes.log on Windows only."""
    import sys
    if sys.platform != "win32":
        return
    try:
        from config import OUTPUT_DIR
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "fuentes.log").write_text(
            "\n".join(lineas) + "\n", encoding="utf-8")
    except Exception:
        pass


def _cargar_fuentes() -> str:
    from PyQt6.QtGui import QFontDatabase
    from config import RECURSOS_DIR
    carpeta = RECURSOS_DIR / "fuentes"
    if not carpeta.is_dir():
        _anotar_fuentes([f"missing folder: {carpeta}"])
        return ""
    familias: list[str] = []
    lineas: list[str] = []
    archivos = sorted(
        archivo for archivo in carpeta.iterdir()
        if archivo.suffix.lower() in (".otf", ".ttf"))
    for archivo in archivos:
        identificador = QFontDatabase.addApplicationFont(str(archivo))
        if identificador < 0:
            from PyQt6.QtCore import QByteArray
            identificador = QFontDatabase.addApplicationFontFromData(
                QByteArray(archivo.read_bytes()))
        cargadas = (QFontDatabase.applicationFontFamilies(identificador)
                    if identificador >= 0 else [])
        lineas.append(f"{archivo.name}: id={identificador} families={cargadas}")
        for nombre in cargadas:
            limpio = nombre.strip()
            if limpio and limpio not in familias:
                familias.append(limpio)
    elegida = (FAMILIA_FUENTE if FAMILIA_FUENTE in familias
               else familias[0] if familias else "")
    lineas.append(f"chosen: {elegida or '(none)'} (expected: {FAMILIA_FUENTE})")
    _anotar_fuentes(lineas)
    return elegida


def _dpi_logico() -> float:
    pantalla = QApplication.primaryScreen()
    if pantalla is None:
        return 96.0
    dpi = float(pantalla.logicalDotsPerInch())
    return dpi if dpi > 0 else 96.0


def _em_px(punto: int) -> float:
    return punto * _dpi_logico() / 72.0


def escala() -> float:
    return _escala_activa


def aplicar_escala(valor: float) -> None:
    global _escala_activa
    _escala_activa = float(valor) if valor > 0 else ESCALA_NORMAL


def _punto_escalado(punto: int) -> int:
    return max(PUNTO_MINIMO, round(punto * _escala_activa))


def fuente(
    punto: int,
    *,
    negrita: bool = False,
    tabular: bool = False,
    familia: str = FAMILIA_FUENTE,
) -> QFont:
    punto_final = _punto_escalado(punto)
    fuente = QFont(familia)
    fuente.setPointSize(punto_final)
    fuente.setBold(negrita)
    if tabular:
        fuente.setFeature(QFont.Tag(TAG_TABULAR), 1)
    espaciado = ESPACIO_POR_TAMANO.get(punto, 0.0)
    if espaciado:
        fuente.setLetterSpacing(
            QFont.SpacingType.AbsoluteSpacing, espaciado * _em_px(punto_final))
    return fuente


def fuente_de_rol(
    rol: str,
    *,
    negrita: bool = False,
    tabular: bool = False,
) -> QFont:
    punto, _, _ = ROLES[rol]
    return fuente(punto, negrita=negrita, tabular=tabular)


def alto_linea(punto: int) -> int:
    linea = LINEA_POR_TAMANO.get(punto, 1.2)
    return round(_em_px(punto) * linea)


def _escalar_qss(hoja: str, valor: float) -> str:
    if valor == ESCALA_NORMAL:
        return hoja

    def _punto(coincidencia: re.Match) -> str:
        punto = round(float(coincidencia.group(2)) * valor)
        return f"{coincidencia.group(1)}{max(1, punto)}{coincidencia.group(3)}"

    def _px(coincidencia: re.Match) -> str:
        pixeles = round(float(coincidencia.group(2)) * valor)
        return f"{coincidencia.group(1)}{max(1, pixeles)}{coincidencia.group(3)}"

    return _PATRON_PX.sub(_px, _PATRON_PUNTO.sub(_punto, hoja))


def aplicar_tema(qt: QApplication, escala: float | None = None) -> None:
    if escala is not None:
        aplicar_escala(escala)
    qt.setStyle("Fusion")
    familia = _cargar_fuentes()
    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(BLANCO))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(TEXTO))
    paleta.setColor(QPalette.ColorRole.Base, QColor(BLANCO))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor(FONDO_FILA))
    paleta.setColor(QPalette.ColorRole.Text, QColor(TEXTO))
    paleta.setColor(QPalette.ColorRole.Button, QColor(GRIS_BOTON))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(TEXTO))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(VERDE))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(BLANCO))
    qt.setPalette(paleta)
    qt.setStyleSheet(_escalar_qss(TEMA_APP, _escala_activa))
    qt.setFont(fuente(TAMANO_BODY, familia=familia or FAMILIA_FUENTE))
