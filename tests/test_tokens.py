from __future__ import annotations

import re

from ui import tema
from ui.estilos import (
    AMBAR_TEXTO,
    BORDE,
    FONDO_FILA,
    GRIS_BOTON,
    PULGAR_SCROLL,
    ROJO,
    SELECCION,
    TEMA_APP,
    TEXTO,
    VERDE,
    VERDE_OSCURO,
    VERDE_PRESIONADO,
    VERDE_TEXTO,
)

COLORES = tema.tokens["colores"]


def test_tokens_json_tiene_las_secciones_esperadas() -> None:
    assert set(tema.tokens) >= {"colores", "radios", "tipografia", "espaciado"}
    assert set(tema.tokens["tipografia"]) >= {"familia", "pesos", "escala"}


def test_el_qss_no_tiene_colores_fuera_de_la_paleta() -> None:
    literales = set(re.findall(r"#[0-9A-Fa-f]{3,8}|rgba\([^)]*\)", TEMA_APP))
    permitidos = set(COLORES.values())
    assert literales <= permitidos


def test_el_qss_se_genera_desde_los_tokens() -> None:
    assert TEMA_APP == tema.qss()
    assert len(TEMA_APP) > 0


def test_las_tablas_no_redefinen_el_estilo_de_fluent() -> None:
    """El encabezado verde heredado tapaba el estilo neutro de Fluent."""
    assert "QTableWidget {" not in TEMA_APP
    assert "QHeaderView::section:horizontal" not in TEMA_APP
    assert "QHeaderView::section:vertical" not in TEMA_APP


def test_los_constantes_de_estilos_vienen_de_los_tokens() -> None:
    assert VERDE == COLORES["verde"]
    assert VERDE_OSCURO == COLORES["verde_oscuro"]
    assert VERDE_PRESIONADO == COLORES["verde_presionado"]
    assert VERDE_TEXTO == COLORES["verde_texto"]
    assert BORDE == COLORES["borde"]
    assert FONDO_FILA == COLORES["fondo_fila"]
    assert ROJO == COLORES["rojo"]
    assert SELECCION == COLORES["seleccion"]
    assert TEXTO == COLORES["texto"]
    assert GRIS_BOTON == COLORES["gris_boton"]
    assert AMBAR_TEXTO == COLORES["ambar_texto"]
    assert PULGAR_SCROLL == COLORES["pulgar_scroll"]


def test_los_accesos_entregan_los_valores_de_los_tokens() -> None:
    assert tema.color("verde") == COLORES["verde"]
    assert tema.radio("tarjeta") == tema.tokens["radios"]["tarjeta"]
    assert tema.tamano("titulo") == tema.tokens["tipografia"]["escala"]["titulo"]["punto"]
    assert tema.tamano("title") == tema.tamano("titulo")
    assert tema.espaciado("basico") == tema.tokens["espaciado"]["basico"]
    assert tema.peso("negrita") == tema.tokens["tipografia"]["pesos"]["negrita"]
    assert tema.sombra("tarjeta")["color"] == tema.tokens["sombras"]["tarjeta"]["color"]


def test_el_verde_de_la_paleta_es_el_de_la_aplicacion() -> None:
    assert COLORES["verde"] == "#2DBC66"
    assert COLORES["verde_oscuro"] == "#1F9D55"
    assert COLORES["verde_texto"] == "#1A7F37"
