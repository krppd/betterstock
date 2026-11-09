from __future__ import annotations

import pytest
from PyQt6.QtCore import QEvent, QPointF, QPoint, QCoreApplication, Qt
from PyQt6.QtGui import QKeyEvent, QWheelEvent
from PyQt6.QtTest import QTest
from PyQt6.QtCharts import QChartView
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QPlainTextEdit, QTableWidget

from ui.estilos import PULGAR_SCROLL, PULGAR_SCROLL_HOVER, PULGAR_SCROLL_PRESIONADO, TEMA_APP
from ui.scroll_suave import FiltroScrollSuave, instalar_scroll_suave


def reglas_scrollbar() -> list[str]:
    return [bloque.split("{")[0].strip() for bloque in TEMA_APP.split("}") if "QScrollBar" in bloque]


def test_hay_reglas_de_scrollbar() -> None:
    assert len(reglas_scrollbar()) == 16


def test_ninguna_regla_de_scrollbar_usa_coma() -> None:
    for regla in reglas_scrollbar():
        assert "," not in regla, regla


def test_ambas_orientaciones_tienen_ancho_y_alto() -> None:
    assert "QScrollBar:vertical" in reglas_scrollbar()
    assert "QScrollBar:horizontal" in reglas_scrollbar()


def test_pulgar_con_color_de_tema() -> None:
    assert PULGAR_SCROLL in TEMA_APP
    assert PULGAR_SCROLL_HOVER in TEMA_APP
    assert PULGAR_SCROLL_PRESIONADO in TEMA_APP


def test_pulgar_mas_oscuro_en_hover_y_presionado() -> None:
    assert int(PULGAR_SCROLL_HOVER[1:], 16) < int(PULGAR_SCROLL[1:], 16)
    assert int(PULGAR_SCROLL_PRESIONADO[1:], 16) < int(PULGAR_SCROLL_HOVER[1:], 16)


def test_pulgar_con_tamano_minimo_y_radio() -> None:
    assert "min-height: 30px" in TEMA_APP
    assert "min-width: 30px" in TEMA_APP
    assert "border-radius: 4px" in TEMA_APP


def test_flechas_ocultas() -> None:
    assert "QScrollBar::add-line:vertical { height: 0px; }" in TEMA_APP
    assert "QScrollBar::sub-line:vertical { height: 0px; }" in TEMA_APP
    assert "QScrollBar::add-line:horizontal { width: 0px; }" in TEMA_APP
    assert "QScrollBar::sub-line:horizontal { width: 0px; }" in TEMA_APP


def test_carril_invisible() -> None:
    assert "QScrollBar::add-page:vertical { background: none; }" in TEMA_APP
    assert "QScrollBar::sub-page:vertical { background: none; }" in TEMA_APP
    assert "QScrollBar::add-page:horizontal { background: none; }" in TEMA_APP
    assert "QScrollBar::sub-page:horizontal { background: none; }" in TEMA_APP


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


class Espia(FiltroScrollSuave):

    def __init__(self, padre: object | None = None) -> None:
        super().__init__(padre)
        self.decisiones: list[bool] = []

    def eventFilter(self, objetivo, evento) -> bool:
        resultado = super().eventFilter(objetivo, evento)
        if evento.type() == QEvent.Type.Wheel:
            self.decisiones.append(resultado)
        return resultado


@pytest.fixture()
def filtro(aplicacion: QApplication) -> Espia:
    espia = Espia()
    aplicacion.installEventFilter(espia)
    yield espia
    aplicacion.removeEventFilter(espia)


def rueda(widget, dy: int = 120, dx: int = 0, pixel: QPoint = QPoint(0, 0),
          modificadores: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
          espiar: Espia | None = None) -> bool:
    evento = QWheelEvent(
        QPointF(10, 10), QPointF(10, 10), pixel, QPoint(dx, dy),
        Qt.MouseButton.NoButton, modificadores, Qt.ScrollPhase.NoScrollPhase, False,
    )
    if espiar is not None:
        espiar.decisiones.clear()
    QCoreApplication.sendEvent(widget, evento)
    if espiar is not None and espiar.decisiones:
        return espiar.decisiones[0]
    return True


def test_tabla_en_modo_pixel_tras_mostrarse(aplicacion: QApplication, filtro: FiltroScrollSuave) -> None:
    tabla = QTableWidget(300, 4)
    tabla.show()
    aplicacion.processEvents()
    assert tabla.horizontalScrollMode() == QAbstractItemView.ScrollMode.ScrollPerPixel
    assert tabla.verticalScrollMode() == QAbstractItemView.ScrollMode.ScrollPerPixel


def test_popup_de_combo_en_modo_pixel(aplicacion: QApplication, filtro: FiltroScrollSuave) -> None:
    combo = QComboBox()
    combo.addItems([str(i) for i in range(200)])
    combo.show()
    combo.showPopup()
    aplicacion.processEvents()
    assert combo.view().verticalScrollMode() == QAbstractItemView.ScrollMode.ScrollPerPixel


def test_rueda_de_tabla_se_consume(aplicacion: QApplication, filtro: Espia) -> None:
    tabla = QTableWidget(300, 4)
    tabla.show()
    aplicacion.processEvents()
    assert rueda(tabla.viewport(), espiar=filtro) is True


def test_rueda_anima_hasta_el_destino(aplicacion: QApplication, filtro: FiltroScrollSuave) -> None:
    tabla = QTableWidget(300, 4)
    tabla.show()
    aplicacion.processEvents()
    barra = tabla.verticalScrollBar()
    barra.setValue(200)
    rueda(tabla.viewport())
    assert barra.value() == 200
    QTest.qWait(400)
    assert barra.value() == 160


def test_rueda_acumula_varias_veces(aplicacion: QApplication, filtro: FiltroScrollSuave) -> None:
    tabla = QTableWidget(300, 4)
    tabla.show()
    aplicacion.processEvents()
    barra = tabla.verticalScrollBar()
    barra.setValue(200)
    for _ in range(5):
        rueda(tabla.viewport())
    QTest.qWait(400)
    assert barra.value() == 0


def test_rueda_se_interrumpe_con_otra(aplicacion: QApplication, filtro: FiltroScrollSuave) -> None:
    tabla = QTableWidget(300, 4)
    tabla.show()
    aplicacion.processEvents()
    barra = tabla.verticalScrollBar()
    barra.setValue(200)
    rueda(tabla.viewport())
    QTest.qWait(40)
    parcial = barra.value()
    rueda(tabla.viewport())
    QTest.qWait(40)
    assert barra.value() <= parcial
    QTest.qWait(400)
    assert barra.value() == 120


def test_trackpad_va_directo_sin_animar(aplicacion: QApplication, filtro: FiltroScrollSuave) -> None:
    tabla = QTableWidget(300, 4)
    tabla.show()
    aplicacion.processEvents()
    barra = tabla.verticalScrollBar()
    barra.setValue(200)
    rueda(tabla.viewport(), dy=-120, pixel=QPoint(0, 120))
    assert barra.value() == 80


def test_rueda_al_tope_no_pasa_del_rango(aplicacion: QApplication, filtro: FiltroScrollSuave) -> None:
    tabla = QTableWidget(300, 4)
    tabla.show()
    aplicacion.processEvents()
    barra = tabla.verticalScrollBar()
    barra.setValue(barra.maximum())
    rueda(tabla.viewport(), dy=-120)
    QTest.qWait(400)
    assert barra.value() == barra.maximum()


def test_rueda_al_reves_en_el_tope_no_mueve(aplicacion: QApplication, filtro: FiltroScrollSuave) -> None:
    tabla = QTableWidget(300, 4)
    tabla.show()
    aplicacion.processEvents()
    barra = tabla.verticalScrollBar()
    barra.setValue(0)
    rueda(tabla.viewport())
    QTest.qWait(400)
    assert barra.value() == 0


def test_rueda_horizontal_sobre_tabla(aplicacion: QApplication, filtro: Espia) -> None:
    tabla = QTableWidget(4, 60)
    tabla.show()
    aplicacion.processEvents()
    barra = tabla.horizontalScrollBar()
    if barra.maximum() <= barra.minimum():
        pytest.skip("sin desborde horizontal")
    assert rueda(tabla.viewport(), dy=0, dx=-120, espiar=filtro) is True


def test_rueda_con_control_no_se_toca(aplicacion: QApplication, filtro: Espia) -> None:
    tabla = QTableWidget(300, 4)
    tabla.show()
    aplicacion.processEvents()
    assert rueda(tabla.viewport(), modificadores=Qt.KeyboardModifier.ControlModifier, espiar=filtro) is False


def test_grafico_no_se_intercepta(aplicacion: QApplication, filtro: Espia) -> None:
    grafico = QChartView()
    grafico.show()
    aplicacion.processEvents()
    assert rueda(grafico, espiar=filtro) is False


def test_texto_no_se_intercepta(aplicacion: QApplication, filtro: Espia) -> None:
    texto = QPlainTextEdit("linea\n" * 400)
    texto.show()
    aplicacion.processEvents()
    assert rueda(texto.viewport(), espiar=filtro) is False


def test_el_filtro_no_consume_el_teclado(aplicacion: QApplication, filtro: Espia) -> None:
    vistos: list[bool] = []

    class Espia(FiltroScrollSuave):
        def eventFilter(self, objetivo, evento) -> bool:
            resultado = super().eventFilter(objetivo, evento)
            if evento.type() in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride):
                vistos.append(resultado)
            return resultado

    espia_teclado = Espia()
    aplicacion.installEventFilter(espia_teclado)
    tabla = QTableWidget(50, 3)
    tabla.show()
    aplicacion.processEvents()
    for tecla in (Qt.Key.Key_F1, Qt.Key.Key_F4, Qt.Key.Key_Escape, Qt.Key.Key_Down,
                  Qt.Key.Key_PageUp, Qt.Key.Key_PageDown, Qt.Key.Key_Home, Qt.Key.Key_End):
        QCoreApplication.sendEvent(tabla, QKeyEvent(QEvent.Type.KeyPress, tecla, Qt.KeyboardModifier.NoModifier))
    assert vistos
    assert not any(vistos)
