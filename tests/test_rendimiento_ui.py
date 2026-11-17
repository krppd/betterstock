from __future__ import annotations

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
        assert len(ventana._cuadros_logo) == 1
        assert ventana.ui.lblLogo.pixmap().width() == ventana.ANCHO_LOGO

        for _ in range(ventana.CUADROS_TIRA):
            ventana._avanzar_logo()

        assert len(ventana._cuadros_logo) == ventana.CUADROS_TIRA
        assert all(
            cuadro.width() == ventana.ANCHO_LOGO and cuadro.height() == ventana.ALTO_LOGO
            for cuadro in ventana._cuadros_logo
        )
        assert not ventana._temporizador_logo.isActive()
        assert ventana._tira_logo is None
    finally:
        ventana.deleteLater()
