from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtTest import QTest

from ui.widgets.notificacion import Notificacion


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def test_muestra_titulo_y_texto(aplicacion: QApplication) -> None:
    padre = QWidget()
    padre.resize(800, 600)
    padre.show()
    aviso = Notificacion(padre, duracion_ms=200)
    aviso.mostrar("Alerta de stock", "Sin yerba")
    assert aviso.isVisible()
    assert aviso._titulo.text() == "Alerta de stock"
    assert "yerba" in aviso._cuerpo.text()


def test_se_oculta_sola(aplicacion: QApplication) -> None:
    padre = QWidget()
    padre.resize(800, 600)
    padre.show()
    aviso = Notificacion(padre, duracion_ms=200)
    aviso.mostrar("Titulo", "cuerpo")
    QTest.qWait(1200)
    assert not aviso.isVisible()


def test_clic_la_cierra_antes(aplicacion: QApplication) -> None:
    padre = QWidget()
    padre.resize(800, 600)
    padre.show()
    aviso = Notificacion(padre, duracion_ms=5000)
    aviso.mostrar("Titulo", "cuerpo")
    QTest.mouseClick(aviso, Qt.MouseButton.LeftButton)
    assert not aviso.isVisible()


def test_arriba_a_la_derecha(aplicacion: QApplication) -> None:
    padre = QWidget()
    padre.resize(800, 600)
    padre.show()
    aviso = Notificacion(padre, duracion_ms=5000)
    aviso.mostrar("Titulo", "cuerpo")
    QTest.qWait(400)
    assert aviso.x() + aviso.width() == padre.width() - Notificacion.MARGEN
    assert aviso.y() == Notificacion.MARGEN


def test_tipo_limite_y_critico_aplican_estilo(aplicacion: QApplication) -> None:
    padre = QWidget()
    padre.resize(800, 600)
    padre.show()
    aviso = Notificacion(padre, duracion_ms=200)
    aviso.mostrar("Tope del plan", "Límite alcanzado", tipo="limite")
    assert aviso._tipo == "limite"
    estilo_limite = aviso._tarjeta.styleSheet()
    assert "#B26A00" in estilo_limite.upper()

    aviso.mostrar("Fallo", "Error crítico", tipo="critico")
    assert aviso._tipo == "critico"
    estilo_critico = aviso._tarjeta.styleSheet()
    assert "#B42318" in estilo_critico.upper()


def test_ancho_se_adapta_a_pantalla_angosta(aplicacion: QApplication) -> None:
    padre = QWidget()
    padre.resize(300, 500)
    padre.show()
    aviso = Notificacion(padre, duracion_ms=200)
    aviso.mostrar("Aviso", "Texto en ventana chica")
    assert aviso.width() <= padre.width()


def test_modo_tactil_escala_ancho_moderado(aplicacion: QApplication) -> None:
    from ui.estilos import aplicar_escala, ESCALA_NORMAL
    padre = QWidget()
    padre.resize(900, 600)
    padre.show()
    try:
        aplicar_escala(1.5)
        aviso = Notificacion(padre, duracion_ms=200)
        aviso.mostrar("Aviso", "Texto táctil")
        assert aviso.width() == 510
    finally:
        aplicar_escala(ESCALA_NORMAL)


def test_con_filas_muestra_el_texto_introductorio(aplicacion: QApplication) -> None:
    padre = QWidget()
    padre.resize(800, 600)
    padre.show()
    aviso = Notificacion(padre, duracion_ms=200)
    aviso.mostrar("Alerta de stock", "Sin stock o en el mínimo:\n• Yerba (stock 0)")
    assert aviso._cuerpo.isVisible()
    assert "Sin stock" in aviso._cuerpo.text()


def test_auto_deteccion_tipo_limite_por_titulo(aplicacion: QApplication) -> None:
    padre = QWidget()
    padre.resize(800, 600)
    padre.show()
    aviso = Notificacion(padre, duracion_ms=200)
    aviso.mostrar("Tope del plan", "Límite alcanzado")
    assert aviso._tipo == "limite"
