from __future__ import annotations

from PyQt6.QtGui import QFontMetrics

from ui.estilos import TAMANO_DISPLAY, fuente
from ui.widgets.etiqueta_rodante import EtiquetaRodante


def _etiqueta(texto: str = "$ 0,00") -> EtiquetaRodante:
    etiqueta = EtiquetaRodante(texto)
    etiqueta.setFont(fuente(TAMANO_DISPLAY, negrita=True, tabular=True))
    return etiqueta


def test_el_tamano_alcanza_para_el_texto() -> None:
    etiqueta = _etiqueta("$ 45.050,00")
    metricas = QFontMetrics(etiqueta.font())
    assert etiqueta.sizeHint().width() >= metricas.horizontalAdvance("$ 45.050,00")


def test_el_alto_alcanza_para_la_linea() -> None:
    etiqueta = _etiqueta("$ 45.050,00")
    metricas = QFontMetrics(etiqueta.font())
    assert etiqueta.sizeHint().height() >= etiqueta._alto_caja(metricas)


def test_el_texto_nuevo_no_queda_afuera_durante_la_animacion() -> None:
    etiqueta = _etiqueta("$ 0,00")
    etiqueta.show()
    etiqueta.mostrar("$ 45.050,00")
    metricas = QFontMetrics(etiqueta.font())
    assert etiqueta.sizeHint().width() >= metricas.horizontalAdvance("$ 45.050,00")
    assert etiqueta.sizeHint().height() >= etiqueta._alto_caja(metricas)


def test_el_texto_se_ve_entero_despues_de_la_animacion() -> None:
    etiqueta = _etiqueta("$ 0,00")
    etiqueta.show()
    etiqueta.mostrar("$ 45.050,00")
    etiqueta._temporizador.stop()
    etiqueta._rollo.terminar()
    etiqueta._fijo = None
    etiqueta.updateGeometry()
    assert etiqueta.text() == "$ 45.050,00"
    assert etiqueta.sizeHint().width() >= QFontMetrics(
        etiqueta.font()).horizontalAdvance("$ 45.050,00")
