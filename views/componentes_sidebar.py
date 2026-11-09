from __future__ import annotations

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFontMetrics, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QSizePolicy, QStyle, QStyleOptionButton

from config import RECURSOS_DIR
from ui.estilos import TAMANO_BODY, escala, fuente
from ui.tema import color
from ui.widgets.boton_rodante import BotonRodante

def _px(valor: int) -> int:
    return round(valor * escala())


_CACHE_ICONOS_TINTADOS: dict[tuple[str, str, int], QIcon] = {}


def _icono_tintado(nombre_o_archivo: str, color_hex: str, lado: int = 20) -> QIcon:
    clave = (nombre_o_archivo, color_hex, lado)
    if clave in _CACHE_ICONOS_TINTADOS:
        return _CACHE_ICONOS_TINTADOS[clave]

    ruta = RECURSOS_DIR / "iconos" / nombre_o_archivo
    if not ruta.is_file():
        ruta = RECURSOS_DIR / nombre_o_archivo
    original = QPixmap(str(ruta))
    if original.isNull():
        return QIcon()

    pintado = QPixmap(original.size())
    pintado.fill(Qt.GlobalColor.transparent)
    p = QPainter(pintado)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.drawPixmap(0, 0, original)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    p.fillRect(pintado.rect(), QColor(color_hex))
    p.end()

    px_lado = round(lado * escala())
    escalado = pintado.scaled(
        px_lado, px_lado,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    icono = QIcon(escalado)
    _CACHE_ICONOS_TINTADOS[clave] = icono
    return icono


def _hoja_estados() -> str:
    """Hoja única de los estados del botón.

    Se aplica una sola vez por botón: el estado activo se resuelve por la propiedad
    Qt `pagina`, así que cambiarlo ya no reconstruye ni reparsea un string QSS.
    No hay reglas para el colapso: `paintEvent` dibuja icono y texto a mano, así que
    el `padding` y el `text-align` del estilo no llegan a verse.
    """
    return (
        "QPushButton { "
        f"background-color: {color('sidebar_btn_inactivo_fondo')}; "
        f"color: {color('sidebar_btn_inactivo_texto')}; "
        "font-weight: 600; "
        f"font-size: {_px(13)}px; "
        f"border: 1px solid {color('sidebar_btn_inactivo_borde')}; "
        f"border-radius: {_px(10)}px; "
        "} "
        "QPushButton:hover { "
        f"background-color: {color('sidebar_btn_hover_fondo')}; "
        f"border-color: {color('sidebar_btn_hover_borde')}; "
        "font-weight: 700; "
        "} "
        "QPushButton:pressed { "
        f"background-color: {color('sidebar_btn_presionado')}; "
        "} "
        'QPushButton[pagina="true"] { '
        f"background-color: {color('sidebar_btn_activo_fondo')}; "
        f"color: {color('sidebar_btn_activo_texto')}; "
        "font-weight: 700; "
        f"border: 1px solid {color('sidebar_btn_activo_borde')}; "
        "} "
        'QPushButton[pagina="true"]:hover { '
        f"background-color: {color('verde_lateral_hover')}; "
        "} "
        'QPushButton[pagina="true"]:pressed { '
        f"background-color: {color('verde_lateral_presionado')}; "
        "}"
    )


class BotonSidebar(BotonRodante):
    """Botón lateral animado (BotonRodante) con estados normal, hover y activo."""

    def __init__(self, clave: str, texto: str, icono_archivo: str, parent=None) -> None:
        super().__init__(texto, parent)
        self.clave = clave
        self._texto = texto
        self._icono_archivo = icono_archivo
        self._activo = False
        self._colapsado = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(_px(46))
        self.setFont(fuente(TAMANO_BODY))

        self.setProperty("pagina", "false")
        self.setStyleSheet(_hoja_estados())
        self.actualizar_apariencia()

    def _repolish(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, evento) -> None:
        if not self._colapsado:
            self.repetir()
        super().mousePressEvent(evento)

    def set_activo(self, activo: bool) -> None:
        if activo and not self._colapsado:
            self.repetir()
        if activo == self._activo:
            return
        self._activo = activo
        self.setProperty("pagina", "true" if activo else "false")
        self.setFont(fuente(TAMANO_BODY, negrita=activo))
        self._repolish()
        self.actualizar_apariencia()

    def set_colapsado(self, colapsado: bool, ancho_btn: int = 48) -> None:
        if colapsado == self._colapsado:
            return
        self._colapsado = colapsado
        if colapsado:
            self.setText("")
            self.setToolTip(self._texto)
            self.setMinimumWidth(ancho_btn)
            self.setMaximumWidth(ancho_btn)
        else:
            self.setText(self._texto)
            self.setToolTip("")
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
        self.actualizar_apariencia()

    def paintEvent(self, evento) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        opcion = QStyleOptionButton()
        self.initStyleOption(opcion)
        opcion.text = ""
        opcion.icon = QIcon()
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, opcion, p, self)

        lado_ico = _px(20)
        h = self.height()
        w = self.width()

        if self._colapsado:
            if not self.icon().isNull():
                x_ico = (w - lado_ico) // 2
                y_ico = (h - lado_ico) // 2
                self.icon().paint(p, x_ico, y_ico, lado_ico, lado_ico)
            p.end()
            return

        pad_izq = _px(12)
        espacio_ico = _px(10)
        x_ico = pad_izq
        y_ico = (h - lado_ico) // 2
        if not self.icon().isNull():
            self.icon().paint(p, x_ico, y_ico, lado_ico, lado_ico)
            x_txt = x_ico + lado_ico + espacio_ico
        else:
            x_txt = pad_izq

        p.setFont(self.font())
        col_txt = color("sidebar_btn_activo_texto") if self._activo else color("sidebar_btn_inactivo_texto")
        p.setPen(QColor(col_txt))
        metricas = QFontMetrics(self.font())
        altura = self._alto_caja(metricas)
        base_y = (h - altura) // 2 + metricas.ascent()

        celda = QRect(x_txt, base_y - metricas.ascent(), max(10, w - x_txt - _px(6)), altura)
        p.setClipRect(celda)
        if self._temporizador.isActive():
            self._rollo.dibujar(p, metricas, x_txt, base_y, altura, self._reloj.elapsed())
        else:
            self._rollo.dibujar(p, metricas, x_txt, base_y, altura, None)
        p.end()

    def actualizar_apariencia(self) -> None:
        lado_ico = 20
        color_ico = color("sidebar_btn_activo_texto") if self._activo else color("sidebar_btn_inactivo_texto")
        self.setIcon(_icono_tintado(self._icono_archivo, color_ico, lado_ico))
        self.setIconSize(QSize(_px(lado_ico), _px(lado_ico)))
