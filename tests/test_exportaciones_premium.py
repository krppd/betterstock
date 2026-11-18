"""Las exportaciones CSV/PDF son funciones premium.

La edición libre no debe traer implementaciones usables de exportación:
ni botones, ni métodos, ni conexiones, ni imports de diálogos/impresoras.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

MODULOS_GENERADOS = [
    RAIZ / "ui" / "generated" / "reportes_ui.py",
    RAIZ / "ui" / "generated" / "alertas_ui.py",
]

VISTAS = [
    RAIZ / "views" / "ventana_reportes.py",
    RAIZ / "views" / "ventana_alertas.py",
]

DISENOS = [
    RAIZ / "ui" / "designer" / "reportes.ui",
    RAIZ / "ui" / "designer" / "alertas.ui",
]

TODOS_LOS_ARCHIVOS = MODULOS_GENERADOS + VISTAS + DISENOS

TOKENS_PROHIBIDOS = [
    "exportar_csv",
    "exportar_pdf",
    "btnExportarPDF",
    "btnExportarCSV",
    "btnExportar",
    "QFileDialog",
    "QPrinter",
    "QtPrintSupport",
]


@pytest.mark.parametrize("ruta", TODOS_LOS_ARCHIVOS, ids=lambda p: p.name)
def test_sin_referencias_a_exportacion_premium(ruta: Path) -> None:
    fuente = ruta.read_text(encoding="utf-8")
    encontrados = [token for token in TOKENS_PROHIBIDOS if token in fuente]
    assert not encontrados, f"{ruta.name} todavía referencia: {encontrados}"


@pytest.mark.parametrize("ruta", DISENOS, ids=lambda p: p.name)
def test_ui_sin_widgets_de_exportacion(ruta: Path) -> None:
    arbol = ET.parse(ruta)  # noqa: S314 - archivos .ui del propio repositorio
    nombres = [
        widget.get("name", "")
        for widget in arbol.iter("widget")
    ]
    de_exportacion = [nombre for nombre in nombres if "exportar" in nombre.lower()]
    assert not de_exportacion, f"{ruta.name} todavía declara: {de_exportacion}"


@pytest.mark.parametrize("ruta", MODULOS_GENERADOS, ids=lambda p: p.name)
def test_ui_form_no_expone_exportar(ruta: Path) -> None:
    import importlib

    modulo = importlib.import_module(
        ruta.relative_to(RAIZ).with_suffix("").as_posix().replace("/", "."))
    clase = modulo.Ui_Form
    assert not hasattr(clase, "exportar_csv")
    assert not hasattr(clase, "exportar_pdf")


ARCHIVOS_SIN_STUBS_PREMIUM = [
    RAIZ / "services" / "estadisticas_ventas.py",
    RAIZ / "views" / "ventana_dashboard.py",
    RAIZ / "views" / "ventana_productos.py",
]


def test_estadisticas_no_expone_stubs_premium() -> None:
    from services.estadisticas_ventas import EstadisticasVentas

    assert not hasattr(EstadisticasVentas, "comparar")
    assert not hasattr(EstadisticasVentas, "total_por_mes")


@pytest.mark.parametrize(
    "ruta", ARCHIVOS_SIN_STUBS_PREMIUM, ids=lambda p: p.name)
def test_sin_rastros_de_premium(ruta: Path) -> None:
    fuente = ruta.read_text(encoding="utf-8")
    assert "PermissionError" not in fuente
    assert "BetterStock Pro" not in fuente
