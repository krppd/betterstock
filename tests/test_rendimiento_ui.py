from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QTableWidget

import views.ventana_base as modulo_base
from ui.estilos import TAG_TABULAR
from views.ventana_base import VentanaBase
from views.ventana_login import VentanaLogin


def test_llenar_tabla_reutiliza_dos_fuentes(monkeypatch) -> None:
    creadas: list[bool] = []
    original = modulo_base.fuente

    def contador(*args, **kwargs):
        creadas.append(bool(kwargs.get("tabular", False)))
        return original(*args, **kwargs)

    monkeypatch.setattr(modulo_base, "fuente", contador)
    tabla = QTableWidget(0, 3)
    VentanaBase.llenar_tabla(
        tabla,
        [["Producto", "123", "$ 4,50"], ["Otro", "texto", ""]],
        ["#4477aa", None],
    )

    assert len(creadas) == 2
    assert sorted(creadas) == [False, True]

    tabular = QFont.Tag(TAG_TABULAR)
    assert not tabla.item(0, 0).font().isFeatureSet(tabular)
    assert tabla.item(0, 1).font().isFeatureSet(tabular)
    assert tabla.item(0, 2).font().isFeatureSet(tabular)
    assert not tabla.item(1, 1).font().isFeatureSet(tabular)
    assert tabla.item(0, 0).foreground().color().name() == "#4477aa"


def test_login_crea_los_cuadros_del_logo_bajo_demanda(aplicacion_global) -> None:
    ventana = VentanaLogin(object())
    try:
        assert ventana._indice_cuadro == 0
        assert ventana.ui.lblLogo.pixmap().width() == ventana.ANCHO_LOGO

        for _ in range(ventana.CUADROS_TIRA):
            ventana._avanzar_logo()

        assert ventana._indice_cuadro == ventana.CUADROS_TIRA - 1
        assert ventana._cuadro_actual.width() == ventana.ANCHO_LOGO
        assert ventana._cuadro_actual.height() == ventana.ALTO_LOGO
        assert not ventana._temporizador_logo.isActive()
        assert ventana._tira_logo is None
    finally:
        ventana.deleteLater()


def test_el_recorte_del_logo_no_cambio(aplicacion_global) -> None:
    ventana = VentanaLogin(object())
    try:
        tira = ventana._tira_logo
        assert tira is not None

        def cuadro_original(numero: int):
            return tira.copy(
                (numero % ventana.COLUMNAS_TIRA) * ventana.ANCHO_CUADRO,
                (numero // ventana.COLUMNAS_TIRA) * ventana.ALTO_CUADRO,
                ventana.ANCHO_CUADRO,
                ventana.ALTO_CUADRO,
            ).scaled(
                ventana.ANCHO_LOGO,
                ventana.ALTO_LOGO,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        assert ventana._cuadro_actual.toImage() == cuadro_original(0).toImage()

        for _ in range(ventana.CUADROS_TIRA - 1):
            ventana._avanzar_logo()

        ultimo = ventana.CUADROS_TIRA - 1
        assert ventana._cuadro_actual.toImage() == cuadro_original(ultimo).toImage()
    finally:
        ventana.deleteLater()
