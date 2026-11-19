"""Dueño único del tema claro/oscuro de BetterStock.

En lugar de que cada widget Fluent reciba su propio QSS y lo reescriba en cada
cambio de tema, este gestor arma UNA hoja maestra por tema y la aplica con un
solo QApplication.setStyleSheet.
"""
from __future__ import annotations

import os
import time
import weakref

from PyQt6.QtWidgets import QApplication, QWidget
from qfluentwidgets import Theme
from qfluentwidgets.common import style_sheet as _ss
from qfluentwidgets.common.style_sheet import FluentStyleSheet, getStyleSheet

# Hojas con selectores de clase de Fluent: seguras de globalizar.
_GLOBALES = (
    FluentStyleSheet.LABEL,
    FluentStyleSheet.PIVOT,
    FluentStyleSheet.SPIN_BOX,
    FluentStyleSheet.CHECK_BOX,
    FluentStyleSheet.COMBO_BOX,
    FluentStyleSheet.LINE_EDIT,
    FluentStyleSheet.LIST_VIEW,
    FluentStyleSheet.TABLE_VIEW,
    FluentStyleSheet.CARD_WIDGET,
    FluentStyleSheet.TIME_PICKER,
    FluentStyleSheet.FLUENT_WINDOW,
    FluentStyleSheet.MENU,
    FluentStyleSheet.CALENDAR_PICKER,
    FluentStyleSheet.NAVIGATION_INTERFACE,
)
# DIALOG, TOOL_TIP y SWITCH_BUTTON traen reglas sobre QLabel/QWidget sin clase
# que, globalizadas, pintarían toda la app. Quedan fuera de _GLOBALES: se
# aplican por widget y sin registrar, y como nacen al abrirse, ya vienen con el
# tema vigente.
#
# BUTTON también queda por widget: cambiar BUTTON en el QSS global con botones
# Fluent vivos hace segfault en Qt6/xcb. Por widget el cambio de tema es seguro,
# así que se re-renderiza solo en los botones existentes.

_GESTOR: "GestorTema | None" = None
_instrumentado = False
_vigilados: "weakref.WeakSet[QWidget]" = weakref.WeakSet()
_botones: "weakref.WeakSet[QWidget]" = weakref.WeakSet()
_contadores = {"updateStyleSheet": 0, "widget": 0, "global": 0}


def _depuracion() -> bool:
    return os.environ.get("BT_DEBUG_TEMA") == "1"


def _instrumentar() -> None:
    """Cuenta sweeps y setStyleSheet cuando BT_DEBUG_TEMA=1. El hook queda puesto."""
    global _instrumentado
    if _instrumentado or not _depuracion():
        return
    _instrumentado = True
    original_update = _ss.updateStyleSheet
    original_widget = QWidget.setStyleSheet
    original_global = QApplication.setStyleSheet

    def update_style_sheet(*args, **kwargs):
        _contadores["updateStyleSheet"] += 1
        return original_update(*args, **kwargs)

    def set_widget_style_sheet(widget, hoja):
        _contadores["widget"] += 1
        return original_widget(widget, hoja)

    def set_global_style_sheet(app, hoja):
        _contadores["global"] += 1
        return original_global(app, hoja)

    _ss.updateStyleSheet = update_style_sheet
    QWidget.setStyleSheet = set_widget_style_sheet
    QApplication.setStyleSheet = set_global_style_sheet


class GestorTema:

    def __init__(self, qt: QApplication) -> None:
        self._qt = qt
        self._instalado = False
        self._clave: tuple[bool, float, str] | None = None
        self._escala: float | None = None
        self._hojas: dict[tuple[bool, float, str], str] = {}

    def instalar(self, aplicar_hoja: bool = True) -> None:
        """Parchea Fluent y aplica el tema vigente una sola vez."""
        global _GESTOR
        _GESTOR = self
        if self._instalado:
            return
        self._instalado = True
        self._parchear()
        _instrumentar()
        if aplicar_hoja:
            self.aplicar(_oscuro_actual())

    def aplicar(self, oscuro: bool) -> None:
        """Aplica el tema completo con una sola hoja global. Idempotente."""
        from ui import estilos

        inicio = time.perf_counter()
        escala = estilos.escala()
        if escala != self._escala:
            self._hojas.clear()
            self._escala = escala
        acento = estilos.color_fluent(oscuro)
        self._fijar_qconfig(oscuro)
        clave = (bool(oscuro), escala, acento)
        if clave != self._clave:
            estilos._asegurar_estilo(self._qt)
            familia = estilos._cargar_fuentes()
            self._qt.setPalette(estilos.paleta(oscuro))
            self._qt.setStyleSheet(self._hoja_maestra(oscuro, escala, acento))
            self._qt.setFont(estilos.fuente(
                estilos.TAMANO_BODY, familia=familia or estilos.FAMILIA_FUENTE))
            self._clave = clave
            _refrescar_botones(Theme.DARK if oscuro else Theme.LIGHT)
            _refrescar_estilos_propios()
        if _depuracion():
            ms = (time.perf_counter() - inicio) * 1000
            print(
                f"[BT_DEBUG_TEMA] tema={'oscuro' if oscuro else 'claro'} {ms:.1f} ms "
                f"updateStyleSheet={_contadores['updateStyleSheet']} "
                f"widget.setStyleSheet={_contadores['widget']} "
                f"app.setStyleSheet={_contadores['global']}")

    def _fijar_qconfig(self, oscuro: bool) -> None:
        """Actualiza el estado de Fluent sin disparar el sweep de updateStyleSheet."""
        from qfluentwidgets import qconfig

        from ui import estilos

        qconfig.set(
            qconfig.themeMode, Theme.DARK if oscuro else Theme.LIGHT, save=False)
        estilos.aplicar_color_fluent(oscuro=oscuro)

    def _hoja_maestra(self, oscuro: bool, escala: float, acento: str) -> str:
        from ui import estilos
        from ui.tema import TEMA_APP, TEMA_APP_OSCURO

        clave = (bool(oscuro), escala, acento)
        hoja = self._hojas.get(clave)
        if hoja is not None:
            return hoja
        tema = Theme.DARK if oscuro else Theme.LIGHT
        propia = TEMA_APP_OSCURO if oscuro else TEMA_APP
        partes = [getStyleSheet(estilo, tema) for estilo in _GLOBALES]
        partes += [estilos._escalar_qss(propia, escala), estilos._qss_escala_tactil()]
        hoja = "\n".join(parte for parte in partes if parte)
        self._hojas[clave] = hoja
        return hoja

    def _parchear(self) -> None:
        """Hace que las hojas Fluent las cubra la hoja maestra, no cada widget."""
        if getattr(_ss, "_betterstock_parcheado", False):
            return
        original_set = _ss.setStyleSheet
        original_add = _ss.addStyleSheet

        def set_style_sheet(widget, source, theme=Theme.AUTO, register=True):
            if isinstance(source, FluentStyleSheet):
                if source in _GLOBALES:
                    _vigilar_estilo_propio(widget)
                    return
                # shortcut: el widget conserva el QSS de su tema de creación;
                # upgrade si algún widget no global llega a ser persistente.
                widget.setStyleSheet(getStyleSheet(source, theme))
                if source is FluentStyleSheet.BUTTON:
                    _botones.add(widget)
                _vigilar_estilo_propio(widget)
                return
            return original_set(widget, source, theme, register)

        def add_style_sheet(widget, source, theme=Theme.AUTO, register=True):
            if isinstance(source, FluentStyleSheet) and source in _GLOBALES:
                return
            return original_add(widget, source, theme, register)

        _ss.setStyleSheet = set_style_sheet
        _ss.addStyleSheet = add_style_sheet
        _ss._betterstock_parcheado = True


def _vigilar_estilo_propio(widget: QWidget) -> None:
    """Mantiene vivos los CustomStyleSheet (colores por widget) sin registrar el Fluent."""
    if getattr(widget, "_bt_vigilantes", None) is not None:
        return
    widget._bt_vigilantes = (
        _ss.CustomStyleSheetWatcher(widget),
        _ss.DirtyStyleSheetWatcher(widget),
    )
    for vigilante in widget._bt_vigilantes:
        widget.installEventFilter(vigilante)
    _vigilados.add(widget)


def _refrescar_botones(tema: Theme) -> None:
    """Re-renderiza el QSS Fluent de cada botón; globalizarlo con botones vivos crashea."""
    for widget in list(_botones):
        try:
            widget.setStyleSheet(getStyleSheet(FluentStyleSheet.BUTTON, tema))
        except RuntimeError:
            _botones.discard(widget)


def _refrescar_estilos_propios() -> None:
    """Re-renderiza los CustomStyleSheet con el tema nuevo; el QSS base ya es global."""
    for widget in list(_vigilados):
        try:
            if (widget.property(_ss.CustomStyleSheet.LIGHT_QSS_KEY)
                    or widget.property(_ss.CustomStyleSheet.DARK_QSS_KEY)):
                _ss.addStyleSheet(widget, _ss.CustomStyleSheet(widget))
        except RuntimeError:
            _vigilados.discard(widget)


def _oscuro_actual() -> bool:
    from qfluentwidgets import isDarkTheme

    return bool(isDarkTheme())


def obtener_gestor(qt: QApplication | None = None) -> "GestorTema | None":
    """Devuelve el gestor instalado; lo crea si la app no lo hizo antes."""
    global _GESTOR
    if _GESTOR is None:
        qt = qt if qt is not None else QApplication.instance()
        if qt is None:
            return None
        # Instalar tarde con widgets vivos: parchea Fluent pero no reaplica la
        # hoja global, que hace segfault en xcb.
        _GESTOR = GestorTema(qt)
        _GESTOR.instalar(aplicar_hoja=not qt.topLevelWidgets())
    return _GESTOR
