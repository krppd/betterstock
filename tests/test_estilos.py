from __future__ import annotations


def test_las_fuentes_se_registran_una_sola_vez() -> None:
    from ui import estilos

    estilos._cargar_fuentes()
    identificadores = list(estilos._fuentes_cache[2])
    assert identificadores, "las fuentes empaquetadas deberían quedar registradas"

    estilos._cargar_fuentes()
    assert estilos._fuentes_cache[2] == identificadores


def test_el_estilo_es_el_nativo_en_windows(monkeypatch) -> None:
    from ui import estilos

    monkeypatch.setattr(estilos.sys, "platform", "win32")
    assert estilos._estilo_base() == "windowsvista"

    monkeypatch.setattr(estilos.sys, "platform", "linux")
    assert estilos._estilo_base() == "Fusion"


def _gestor_limpio():
    from PyQt6.QtWidgets import QApplication

    from ui import estilos
    from ui import gestor_tema
    from ui.gestor_tema import GestorTema

    aplicacion = QApplication.instance() or QApplication([])
    estilos.aplicar_escala(estilos.ESCALA_NORMAL)
    # Los botones Fluent vivos de otros tests quedan en estos WeakSets y se
    # re-renderizan al cambiar de tema. Limpiarlos aísla este gestor.
    gestor_tema._botones.clear()
    gestor_tema._vigilados.clear()
    gestor = GestorTema(aplicacion)
    gestor.instalar()
    return gestor


def _contar_hojas(monkeypatch) -> dict[str, int]:
    from PyQt6.QtWidgets import QApplication, QWidget

    contador = {"global": 0, "widget": 0}
    original_global = QApplication.setStyleSheet
    original_widget = QWidget.setStyleSheet

    def global_(self, hoja):
        contador["global"] += 1
        return original_global(self, hoja)

    def widget_(self, hoja):
        contador["widget"] += 1
        return original_widget(self, hoja)

    monkeypatch.setattr(QApplication, "setStyleSheet", global_)
    monkeypatch.setattr(QWidget, "setStyleSheet", widget_)
    return contador


def test_cambio_de_tema_aplica_una_sola_hoja(monkeypatch) -> None:
    from qfluentwidgets import isDarkTheme

    gestor = _gestor_limpio()
    contador = _contar_hojas(monkeypatch)

    gestor.aplicar(not isDarkTheme())

    # Lo que importa es una sola hoja global. Los setStyleSheet por widget
    # vienen de los suscriptores de themeChanged que siguen vivos de otros
    # tests; no los dispara el gestor.
    assert contador["global"] == 1


def test_qfluent_no_hace_update_style_sheet_en_el_cambio(monkeypatch) -> None:
    from qfluentwidgets import isDarkTheme
    from qfluentwidgets.common import style_sheet

    gestor = _gestor_limpio()

    def fallar(*_args, **_kwargs):
        raise AssertionError("updateStyleSheet no debe correr al cambiar de tema")

    monkeypatch.setattr(style_sheet, "updateStyleSheet", fallar)
    gestor.aplicar(not isDarkTheme())


def test_idempotencia(monkeypatch) -> None:
    from qfluentwidgets import isDarkTheme

    gestor = _gestor_limpio()
    contador = _contar_hojas(monkeypatch)

    gestor.aplicar(isDarkTheme())
    gestor.aplicar(isDarkTheme())

    assert contador["global"] == 0


def test_obtener_gestor_tarde_no_reaplica_la_hoja_global(monkeypatch) -> None:
    from PyQt6.QtWidgets import QApplication, QWidget

    from ui import gestor_tema

    aplicacion = QApplication.instance()
    widget = QWidget()
    try:
        contador = _contar_hojas(monkeypatch)
        monkeypatch.setattr(gestor_tema, "_GESTOR", None)

        gestor = gestor_tema.obtener_gestor(aplicacion)

        assert gestor is not None
        assert contador["global"] == 0
    finally:
        widget.deleteLater()
