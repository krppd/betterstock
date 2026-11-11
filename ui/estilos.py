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
    TEMA_APP_OSCURO,
    TEXTO,
    TEXTO_SUAVE,
    VERDE,
    VERDE_OSCURO,
    VERDE_PRESIONADO,
    VERDE_TEXTO,
    color_fluent,
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
    "aplicar_color_fluent",
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
    """Deja un diagnóstico en output/fuentes.log solo en Windows."""
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
        _anotar_fuentes([f"carpeta inexistente: {carpeta}"])
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
        lineas.append(f"{archivo.name}: id={identificador} familias={cargadas}")
        for nombre in cargadas:
            limpio = nombre.strip()
            if limpio and limpio not in familias:
                familias.append(limpio)
    elegida = (FAMILIA_FUENTE if FAMILIA_FUENTE in familias
               else familias[0] if familias else "")
    lineas.append(f"elegida: {elegida or '(ninguna)'} (esperada: {FAMILIA_FUENTE})")
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


def _paleta_oscura() -> QPalette:
    """Paleta equivalent a la clara, pero con superficies y textos de alto contraste."""
    from ui.tema import COLORES_OSCUROS

    def valor(nombre: str, por_defecto: str) -> str:
        return str(COLORES_OSCUROS.get(nombre, por_defecto))

    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(valor("superficie", "#1F1F1F")))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(valor("texto", "#E6E6E6")))
    paleta.setColor(QPalette.ColorRole.Base, QColor(valor("superficie", "#1F1F1F")))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor(valor("fondo_fila", "#252525")))
    paleta.setColor(QPalette.ColorRole.Text, QColor(valor("texto", "#E6E6E6")))
    paleta.setColor(QPalette.ColorRole.Button, QColor(valor("gris_boton", "#2B2B2B")))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(valor("texto", "#E6E6E6")))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(valor("verde", "#2DBC66")))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor(valor("superficie", "#1F1F1F")))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor(valor("texto", "#E6E6E6")))
    return paleta


def _tema_oscuro() -> bool:
    try:
        from qfluentwidgets import isDarkTheme

        return bool(isDarkTheme())
    except Exception:
        return False


def aplicar_color_fluent(qt: QApplication | None = None, oscuro: bool | None = None) -> None:
    """Fija el verde de la marca como color de acento de PyQt-Fluent-Widgets.

    La librería usa #009faa (celeste) por defecto para botones primarios,
    switches, combos y bordes de foco. Se aplica al inicio de la app para que
    login, primer usuario y ventana principal ya nazcan en verde, y se
    vuelve a aplicar cada vez que cambia el tema.
    """
    try:
        from qfluentwidgets import qconfig, setThemeColor
    except Exception:
        return
    color = color_fluent(oscuro)
    try:
        actual = qconfig.get(qconfig.themeColor)
        if actual is not None and QColor(actual).name() == QColor(color).name():
            return
    except Exception:
        pass
    try:
        setThemeColor(color)
    except Exception:
        pass


def aplicar_tema(qt: QApplication, escala: float | None = None) -> None:
    """Aplica la paleta y la hoja de estilos global, adaptadas al tema Fluent activo.

    Tras la migración a Fluent, casi ningún widget usa ya la hoja global: cada
    componente Fluent trae su propio estilo. Por eso la hoja se mantiene
    reducida a lo que todavía la necesita (etiquetas, tablas y scrollbars
    heredados) y se regenera en modo "vacío" cuando no aporta nada, para no
    pagar el costo de reparsear el QSS en cada cambio de tema.
    """
    if escala is not None:
        aplicar_escala(escala)
    if qt.style() is None or qt.style().objectName().lower() != "fusion":
        qt.setStyle("Fusion")
    familia = _cargar_fuentes()
    oscuro = _tema_oscuro()
    aplicar_color_fluent(qt, oscuro)
    if oscuro:
        qt.setPalette(_paleta_oscura())
        hoja = _escalar_qss(TEMA_APP_OSCURO, _escala_activa)
    else:
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
        hoja = _escalar_qss(TEMA_APP, _escala_activa)
    qt.setStyleSheet(hoja + _qss_escala_tactil())
    qt.setFont(fuente(TAMANO_BODY, familia=familia or FAMILIA_FUENTE))
    _conectar_reaplicacion(qt)


def _qss_escala_tactil() -> str:
    """Reglas que agrandan los controles de Fluent en modo táctil.

    Fluent fija el tamaño de sus widgets en píxeles y no expone una escala
    global, así que el modo táctil (1.5x) no los afecta. Estas reglas suben el
    alto mínimo y el cuerpo de la fuente de los controles interactivos, que es
    lo que hace falta para que el dedo alcance todo.
    """
    if _escala_activa <= ESCALA_NORMAL:
        return ""
    return """
QPushButton, QToolButton {
    min-height: 40px;
    font-size: 11pt;
}
LineEdit, TextEdit, ComboBox, SpinBox, DateEdit {
    min-height: 38px;
    font-size: 11pt;
}
CheckBox, RadioButton {
    font-size: 11pt;
    min-height: 32px;
}
"""


def _conectar_reaplicacion(qt: QApplication) -> None:
    """Vuelve a aplicar la hoja global cada vez que Fluent cambia de tema."""
    if getattr(qt, "_betterstock_tema_conectado", False):
        return
    try:
        from qfluentwidgets import qconfig

        qconfig.themeChanged.connect(lambda *_: aplicar_paleta(qt))
        qt._betterstock_tema_conectado = True
    except Exception:
        pass


def _hoja_actual(qt: QApplication) -> str:
    """Devuelve la hoja global que corresponde al tema Fluent activo."""
    if _tema_oscuro():
        return _escalar_qss(TEMA_APP_OSCURO, _escala_activa)
    return _escalar_qss(TEMA_APP, _escala_activa)


def aplicar_paleta(qt: QApplication) -> None:
    """Repinta la app con la paleta y la hoja de estilos del tema activo."""
    oscuro = _tema_oscuro()
    aplicar_color_fluent(qt, oscuro)
    if oscuro:
        qt.setPalette(_paleta_oscura())
        hoja = _escalar_qss(TEMA_APP_OSCURO, _escala_activa)
    else:
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
        hoja = _escalar_qss(TEMA_APP, _escala_activa)
    qt.setStyleSheet(hoja + _qss_escala_tactil())
