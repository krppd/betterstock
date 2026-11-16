from __future__ import annotations

import json
import sys
from pathlib import Path
from string import Template

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot


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
TAMANO_COMPACTO = float(ESCALA["compacto"]["punto"])
TAMANO_NOTA = float(ESCALA["nota"]["punto"])

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
VERDE_CLARO = COLORES["verde_claro"]
VERDE_OSCURO = COLORES["verde_oscuro"]
VERDE_PRESIONADO = COLORES["verde_presionado"]
VERDE_TEXTO = COLORES["verde_texto"]
VERDE_ENCABEZADO = COLORES["verde_encabezado"]
VERDE_PROFUNDO = COLORES["verde_profundo"]
VERDE_PROFUNDO_BORDE = COLORES["verde_profundo_borde"]
VERDE_PROFUNDO_HOVER = COLORES["verde_profundo_hover"]
VERDE_LATERAL_INICIO = COLORES["verde_lateral_inicio"]
VERDE_LATERAL_MEDIO = COLORES["verde_lateral_medio"]
VERDE_LATERAL_FONDO = COLORES["verde_lateral_fondo"]
VERDE_LATERAL_FONDO_CLARO = COLORES["verde_lateral_fondo_claro"]
VERDE_LATERAL_HOVER = COLORES["verde_lateral_hover"]
VERDE_LATERAL_PRESIONADO = COLORES["verde_lateral_presionado"]
FONDO_FILA = COLORES["fondo_fila"]
SELECCION = COLORES["seleccion"]
GRILLA = COLORES["grilla"]
GRIS_BOTON = COLORES["gris_boton"]
GRIS_HOVER = COLORES["gris_hover"]
GRIS_PRESIONADO = COLORES["gris_presionado"]
GRIS_DESHABILITADO = COLORES["gris_deshabilitado"]
FONDO_DESHABILITADO = COLORES["fondo_deshabilitado"]
BORDE = COLORES["borde"]
TEXTO = COLORES["texto"]
ROJO = COLORES["rojo"]
ROJO_TEXTO = COLORES["rojo_texto"]
ROJO_SUAVE = COLORES["rojo_suave"]
ROJO_PRESIONADO = COLORES["rojo_presionado"]
AMBAR_TEXTO = COLORES["ambar_texto"]
GRIS_TEXTO = COLORES["gris_texto"]
TEXTO_SUAVE = COLORES["texto_suave"]
PULGAR_SCROLL = COLORES["pulgar_scroll"]
PULGAR_SCROLL_HOVER = COLORES["pulgar_scroll_hover"]
PULGAR_SCROLL_PRESIONADO = COLORES["pulgar_scroll_presionado"]
BLANCO = COLORES["blanco"]
BLANCO_CSS = COLORES["blanco_css"]
TRANSPARENTE = COLORES["transparente"]
NINGUNO = COLORES["ninguno"]
FONDO_SUAVE = COLORES["fondo_suave"]
FONDO_INSIGNIA = COLORES["fondo_insignia"]
TEXTO_OSCURO = COLORES["texto_oscuro"]
TEXTO_FUERTE = COLORES["texto_fuerte"]
GRIS_MEDIO = COLORES["gris_medio"]
GRIS_LINEA = COLORES["gris_linea"]
GRIS_APAGADO = COLORES["gris_apagado"]
BORDE_SUAVE = COLORES["borde_suave"]
BORDE_DESTACADO = COLORES["borde_destacado"]
BORDE_POSITIVO = COLORES["borde_positivo"]
BORDE_NEGATIVO = COLORES["borde_negativo"]
PASTILLA_POSITIVA = COLORES["pastilla_positiva"]
PASTILLA_NEGATIVA = COLORES["pastilla_negativa"]
PASTILLA_ALERTA = COLORES["pastilla_alerta"]
PASTILLA_TEAL = COLORES["pastilla_teal"]
PASTILLA_SKY = COLORES["pastilla_sky"]
ACENTO_TEAL = COLORES["acento_teal"]
ACENTO_SKY = COLORES["acento_sky"]
ACENTO_AMBAR = COLORES["acento_ambar"]
ACENTO_ESMERALDA = COLORES["acento_esmeralda"]
PASTILLA_ESMERALDA = COLORES["pastilla_esmeralda"]
ACENTO_BOSQUE = COLORES["acento_bosque"]
PASTILLA_BOSQUE = COLORES["pastilla_bosque"]
ACENTO_LIMA = COLORES["acento_lima"]
PASTILLA_LIMA = COLORES["pastilla_lima"]
PASTILLA_AMBAR = COLORES["pastilla_ambar"]
ROJO_ALERTA = COLORES["rojo_alerta"]
ROJO_OSCURO = COLORES["rojo_oscuro"]
AMBAR_ALERTA = COLORES["ambar_alerta"]
VERDE_ACENTO = COLORES["verde_acento"]
VERDE_GRAFICO = COLORES["verde_grafico"]
VERDE_BOTON_HOVER = COLORES["verde_boton_hover"]
VERDE_LATERAL_OSCURO = COLORES["verde_lateral_oscuro"]
VERDE_LATERAL_FIN = COLORES["verde_lateral_fin"]
SIDEBAR_BTN_INACTIVO_FONDO = COLORES["sidebar_btn_inactivo_fondo"]
SIDEBAR_BTN_INACTIVO_TEXTO = COLORES["sidebar_btn_inactivo_texto"]
SIDEBAR_BTN_INACTIVO_BORDE = COLORES["sidebar_btn_inactivo_borde"]
SIDEBAR_BTN_HOVER_FONDO = COLORES["sidebar_btn_hover_fondo"]
SIDEBAR_BTN_HOVER_BORDE = COLORES["sidebar_btn_hover_borde"]
SIDEBAR_BTN_PRESIONADO = COLORES["sidebar_btn_presionado"]
SIDEBAR_BTN_ACTIVO_FONDO = COLORES["sidebar_btn_activo_fondo"]
SIDEBAR_BTN_ACTIVO_TEXTO = COLORES["sidebar_btn_activo_texto"]
SIDEBAR_BTN_ACTIVO_BORDE = COLORES["sidebar_btn_activo_borde"]

RAD_SUTIL = RADIOS["sutil"]
RAD_INSIGNIA = RADIOS["insignia"]
RAD_CONTROL = RADIOS["control"]
RAD_PANEL = RADIOS["panel"]
RAD_DESTACADO = RADIOS["destacado"]
RAD_TARJETA = RADIOS["tarjeta"]
RAD_LATERAL = RADIOS["lateral"]

ESP_CERO = ESPACIADO["cero"]
ESP_PICO = ESPACIADO["pico"]
ESP_MICRO = ESPACIADO["micro"]
ESP_PEQUENO = ESPACIADO["pequeno"]
ESP_BASICO = ESPACIADO["basico"]
ESP_MEDIANO = ESPACIADO["mediano"]
ESP_GRANDE = ESPACIADO["grande"]
ESP_AMPLIO = ESPACIADO["amplio"]
ESP_EXTRA = ESPACIADO["extra"]
ESP_SECCION = ESPACIADO["seccion"]

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
QTableWidget {
    background-color: ${blanco_css};
    alternate-background-color: ${fondo_fila};
    gridline-color: ${grilla};
    selection-background-color: ${seleccion};
    selection-color: ${texto};
    font-size: ${tam_small}pt;
}
QTableWidget::item {
    padding: ${esp_pequeno}px;
}
QHeaderView {
    font-size: ${tam_small}pt;
}
QHeaderView::section {
    background-color: ${verde_encabezado};
    color: ${blanco_css};
    font-weight: bold;
    padding: ${esp_basico}px;
    border: 0px;
}
QPushButton {
    background-color: ${gris_boton};
    color: ${texto};
    border: 1px solid ${borde};
    border-radius: ${rad_control}px;
    padding: ${esp_pequeno}px ${esp_grande}px;
}
QPushButton:hover {
    background-color: ${gris_hover};
}
QPushButton:pressed {
    background-color: ${gris_presionado};
}
QPushButton:disabled {
    background-color: ${fondo_deshabilitado};
    color: ${gris_deshabilitado};
}
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
QLineEdit, QTextEdit {
    background-color: ${blanco_css};
    border: 1px solid ${borde};
    border-radius: ${rad_control}px;
    padding: ${esp_micro}px ${esp_pequeno}px;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid ${verde};
}
QLabel {
    color: ${texto};
}
QDialog, QMessageBox {
    background-color: ${superficie};
    color: ${texto};
}
QMessageBox QLabel, QDialog QLabel {
    color: ${texto};
    background-color: transparent;
}
QComboBox QAbstractItemView {
    background-color: ${blanco_css};
    selection-background-color: ${verde_oscuro};
    selection-color: ${blanco_css};
    outline: ${ninguno};
}
QComboBox QAbstractItemView::item {
    padding: ${esp_pequeno}px ${esp_basico}px;
    min-height: ${med_alto_item_combo}px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: ${verde_oscuro};
    color: ${blanco_css};
}
QComboBox QAbstractItemView::item:selected {
    background-color: ${verde_oscuro};
    color: ${blanco_css};
}
QComboBox QAbstractItemView {
    background-color: ${blanco_css};
    selection-background-color: ${verde_oscuro};
    selection-color: ${blanco_css};
    outline: ${ninguno};
}
QComboBox QAbstractItemView::item {
    padding: ${esp_pequeno}px ${esp_basico}px;
    min-height: ${med_alto_item_combo}px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: ${verde_oscuro};
    color: ${blanco_css};
}
QComboBox QAbstractItemView::item:selected {
    background-color: ${verde_oscuro};
    color: ${blanco_css};
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

def _hoja_primaria(nombre: str, contexto: dict[str, str]) -> str:
    verde = contexto["verde"]
    verde_oscuro = contexto["verde_oscuro"]
    verde_presionado = contexto["verde_presionado"]
    fondo_deshabilitado = contexto["fondo_deshabilitado"]
    gris_deshabilitado = contexto["gris_deshabilitado"]
    borde = contexto["borde"]
    return (
        f'QPushButton#{nombre} {{'
        f"background-color: {verde}; color: {contexto['blanco_css']}; "
        f"border: 1px solid {verde_oscuro}; border-radius: {RAD_CONTROL}px; "
        f"padding: {ESP_PEQUENO}px {ESP_GRANDE}px; font-weight: bold;}}"
        f'QPushButton#{nombre}:hover {{background-color: {verde_oscuro};}}'
        f'QPushButton#{nombre}:pressed {{background-color: {verde_presionado};}}'
        f'QPushButton#{nombre}:disabled {{background-color: {fondo_deshabilitado}; '
        f"color: {gris_deshabilitado}; border: 1px solid {borde};}}"
    )


def _hoja_destructiva(nombre: str, contexto: dict[str, str]) -> str:
    fondo_deshabilitado = contexto["fondo_deshabilitado"]
    gris_deshabilitado = contexto["gris_deshabilitado"]
    borde = contexto["borde"]
    return (
        f'QPushButton#{nombre} {{'
        f"background-color: {contexto['superficie']}; "
        f"color: {contexto['rojo']}; border: 1px solid {contexto['rojo']}; "
        f"border-radius: {RAD_CONTROL}px; "
        f"padding: {ESP_PEQUENO}px {ESP_GRANDE}px; font-weight: bold;}}"
        f'QPushButton#{nombre}:hover {{background-color: {contexto["rojo_suave"]};}}'
        f'QPushButton#{nombre}:pressed {{background-color: {contexto["rojo_presionado"]};}}'
        f'QPushButton#{nombre}:disabled {{background-color: {fondo_deshabilitado}; '
        f"color: {gris_deshabilitado}; border: 1px solid {borde};}}"
    )


def qss(oscuro: bool = False) -> str:
    contexto = _contexto(oscuro)
    base = PLANTILLA_QSS.substitute(contexto)
    scroll = "\n".join(regla.substitute(contexto) for regla in REGLAS_SCROLL)
    botones = "\n".join(
        [_hoja_primaria(nombre, contexto) for nombre in BOTONES_PRIMARIOS]
        + [_hoja_destructiva(nombre, contexto) for nombre in BOTONES_DESTRUCTIVOS]
    )
    return base + "\n" + scroll + "\n" + botones


TEMA_APP = qss()
TEMA_APP_OSCURO = qss(oscuro=True)


class Tema(QObject):
    """Puente de tema para QML: expone los tokens y avisa cuando cambian.

    ``color`` devuelve siempre el valor del tema activo, así que el QML se
    repinta al conmutar entre modo claro y oscuro.
    """

    temaCambiado = pyqtSignal()

    def __init__(self, padre: QObject | None = None) -> None:
        super().__init__(padre)
        try:
            from qfluentwidgets import qconfig

            qconfig.themeChanged.connect(self._al_cambiar_tema)
        except Exception:
            pass

    def _al_cambiar_tema(self, *_args) -> None:
        self.temaCambiado.emit()

    @pyqtSlot(str, result=str)
    def color(self, nombre: str) -> str:
        return color_tema(nombre)

    @pyqtSlot(result=bool)
    def oscuro(self) -> bool:
        return _tema_oscuro()

    @pyqtSlot(str, result=int)
    def radio(self, nombre: str) -> int:
        return RADIOS[nombre]

    @pyqtSlot(str, result=float)
    def tamano(self, nombre: str) -> float:
        return float(ESCALA[_clave_tamano(nombre)]["punto"])

    @pyqtSlot(str, result=int)
    def espaciado(self, nombre: str) -> int:
        return ESPACIADO[nombre]

    @pyqtSlot(str, result=int)
    def medida(self, nombre: str) -> int:
        return MEDIDAS[nombre]

    @pyqtSlot(str, result=int)
    def peso(self, nombre: str) -> int:
        return PESOS[nombre]

    @pyqtSlot(str, result="QVariantMap")
    def sombra(self, nombre: str) -> dict:
        return dict(SOMBRAS[nombre])

    @pyqtSlot(result="QVariantMap")
    def caracteristicas(self) -> dict:
        return {TAG_TABULAR: 1}

    @pyqtSlot(result=str)
    def familia(self) -> str:
        return FAMILIA_FUENTE


_PUENTES: list[Tema] = []


def puente_tema(padre: QObject) -> Tema:
    puente = Tema(padre)
    _PUENTES.append(puente)
    return puente
