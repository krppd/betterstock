from __future__ import annotations

import json
import sys
from pathlib import Path
from string import Template


def _ruta_tokens() -> Path:
    raiz = getattr(sys, "_MEIPASS", None)
    if raiz is not None:
        return Path(raiz) / "ui" / "tokens.json"
    return Path(__file__).resolve().parent / "tokens.json"


RUTA_TOKENS = _ruta_tokens()

with RUTA_TOKENS.open(encoding="utf-8") as archivo:
    tokens: dict = json.load(archivo)

COLORES: dict[str, str] = tokens["colores"]
COLORES_OSCUROS: dict[str, str] = tokens.get("colores_oscuros", {})
RADIOS: dict[str, int] = tokens["radios"]
TIPOGRAFIA: dict = tokens["tipografia"]
ESPACIADO: dict[str, int] = tokens["espaciado"]
MEDIDAS: dict[str, int] = tokens["medidas"]
SOMBRAS: dict[str, dict] = tokens["sombras"]

ESCALA: dict[str, dict] = TIPOGRAFIA["escala"]
PESOS: dict[str, int] = TIPOGRAFIA["pesos"]
FAMILIA_FUENTE: str = TIPOGRAFIA["familia"]
TAG_TABULAR: str = TIPOGRAFIA["tag_tabular"]

ALIAS_TAMANOS: dict[str, str] = {
    "micro": "micro",
    "small": "pequeno",
    "pequeno": "pequeno",
    "body": "cuerpo",
    "cuerpo": "cuerpo",
    "subtitle": "subtitulo",
    "subtitulo": "subtitulo",
    "title": "titulo",
    "titulo": "titulo",
    "display": "display",
    "hero": "heroe",
    "heroe": "heroe",
    "compacto": "compacto",
    "nota": "nota",
}


def _clave_tamano(nombre: str) -> str:
    clave = ALIAS_TAMANOS.get(nombre)
    if clave is None:
        raise KeyError(f"tamaño desconocido: {nombre}")
    return clave


def color(nombre: str) -> str:
    return COLORES[nombre]


def color_tema(nombre: str) -> str:
    """Devuelve el color del token ``nombre`` según el tema Fluent activo."""
    if _tema_oscuro():
        return COLORES_OSCUROS.get(nombre, COLORES.get(nombre, nombre))
    return COLORES.get(nombre, nombre)


def _tema_oscuro() -> bool:
    try:
        from qfluentwidgets import isDarkTheme

        return bool(isDarkTheme())
    except Exception:
        return False


VERDE_FLUENT = COLORES["acento_fluent"]
VERDE_FLUENT_OSCURO = COLORES_OSCUROS.get("acento_fluent", COLORES["verde_claro"])


def color_fluent(oscuro: bool | None = None) -> str:
    """Devuelve el verde de acento de Fluent según el tema activo."""
    if oscuro is None:
        oscuro = _tema_oscuro()
    return VERDE_FLUENT_OSCURO if oscuro else VERDE_FLUENT


def radio(nombre: str) -> int:
    return RADIOS[nombre]


def tamano(nombre: str) -> float:
    return float(ESCALA[_clave_tamano(nombre)]["punto"])


def espaciado(nombre: str) -> int:
    return ESPACIADO[nombre]


def medida(nombre: str) -> int:
    return MEDIDAS[nombre]


def peso(nombre: str) -> int:
    return PESOS[nombre]


def sombra(nombre: str) -> dict:
    return SOMBRAS[nombre]


def familia() -> str:
    return FAMILIA_FUENTE


def interlinea(nombre: str) -> float:
    return float(ESCALA[_clave_tamano(nombre)].get("interlinea", 1.2))


TAMANO_MICRO = int(ESCALA["micro"]["punto"])
TAMANO_SMALL = int(ESCALA["pequeno"]["punto"])
TAMANO_BODY = int(ESCALA["cuerpo"]["punto"])
TAMANO_SUBTITLE = int(ESCALA["subtitulo"]["punto"])
TAMANO_TITLE = int(ESCALA["titulo"]["punto"])
TAMANO_DISPLAY = int(ESCALA["display"]["punto"])
TAMANO_HERO = int(ESCALA["heroe"]["punto"])

LINEA_MICRO = ESCALA["micro"]["interlinea"]
LINEA_SMALL = ESCALA["pequeno"]["interlinea"]
LINEA_BODY = ESCALA["cuerpo"]["interlinea"]
LINEA_SUBTITLE = ESCALA["subtitulo"]["interlinea"]
LINEA_TITLE = ESCALA["titulo"]["interlinea"]
LINEA_DISPLAY = ESCALA["display"]["interlinea"]
LINEA_HERO = ESCALA["heroe"]["interlinea"]

ESPACIO_MICRO = ESCALA["micro"]["espaciado"]
ESPACIO_SMALL = ESCALA["pequeno"]["espaciado"]
ESPACIO_BODY = ESCALA["cuerpo"]["espaciado"]
ESPACIO_SUBTITLE = ESCALA["subtitulo"]["espaciado"]
ESPACIO_TITLE = ESCALA["titulo"]["espaciado"]
ESPACIO_DISPLAY = ESCALA["display"]["espaciado"]
ESPACIO_HERO = ESCALA["heroe"]["espaciado"]

ROLES: dict[str, tuple[int, float, float]] = {
    "micro": (TAMANO_MICRO, LINEA_MICRO, ESPACIO_MICRO),
    "small": (TAMANO_SMALL, LINEA_SMALL, ESPACIO_SMALL),
    "body": (TAMANO_BODY, LINEA_BODY, ESPACIO_BODY),
    "subtitle": (TAMANO_SUBTITLE, LINEA_SUBTITLE, ESPACIO_SUBTITLE),
    "title": (TAMANO_TITLE, LINEA_TITLE, ESPACIO_TITLE),
    "display": (TAMANO_DISPLAY, LINEA_DISPLAY, ESPACIO_DISPLAY),
    "hero": (TAMANO_HERO, LINEA_HERO, ESPACIO_HERO),
}

LINEA_POR_TAMANO: dict[int, float] = {
    TAMANO_MICRO: LINEA_MICRO,
    TAMANO_SMALL: LINEA_SMALL,
    TAMANO_BODY: LINEA_BODY,
    TAMANO_SUBTITLE: LINEA_SUBTITLE,
    TAMANO_TITLE: LINEA_TITLE,
    TAMANO_DISPLAY: LINEA_DISPLAY,
    TAMANO_HERO: LINEA_HERO,
}

ESPACIO_POR_TAMANO: dict[int, float] = {
    TAMANO_MICRO: ESPACIO_MICRO,
    TAMANO_SMALL: ESPACIO_SMALL,
    TAMANO_BODY: ESPACIO_BODY,
    TAMANO_SUBTITLE: ESPACIO_SUBTITLE,
    TAMANO_TITLE: ESPACIO_TITLE,
    TAMANO_DISPLAY: ESPACIO_DISPLAY,
    TAMANO_HERO: ESPACIO_HERO,
}

VERDE = COLORES["verde"]
VERDE_OSCURO = COLORES["verde_oscuro"]
VERDE_PRESIONADO = COLORES["verde_presionado"]
VERDE_TEXTO = COLORES["verde_texto"]
FONDO_FILA = COLORES["fondo_fila"]
SELECCION = COLORES["seleccion"]
GRIS_BOTON = COLORES["gris_boton"]
BORDE = COLORES["borde"]
TEXTO = COLORES["texto"]
ROJO = COLORES["rojo"]
ROJO_TEXTO = COLORES["rojo_texto"]
AMBAR_TEXTO = COLORES["ambar_texto"]
PULGAR_SCROLL = COLORES["pulgar_scroll"]
PULGAR_SCROLL_HOVER = COLORES["pulgar_scroll_hover"]
PULGAR_SCROLL_PRESIONADO = COLORES["pulgar_scroll_presionado"]
BLANCO = COLORES["blanco"]

BOTONES_PRIMARIOS = (
    "btnCobrar",
    "btnGuardar",
    "btnIngresar",
    "btnPago",
    "btnCerrarCaja",
    "btnRegistrar",
    "btnGuardarToken",
    "btnElegir",
    "btnImportar",
)

BOTONES_DESTRUCTIVOS = (
    "btnEliminar",
    "btnQuitar",
    "btnAnular",
)


def _contexto(oscuro: bool = False) -> dict[str, str]:
    base = dict(COLORES)
    if oscuro:
        base.update(COLORES_OSCUROS)
    contexto = {nombre: str(valor) for nombre, valor in base.items()}
    contexto.update({f"rad_{nombre}": str(valor) for nombre, valor in RADIOS.items()})
    contexto.update({f"esp_{nombre}": str(valor) for nombre, valor in ESPACIADO.items()})
    contexto.update({f"med_{nombre}": str(valor) for nombre, valor in MEDIDAS.items()})
    contexto["tam_small"] = str(ESCALA["pequeno"]["punto"])
    contexto["tam_micro"] = str(ESCALA["micro"]["punto"])
    return contexto


PLANTILLA_QSS = Template(
    """
/* Las tablas y sus encabezados los estila Fluent (FluentStyleSheet.TABLE_VIEW):
   fondos transparentes, gris neutro y bordes sutiles. No redefinirlos acá:
   la regla verde heredada tapaba el encabezado vertical de números de fila. */
QFrame#frameSidebar {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0.0 ${verde_lateral_inicio},
        stop: 0.04 ${verde_lateral_medio},
        stop: 0.12 ${verde},
        stop: 1.0 ${verde_claro}
    );
    border: ${ninguno};
    border-top-left-radius: ${rad_lateral}px;
    border-bottom-left-radius: ${rad_lateral}px;
}
QFrame#frameSidebar QLabel {
    color: ${blanco};
    font-size: ${tam_micro}pt;
    font-weight: bold;
    padding: ${esp_basico}px ${esp_cero}px ${esp_cero}px ${esp_mediano}px;
}
QFrame#frameSidebar QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0.0 ${blanco},
        stop: 0.85 ${blanco},
        stop: 1.0 ${verde_lateral_fondo}
    );
    color: ${verde_profundo};
    border: 1px solid ${borde_sombra_tenue};
    border-radius: ${rad_destacado}px;
    padding: ${esp_pequeno}px ${esp_amplio}px;
    text-align: left;
}
QFrame#frameSidebar QPushButton:hover {
    background: ${verde_lateral_hover};
    border: 1px solid ${borde_sombra_fuerte};
    font-weight: bold;
}
QFrame#frameSidebar QPushButton:pressed {
    background: ${verde_lateral_presionado};
    border: 1px solid ${borde_sombra_medio};
}
QFrame#frameSidebar QPushButton[pagina="true"] {
    background-color: ${verde_profundo};
    color: ${blanco};
    border: 1px solid ${verde_profundo_borde};
    font-weight: bold;
}
QFrame#frameSidebar QPushButton[pagina="true"]:hover {
    background-color: ${verde_profundo_hover};
}
QComboBox QAbstractItemView {
    background-color: ${blanco_css};
    selection-background-color: ${verde_oscuro};
    selection-color: ${texto_inverso};
    outline: ${ninguno};
}
QComboBox QAbstractItemView::item {
    padding: ${esp_pequeno}px ${esp_basico}px;
    min-height: ${med_alto_item_combo}px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: ${verde_oscuro};
    color: ${texto_inverso};
}
QComboBox QAbstractItemView::item:selected {
    background-color: ${verde_oscuro};
    color: ${texto_inverso};
}
"""
)

REGLAS_SCROLL = (
    Template("QScrollBar:vertical { background: ${transparente}; width: ${med_ancho_scroll}px; margin: ${med_margen_scroll}px; }"),
    Template("QScrollBar:horizontal { background: ${transparente}; height: ${med_ancho_scroll}px; margin: ${med_margen_scroll}px; }"),
    Template("QScrollBar::handle:vertical { background: ${pulgar_scroll}; min-height: ${med_minimo_scroll}px; border-radius: ${rad_sutil}px; }"),
    Template("QScrollBar::handle:vertical:hover { background: ${pulgar_scroll_hover}; }"),
    Template("QScrollBar::handle:vertical:pressed { background: ${pulgar_scroll_presionado}; }"),
    Template("QScrollBar::handle:horizontal { background: ${pulgar_scroll}; min-width: ${med_minimo_scroll}px; border-radius: ${rad_sutil}px; }"),
    Template("QScrollBar::handle:horizontal:hover { background: ${pulgar_scroll_hover}; }"),
    Template("QScrollBar::handle:horizontal:pressed { background: ${pulgar_scroll_presionado}; }"),
    Template("QScrollBar::add-line:vertical { height: ${esp_cero}px; }"),
    Template("QScrollBar::sub-line:vertical { height: ${esp_cero}px; }"),
    Template("QScrollBar::add-line:horizontal { width: ${esp_cero}px; }"),
    Template("QScrollBar::sub-line:horizontal { width: ${esp_cero}px; }"),
    Template("QScrollBar::add-page:vertical { background: ${ninguno}; }"),
    Template("QScrollBar::sub-page:vertical { background: ${ninguno}; }"),
    Template("QScrollBar::add-page:horizontal { background: ${ninguno}; }"),
    Template("QScrollBar::sub-page:horizontal { background: ${ninguno}; }"),
)

PLANTILLA_BOTON = Template(
    "QPushButton#${nombre} {"
    "background-color: ${fondo}; color: ${texto}; "
    "border: 1px solid ${borde_boton}; border-radius: ${rad_control}px; "
    "font-weight: bold;}"
    "QPushButton#${nombre}:hover {background-color: ${hover};}"
    "QPushButton#${nombre}:pressed {background-color: ${presionado};}"
    "QPushButton#${nombre}:disabled {background-color: ${fondo_deshabilitado}; "
    "color: ${gris_deshabilitado}; border: 1px solid ${borde};}"
)

# (fondo, texto, borde, hover, presionado)
_FAMILIAS_BOTON = {
    "primaria": ("verde", "texto_inverso", "verde_oscuro", "verde_oscuro", "verde_presionado"),
    "destructiva": ("superficie", "rojo", "rojo", "rojo_suave", "rojo_presionado"),
}


def _hoja_boton(nombre: str, contexto: dict[str, str], familia: str) -> str:
    fondo, texto, borde, hover, presionado = (
        contexto[token] for token in _FAMILIAS_BOTON[familia])
    return PLANTILLA_BOTON.substitute(
        contexto, nombre=nombre, fondo=fondo, texto=texto,
        borde_boton=borde, hover=hover, presionado=presionado)


def qss(oscuro: bool = False) -> str:
    contexto = _contexto(oscuro)
    base = PLANTILLA_QSS.substitute(contexto)
    scroll = "\n".join(regla.substitute(contexto) for regla in REGLAS_SCROLL)
    botones = "\n".join(
        [_hoja_boton(nombre, contexto, "primaria") for nombre in BOTONES_PRIMARIOS]
        + [_hoja_boton(nombre, contexto, "destructiva") for nombre in BOTONES_DESTRUCTIVOS]
    )
    return base + "\n" + scroll + "\n" + botones


TEMA_APP = qss()
TEMA_APP_OSCURO = qss(oscuro=True)
