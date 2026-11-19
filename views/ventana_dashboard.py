from __future__ import annotations

import datetime
from datetime import date, timedelta
from typing import Any

from PyQt6 import sip
from PyQt6.QtCore import (
    QObject,
    QPointF,
    QRectF,
    QRunnable,
    QSize,
    Qt,
    QThreadPool,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ScrollArea,
    SegmentedWidget,
    StrongBodyLabel,
    SubtitleLabel,
    TitleLabel,
    TransparentPushButton,
    isDarkTheme,
    themeColor,
)

from config import RECURSOS_DIR
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from ui.estilos import (
    ESCALA_NORMAL,
    TAMANO_BODY,
    TAMANO_SMALL,
    TAMANO_SUBTITLE,
    TAMANO_TITLE,
    escala,
    fuente,
)
from ui.fluent import CLARO, OSCURO, color, conectar_tema
from ui.tema import color_tema
from utils.formato import formatear_cantidad, formatear_dinero


def _px(valor: int) -> int:
    return round(valor * escala())


_PASTILLAS: dict[str, str] = {
    "ventas": "pastilla_esmeralda",
    "pedidos": "pastilla_bosque",
    "ticket": "pastilla_ambar",
    "unidades": "pastilla_lima",
}

_ACENTOS: dict[str, str] = {
    "ventas": "acento_esmeralda",
    "pedidos": "acento_bosque",
    "ticket": "acento_ambar",
    "unidades": "acento_lima",
}


def _pastilla(tipo: str) -> str:
    """Color de fondo de la pastilla del indicador según el tema activo."""
    return color_tema(_PASTILLAS.get(tipo, "pastilla_neutra"))


def _acento(tipo: str) -> str:
    """Color de acento del indicador según el tema activo."""
    return color_tema(_ACENTOS.get(tipo, "verde"))


def _tintar(etiqueta, token: str) -> None:
    """Aplica a una etiqueta Fluent el color de un token de ui.fluent (claro y oscuro)."""
    etiqueta.setTextColor(
        QColor(CLARO.get(token, "#000000")),
        QColor(OSCURO.get(token, "#FFFFFF")),
    )


def estilo_dashboard() -> str:
    """Hoja de estilos del dashboard, adapted al tema activo."""
    return f"""
QFrame#filaActividad {{
    background: transparent;
    border-bottom: 1px solid {color('borde_suave')};
    padding: {_px(6)}px 0px;
}}
QFrame#filaActividad:hover {{
    background-color: {color('fondo_suave')};
    border-radius: {_px(6)}px;
}}
"""


class IconoPastel(QWidget):
    """Badge de 36x36 px con fondo pastel e icono vectorial nítido."""

    def __init__(self, tipo: str, color_icono: str | None = None, fondo: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.tipo = tipo
        self.color_icono = QColor(color_icono or _acento(tipo))
        self.color_fondo = QColor(fondo or _pastilla(tipo))
        self.setFixedSize(_px(36), _px(36))

    def set_colores(self, color_icono: str, fondo: str) -> None:
        """Cambia los colores del badge (se usa al cambiar de tema)."""
        self.color_icono = QColor(color_icono)
        self.color_fondo = QColor(fondo)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self.color_fondo))
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), _px(8), _px(8))

        p.setPen(QPen(self.color_icono, max(1.5, float(_px(2))), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        w = float(self.width())
        h = float(self.height())

        if self.tipo == "ventas":
            fuente_s = fuente(TAMANO_TITLE + 1, negrita=True)
            p.setFont(fuente_s)
            p.setPen(self.color_icono)
            p.drawText(QRectF(0, -1, w, h), Qt.AlignmentFlag.AlignCenter, "$")
        elif self.tipo == "pedidos":
            path = QPainterPath()
            path.moveTo(w * 0.28, h * 0.38)
            path.lineTo(w * 0.72, h * 0.38)
            path.lineTo(w * 0.68, h * 0.72)
            path.lineTo(w * 0.32, h * 0.72)
            path.closeSubpath()
            p.drawPath(path)
            p.drawArc(QRectF(w * 0.38, h * 0.24, w * 0.24, h * 0.28), 0, 180 * 16)
        elif self.tipo == "ticket":
            p.drawRoundedRect(QRectF(w * 0.28, h * 0.26, w * 0.44, h * 0.48), 2, 2)
            p.drawLine(QPointF(w * 0.36, h * 0.40), QPointF(w * 0.64, h * 0.40))
            p.drawLine(QPointF(w * 0.36, h * 0.52), QPointF(w * 0.54, h * 0.52))
        elif self.tipo == "unidades":
            outer = QPainterPath()
            outer.moveTo(w * 0.50, h * 0.24)
            outer.lineTo(w * 0.77, h * 0.38)
            outer.lineTo(w * 0.77, h * 0.64)
            outer.lineTo(w * 0.50, h * 0.78)
            outer.lineTo(w * 0.23, h * 0.64)
            outer.lineTo(w * 0.23, h * 0.38)
            outer.closeSubpath()
            p.drawPath(outer)
            p.drawLine(QPointF(w * 0.50, h * 0.51), QPointF(w * 0.50, h * 0.78))
            p.drawLine(QPointF(w * 0.50, h * 0.51), QPointF(w * 0.23, h * 0.38))
            p.drawLine(QPointF(w * 0.50, h * 0.51), QPointF(w * 0.77, h * 0.38))
        p.end()


class KPICard(CardWidget):
    """Tarjeta de métrica clave con icono, valor y tendencia."""

    def __init__(self, titulo: str, tipo_icono: str, color_acento: str, color_fondo: str, parent=None) -> None:
        super().__init__(parent)
        self.tipo_icono = tipo_icono
        self.setObjectName("tarjetaMetrica")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(_px(118))
        self.setBorderRadius(8)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(_px(12), _px(12), _px(12), _px(12))
        layout.setSpacing(_px(4))

        fila_sup = QHBoxLayout()
        fila_sup.setSpacing(_px(6))

        self.lbl_titulo = BodyLabel(titulo, self)
        self.lbl_titulo.setWordWrap(True)

        self.icono = IconoPastel(tipo_icono, color_acento, color_fondo, self)

        fila_sup.addWidget(self.lbl_titulo)
        fila_sup.addStretch()
        fila_sup.addWidget(self.icono)
        layout.addLayout(fila_sup)

        fila_inf = QHBoxLayout()
        fila_inf.setSpacing(_px(6))

        self.lbl_valor = StrongBodyLabel("--", self)

        self.badge_tendencia = QLabel("+0%", self)
        self.badge_tendencia.setFixedHeight(_px(22))
        self.badge_tendencia.hide()

        fila_inf.addWidget(self.lbl_valor)
        fila_inf.addWidget(self.badge_tendencia)
        fila_inf.addStretch()
        layout.addLayout(fila_inf)

        self._positivo = True
        self._tendencia = ""
        self._aplicar_estilos()

    def _aplicar_estilos(self) -> None:
        """Repinta la tarjeta con los colores del tema activo."""
        _tintar(self.lbl_titulo, "gris_medio")
        if self._tendencia:
            if self._positivo:
                fondo, texto, borde = (
                    color("pastilla_positiva"), color("exito"), color("borde"))
            else:
                fondo, texto, borde = (
                    color("pastilla_negativa"), color("error"), color("borde"))
            self.badge_tendencia.setStyleSheet(
                f"background-color: {fondo}; color: {texto}; font-size: {_px(11)}px; "
                f"font-weight: 700; border: 1px solid {borde}; border-radius: {_px(6)}px; "
                f"padding: {_px(2)}px {_px(6)}px;"
            )
        else:
            self.badge_tendencia.setStyleSheet(
                f"background-color: {color('pastilla_positiva')}; color: {color('exito')}; "
                f"font-size: {_px(11)}px; font-weight: 700; border: 1px solid {color('borde')}; "
                f"border-radius: {_px(6)}px; padding: {_px(2)}px {_px(6)}px;"
            )

    def set_colores(self, color_acento: str, color_fondo: str) -> None:
        """Actualiza los colores del icono (se usa al cambiar de tema)."""
        self.icono.set_colores(color_acento, color_fondo)

    def minimumSizeHint(self) -> QSize:
        return QSize(_px(150), _px(90))

    def set_datos(self, valor: str, tendencia: str = "", positiva: bool = True) -> None:
        self._valor_crudo = valor
        self._tendencia = tendencia
        self._positivo = positiva
        if "," in valor:
            entero, _, dec = valor.partition(",")
            txt_html = (
                f"<span style='font-size: {_px(25)}px; font-weight: 700; color: {color('texto')};'>{entero}</span>"
                f"<span style='font-size: {_px(16)}px; font-weight: 600; color: {color('gris_medio')};'>,{dec}</span>"
            )
        else:
            txt_html = f"<span style='font-size: {_px(25)}px; font-weight: 700; color: {color('texto')};'>{valor}</span>"
        self.lbl_valor.setText(txt_html)
        self.lbl_valor.adjustSize()
        self._aplicar_estilos()
        if tendencia:
            self.badge_tendencia.setText(tendencia)
            self.badge_tendencia.adjustSize()
            self.badge_tendencia.show()
        else:
            self.badge_tendencia.hide()


class GraficoTendenciaWidget(QWidget):
    """Gráfico vectorial interactivo con renderizado Qt antialiasing."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(_px(190))
        self._datos: list[tuple[str, float]] = []
        self._modo: str = "linea"
        self.setMouseTracking(True)

    def set_datos(self, datos: list[tuple[str, float]]) -> None:
        self._datos = datos
        self.update()

    def set_modo(self, modo: str) -> None:
        self._modo = modo
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())

        if not self._datos:
            p.setPen(QColor(color("gris_medio")))
            p.setFont(fuente(TAMANO_BODY))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin movimientos registrados en este período")
            p.end()
            return

        valores = [d[1] for d in self._datos]
        val_max = max(valores) if valores and max(valores) > 0 else 100.0

        fm_y = p.fontMetrics()
        txt_max = f"$ {int(val_max):_}".replace("_", ".")
        ancho_num = fm_y.horizontalAdvance(txt_max)
        pad_izq = max(float(_px(80)), float(ancho_num + _px(18)))
        pad_der = float(_px(25))
        pad_arr = float(_px(22))
        pad_abj = float(_px(36))

        ancho_util = max(10.0, w - pad_izq - pad_der)
        alto_util = max(10.0, h - pad_arr - pad_abj)

        lineas = 4
        alt_txt = float(_px(18))
        for i in range(lineas + 1):
            y = pad_arr + (alto_util * (i / lineas))
            val = val_max * (1.0 - (i / lineas))

            p.setPen(QPen(QColor(color("fondo_suave")), 1, Qt.PenStyle.SolidLine))
            p.drawLine(QPointF(pad_izq, y), QPointF(w - pad_der, y))

            p.setPen(QColor(color("gris_linea")))
            p.setFont(fuente(TAMANO_SMALL, tabular=True))
            p.drawText(
                QRectF(float(_px(2)), y - alt_txt / 2.0, pad_izq - float(_px(8)), alt_txt),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"$ {int(val):_}".replace("_", "."),
            )

        n = len(self._datos)
        if n == 0:
            p.end()
            return

        puntos: list[QPointF] = []
        paso_x = ancho_util / max(1, n - 1) if n > 1 else ancho_util / 2
        ancho_tag = float(_px(56))
        alt_tag = float(_px(18))

        for idx, (etiqueta, valor) in enumerate(self._datos):
            x = pad_izq + (idx * paso_x) if n > 1 else pad_izq + ancho_util / 2
            frac = valor / val_max if val_max > 0 else 0
            y = (pad_arr + alto_util) - (frac * alto_util)
            puntos.append(QPointF(x, y))

            if n <= 12 or idx % max(1, n // 7) == 0:
                p.setPen(QColor(color("gris_linea")))
                p.setFont(fuente(TAMANO_SMALL))
                p.drawText(
                    QRectF(x - ancho_tag / 2.0, h - pad_abj + float(_px(6)), ancho_tag, alt_tag),
                    Qt.AlignmentFlag.AlignCenter,
                    etiqueta,
                )

        if self._modo == "linea" and n > 1:
            path = QPainterPath()
            path.moveTo(puntos[0])
            for i in range(len(puntos) - 1):
                p1 = puntos[i]
                p2 = puntos[i + 1]
                dx = (p2.x() - p1.x()) * 0.5
                c1 = QPointF(p1.x() + dx, p1.y())
                c2 = QPointF(p2.x() - dx, p2.y())
                path.cubicTo(c1, c2, p2)

            area_path = QPainterPath(path)
            area_path.lineTo(puntos[-1].x(), pad_arr + alto_util)
            area_path.lineTo(puntos[0].x(), pad_arr + alto_util)
            area_path.closeSubpath()

            c_v = QColor(color("acento"))
            grad = QLinearGradient(0, pad_arr, 0, pad_arr + alto_util)
            grad.setColorAt(0.0, QColor(c_v.red(), c_v.green(), c_v.blue(), 55))
            grad.setColorAt(1.0, QColor(c_v.red(), c_v.green(), c_v.blue(), 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawPath(area_path)

            p.setPen(QPen(QColor(color("acento")), float(_px(2.5)), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

            p.setBrush(QBrush(QColor(color("fondo_tarjeta"))))
            p.setPen(QPen(QColor(color("acento")), float(_px(2))))
            radio_pt = float(_px(3.5))
            for pt in puntos:
                p.drawEllipse(pt, radio_pt, radio_pt)

        elif self._modo == "barras" or n == 1:
            ancho_barra = min(float(_px(36)), max(float(_px(12)), (ancho_util / n) * 0.55))
            for pt in puntos:
                x_b = pt.x() - (ancho_barra / 2.0)
                y_b = pt.y()
                h_b = (pad_arr + alto_util) - y_b
                rect_b = QRectF(x_b, y_b, ancho_barra, h_b)

                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(color("acento"))))
                p.drawRoundedRect(rect_b, float(_px(4)), float(_px(4)))
        p.end()


class PillGroup(SegmentedWidget):
    """Segmented Control (pill buttons) de opciones exclusivas."""

    cambio_seleccion = pyqtSignal(str)

    def __init__(self, opciones: list[tuple[str, str]], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pillGroupRango")
        self.hBoxLayout.setContentsMargins(_px(2), _px(2), _px(2), _px(2))
        self.hBoxLayout.setSpacing(_px(2))
        self._botones: dict[str, QPushButton] = {}
        self._clave_activa = opciones[0][0] if opciones else ""

        from PyQt6.QtGui import QFontMetrics
        fm_bold = QFontMetrics(fuente(TAMANO_BODY, negrita=True))
        for clave, texto in opciones:
            btn = self.addItem(clave, texto)
            btn.setStyleSheet(
                "SegmentedItem { padding: 4px 10px; margin: 0px; border-radius: 5px; border: none; }"
                "SegmentedItem:hover { font-weight: normal; }"
            )
            ancho_min = fm_bold.horizontalAdvance(texto) + _px(26)
            btn.setMinimumWidth(ancho_min)
            self._botones[clave] = btn

        self.currentItemChanged.connect(self._al_cambiar_item)
        if self._clave_activa:
            self.setCurrentItem(self._clave_activa)

    def paintEvent(self, e) -> None:
        QWidget.paintEvent(self, e)
        item = self.currentItem()
        if not item:
            return

        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )

        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255, 16))
            painter.setBrush(QColor(255, 255, 255, 22))
        else:
            painter.setPen(QColor(0, 0, 0, 18))
            painter.setBrush(QColor(255, 255, 255, 245))

        x = int(self.slideAni.value())
        rect = QRectF(x, 2, item.width(), self.height() - 4)
        painter.drawRoundedRect(rect, 5, 5)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(themeColor())
        ind_w = 16
        ind_x = x + (item.width() - ind_w) / 2
        ind_y = self.height() - 5.5
        painter.drawRoundedRect(QRectF(ind_x, ind_y, ind_w, 2.5), 1.25, 1.25)

    def _al_cambiar_item(self, clave: str) -> None:
        self._clave_activa = clave
        self.cambio_seleccion.emit(clave)

    def seleccionar(self, clave: str) -> None:
        if clave not in self._botones:
            return
        self.setCurrentItem(clave)


class FilaActividad(QFrame):
    """Fila con título, detalle, importe e insignia de una lista de actividad."""

    def __init__(
        self,
        titulo: str,
        subtitulo: str = "",
        derecha: str = "",
        color_derecha: str | None = None,
        badge: str = "",
        badge_bg: str | None = None,
        badge_fg: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        col_der = color_derecha or color("texto")
        bg_b = badge_bg or color("fondo_suave")
        fg_b = badge_fg or color("gris_linea")
        self.setObjectName("filaActividad")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(_px(6), _px(4), _px(6), _px(4))
        lay.setSpacing(_px(8))

        col_izq = QVBoxLayout()
        col_izq.setContentsMargins(0, 0, 0, 0)
        col_izq.setSpacing(_px(2))

        lbl_tit = StrongBodyLabel(titulo, self)
        _tintar(lbl_tit, "texto")
        col_izq.addWidget(lbl_tit)

        if subtitulo:
            lbl_sub = CaptionLabel(subtitulo, self)
            _tintar(lbl_sub, "gris_medio")
            col_izq.addWidget(lbl_sub)

        lay.addLayout(col_izq, 1)

        if derecha:
            lbl_der = QLabel(derecha, self)
            lbl_der.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
            lbl_der.setStyleSheet(f"color: {col_der}; background: transparent; border: none;")
            lbl_der.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lay.addWidget(lbl_der)

        if badge:
            lbl_badge = QLabel(badge, self)
            lbl_badge.setFont(fuente(TAMANO_SMALL, negrita=True))
            lbl_badge.setStyleSheet(
                f"background-color: {bg_b}; color: {fg_b}; "
                f"border-radius: {_px(6)}px; padding: {_px(2)}px {_px(6)}px; border: none;"
            )
            lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(lbl_badge)


class ListaActividadWidget(QWidget):
    """Lista de filas de actividad con estado vacío."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(_px(2))
        self._filas: list[QWidget] = []
        self._lbl_vacio = QLabel(self)
        self._lbl_vacio.setFont(fuente(TAMANO_SMALL))
        self._lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lay.addWidget(self._lbl_vacio)
        self._lbl_vacio.hide()
        self._aplicar_estilos()

    def _aplicar_estilos(self) -> None:
        """Repinta el mensaje de lista vacía con los colores del tema activo."""
        self._lbl_vacio.setStyleSheet(
            f"color: {color('gris_apagado')}; padding: {_px(14)}px 0px; background: transparent;"
        )

    def limpiar(self) -> None:
        for fila in self._filas:
            self._lay.removeWidget(fila)
            fila.deleteLater()
        self._filas.clear()
        self._lbl_vacio.hide()

    def mostrar_vacio(self, texto: str) -> None:
        self.limpiar()
        self._lbl_vacio.setText(texto)
        self._lbl_vacio.show()

    def agregar_fila(
        self,
        titulo: str,
        subtitulo: str = "",
        derecha: str = "",
        color_derecha: str | None = None,
        badge: str = "",
        badge_bg: str | None = None,
        badge_fg: str | None = None,
    ) -> None:
        self._lbl_vacio.hide()
        fila = FilaActividad(
            titulo,
            subtitulo,
            derecha,
            color_derecha or color("texto"),
            badge,
            badge_bg or color("fondo_suave"),
            badge_fg or color("gris_linea"),
            self,
        )
        self._filas.append(fila)
        self._lay.addWidget(fila)


class CargaDashboardSignals(QObject):
    datos_listos = pyqtSignal(dict)


class WorkerCargaDashboard(QRunnable):
    def __init__(
        self,
        id_carga: int,
        periodo: str,
        estadisticas: EstadisticasVentas | None,
        gestor_stock: GestorStock | None,
        fiado: GestorFiado | None,
    ) -> None:
        super().__init__()
        self.id_carga = id_carga
        self.periodo = periodo
        self._estadisticas = estadisticas
        self._gestor_stock = gestor_stock
        self._fiado = fiado
        self.signals = CargaDashboardSignals()

    def run(self) -> None:
        hoy = date.today()
        if self.periodo == "hoy":
            desde, hasta = EstadisticasVentas.del_dia(hoy)
            dias_atras = 1
        elif self.periodo == "mes_actual":
            desde, hasta = EstadisticasVentas.del_mes(hoy.year, hoy.month)
            dias_atras = (hasta - desde).days + 1
        elif self.periodo == "mes_anterior":
            mes, anio = (hoy.month - 1 or 12, hoy.year - 1 if hoy.month == 1 else hoy.year)
            desde, hasta = EstadisticasVentas.del_mes(anio, mes)
            dias_atras = (hasta - desde).days + 1
        elif self.periodo == "30d":
            desde, hasta = EstadisticasVentas.ultimos_dias(30, hoy)
            dias_atras = 30
        else:
            desde, hasta = EstadisticasVentas.ultimos_dias(365, hoy)
            dias_atras = 365

        total_ventas = 0.0
        cant_pedidos = 0
        ticket_promedio = 0.0
        unidades_vendidas = 0.0
        var_ventas_txt = ""
        var_ventas_pos = True
        var_pedidos_txt = ""
        var_pedidos_pos = True
        var_ticket_txt = ""
        var_ticket_pos = True
        var_unidades_txt = ""
        var_unidades_pos = True

        if self._estadisticas:
            try:
                res = self._estadisticas.resumen(desde, hasta)
                total_ventas = float(res.total)
                cant_pedidos = int(res.cantidad_ventas)
                ticket_promedio = float(res.ticket_promedio)
                unidades_vendidas = float(res.unidades)
            except Exception:
                pass

        puntos_grafico: list[tuple[str, float]] = []
        if self._estadisticas:
            try:
                if self.periodo == "12m":
                    meses_abr = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    anio_cur, mes_cur = hoy.year, hoy.month
                    m_ini = mes_cur - 11
                    a_ini = anio_cur
                    while m_ini <= 0:
                        m_ini += 12
                        a_ini -= 1
                    inicio = date(a_ini, m_ini, 1)

                    por_mes: dict[tuple[int, int], float] = {}
                    for dia, total in self._estadisticas.total_por_dia(inicio, hoy):
                        clave = (dia.year, dia.month)
                        por_mes[clave] = por_mes.get(clave, 0.0) + float(total)

                    puntos_mes: list[tuple[str, float]] = []
                    for offset in range(11, -1, -1):
                        m = mes_cur - offset
                        a = anio_cur
                        while m <= 0:
                            m += 12
                            a -= 1
                        tag = f"{meses_abr[m]} '{str(a)[2:]}" if anio_cur != a else meses_abr[m]
                        puntos_mes.append((tag, float(por_mes.get((a, m), 0.0))))
                    puntos_grafico = puntos_mes
                else:
                    totales_dia = self._estadisticas.total_por_dia(desde, hasta)
                    for dia, total in totales_dia:
                        puntos_grafico.append((dia.strftime("%d/%m"), float(total)))
            except Exception:
                pass

        if not puntos_grafico:
            if self.periodo == "12m":
                meses_abr = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                anio_cur, mes_cur = hoy.year, hoy.month
                for offset in range(11, -1, -1):
                    m = mes_cur - offset
                    a = anio_cur
                    while m <= 0:
                        m += 12
                        a -= 1
                    tag = f"{meses_abr[m]} '{str(a)[2:]}" if anio_cur != a else meses_abr[m]
                    puntos_grafico.append((tag, 0.0))
            else:
                for i in range(min(7, dias_atras)):
                    d = hoy - timedelta(days=(min(7, dias_atras) - 1 - i))
                    puntos_grafico.append((d.strftime("%d/%m"), 0.0))

        filas_ventas: list[dict[str, Any]] = []
        if self._estadisticas:
            try:
                ventas = self._estadisticas.ventas_del_periodo(desde, hasta)
                if ventas:
                    ventas_recientes = list(reversed(ventas))[:4]
                    for idx, v in enumerate(ventas_recientes):
                        num_id = getattr(v, "id", None)
                        id_txt = f"Venta #{num_id}" if num_id is not None else f"Venta {idx + 1}"
                        fecha_str = v.fecha.strftime("%d/%m")
                        hora_str = str(v.hora)[:5] if v.hora else ""
                        metodo = str(v.medio_pago or "Efectivo")
                        sub = f"{fecha_str} {hora_str} · {metodo}".strip()
                        filas_ventas.append({
                            "titulo": id_txt,
                            "subtitulo": sub,
                            "derecha": formatear_dinero(v.total),
                        })
            except Exception:
                pass

        filas_top: list[dict[str, Any]] = []
        if self._estadisticas:
            try:
                top = self._estadisticas.mas_vendidos(desde, hasta, limite=4)
                if top:
                    for item in top:
                        sub = f"Cód. {item.codigo} · {formatear_cantidad(item.unidades)} un."
                        filas_top.append({
                            "titulo": str(item.nombre),
                            "subtitulo": sub,
                            "derecha": formatear_dinero(item.total),
                        })
            except Exception:
                pass

        filas_alertas: list[dict[str, Any]] = []
        if self._gestor_stock:
            try:
                productos = self._gestor_stock.productos_criticos()[:4]
                if productos:
                    for p in productos:
                        sub = f"Cód. {p.codigo} · Mínimo: {formatear_cantidad(p.stock_minimo)}"
                        es_cero = p.stock_actual <= 0
                        filas_alertas.append({
                            "titulo": str(p.nombre),
                            "subtitulo": sub,
                            "derecha": f"{formatear_cantidad(p.stock_actual)} un.",
                            "es_cero": es_cero,
                        })
            except Exception:
                pass

        filas_clientes: list[dict[str, Any]] = []
        if self._fiado:
            try:
                deudores = self._fiado.deudores()[:4]
                if deudores:
                    for c, saldo in deudores:
                        sub = f"Tel: {c.telefono}" if c.telefono else "Cliente registrado"
                        filas_clientes.append({
                            "titulo": str(c.nombre),
                            "subtitulo": sub,
                            "derecha": formatear_dinero(saldo),
                        })
            except Exception:
                pass

        datos = {
            "id_carga": self.id_carga,
            "total_ventas": total_ventas,
            "cant_pedidos": cant_pedidos,
            "ticket_promedio": ticket_promedio,
            "unidades_vendidas": unidades_vendidas,
            "var_ventas_txt": var_ventas_txt,
            "var_ventas_pos": var_ventas_pos,
            "var_pedidos_txt": var_pedidos_txt,
            "var_pedidos_pos": var_pedidos_pos,
            "var_ticket_txt": var_ticket_txt,
            "var_ticket_pos": var_ticket_pos,
            "var_unidades_txt": var_unidades_txt,
            "var_unidades_pos": var_unidades_pos,
            "puntos_grafico": puntos_grafico,
            "filas_ventas": filas_ventas,
            "filas_top": filas_top,
            "filas_alertas": filas_alertas,
            "filas_clientes": filas_clientes,
        }
        try:
            self.signals.datos_listos.emit(datos)
        except RuntimeError:
            pass


class DashboardPrincipalWidget(QWidget):
    """Vista principal con métricas clave, gráfico interactivo y listas de actividad."""

    solicitar_ver_ventas = pyqtSignal()
    solicitar_ver_ranking = pyqtSignal()

    def __init__(
        self,
        gestor_stock: GestorStock,
        estadisticas: EstadisticasVentas,
        fiado: GestorFiado | None = None,
        usuario: str = "Admin",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._gestor_stock = gestor_stock
        self._estadisticas = estadisticas
        self._fiado = fiado
        self._usuario = usuario
        self._periodo_actual = "30d"
        self._id_carga = 0
        self._worker_actual: WorkerCargaDashboard | None = None
        self._ultimos_datos: dict[str, Any] | None = None

        self._construir_ui()
        conectar_tema(self._aplicar_temas)
        self.recargar_datos()

    def _construir_ui(self) -> None:
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)

        scroll = ScrollArea(self)
        scroll.setObjectName("scrollDashboard")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea#scrollDashboard { background: transparent; border: none; }"
        )
        scroll.viewport().setAutoFillBackground(False)

        contenedor = QWidget()
        contenedor.setObjectName("contenidoDashboard")
        layout_cont = QVBoxLayout(contenedor)
        layout_cont.setContentsMargins(_px(20), _px(16), _px(20), _px(20))
        layout_cont.setSpacing(_px(14))

        col_header = QVBoxLayout()
        col_header.setSpacing(_px(6))

        fila_sup_header = QHBoxLayout()
        fila_sup_header.setSpacing(_px(10))

        hora = datetime.datetime.now().hour
        if 6 <= hora < 13:
            saludo = "Buen día"
        elif 13 <= hora < 20:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"

        self.lbl_saludo = TitleLabel(f"{saludo}, {self._usuario.capitalize()}", self)
        self.lbl_saludo.setFont(
            fuente(TAMANO_TITLE if escala() == ESCALA_NORMAL else TAMANO_SUBTITLE, negrita=True)
        )
        _tintar(self.lbl_saludo, "texto")
        fila_sup_header.addWidget(self.lbl_saludo)

        fila_sup_header.addStretch()

        self.lbl_logo = QLabel()
        ruta_logo = RECURSOS_DIR / "logo_u.png"
        if not ruta_logo.is_file():
            ruta_logo = RECURSOS_DIR / "logo_sf_crop.png"
        pix_logo = QPixmap(str(ruta_logo))
        if not pix_logo.isNull():
            alto_logo = _px(38)
            self.lbl_logo.setPixmap(
                pix_logo.scaledToHeight(
                    alto_logo,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        fila_sup_header.addWidget(self.lbl_logo)

        col_header.addLayout(fila_sup_header)

        fila_pill = QHBoxLayout()
        fila_pill.setSpacing(_px(8))

        self.pill_rango = PillGroup([
            ("hoy", "Hoy"),
            ("mes_actual", "Mes actual"),
            ("mes_anterior", "Mes anterior"),
            ("30d", "Últimos 30 días"),
            ("12m", "Últimos 12 meses"),
        ])
        self.pill_rango.seleccionar("30d")
        self.pill_rango.cambio_seleccion.connect(self._al_cambiar_periodo)
        fila_pill.addWidget(self.pill_rango)
        fila_pill.addStretch()

        col_header.addLayout(fila_pill)

        self.lbl_nota_plan = CaptionLabel(
            "Gratis: 12 meses de estadísticas. Con el plan Mensual ves todo el historial.", self)
        col_header.addWidget(self.lbl_nota_plan)

        layout_cont.addLayout(col_header)

        grid_kpi = QGridLayout()
        grid_kpi.setHorizontalSpacing(_px(14))
        grid_kpi.setVerticalSpacing(_px(14))

        self.kpi_ventas = KPICard("Ventas del período", "ventas", _acento("ventas"), _pastilla("ventas"))
        self.kpi_pedidos = KPICard("Ventas realizadas", "pedidos", _acento("pedidos"), _pastilla("pedidos"))
        self.kpi_ticket = KPICard("Ticket promedio", "ticket", _acento("ticket"), _pastilla("ticket"))
        self.kpi_unidades = KPICard("Unidades vendidas", "unidades", _acento("unidades"), _pastilla("unidades"))

        self._kpis = (
            (self.kpi_ventas, "ventas"),
            (self.kpi_pedidos, "pedidos"),
            (self.kpi_ticket, "ticket"),
            (self.kpi_unidades, "unidades"),
        )

        grid_kpi.addWidget(self.kpi_ventas, 0, 0)
        grid_kpi.addWidget(self.kpi_pedidos, 0, 1)
        grid_kpi.addWidget(self.kpi_ticket, 0, 2)
        grid_kpi.addWidget(self.kpi_unidades, 0, 3)
        layout_cont.addLayout(grid_kpi)

        tarjeta_grafico = CardWidget()
        tarjeta_grafico.setObjectName("tarjetaGrafico")
        tarjeta_grafico.setBorderRadius(8)

        lay_grafico = QVBoxLayout(tarjeta_grafico)
        lay_grafico.setContentsMargins(_px(16), _px(12), _px(16), _px(12))
        lay_grafico.setSpacing(_px(10))

        header_graf = QHBoxLayout()
        header_graf.setSpacing(_px(8))

        lbl_tit_graf = SubtitleLabel("Tendencia de ingresos", tarjeta_grafico)
        _tintar(lbl_tit_graf, "texto")
        header_graf.addWidget(lbl_tit_graf)
        header_graf.addStretch()

        self.pill_tipo_graf = PillGroup([("linea", "Línea"), ("barras", "Barras")])
        self.pill_tipo_graf.cambio_seleccion.connect(self._al_cambiar_modo_grafico)
        header_graf.addWidget(self.pill_tipo_graf)
        lay_grafico.addLayout(header_graf)

        self.grafico_tendencia = GraficoTendenciaWidget(tarjeta_grafico)
        lay_grafico.addWidget(self.grafico_tendencia)
        layout_cont.addWidget(tarjeta_grafico)

        self.tablaVentas = ListaActividadWidget()
        self.tablaTop = ListaActividadWidget()
        self.tablaAlertas = ListaActividadWidget()
        self.tablaClientes = ListaActividadWidget()

        grid_actividad = QGridLayout()
        grid_actividad.setSpacing(_px(14))
        grid_actividad.addWidget(
            self._crear_tarjeta_actividad(
                "Últimas ventas", self.tablaVentas, self.solicitar_ver_ventas.emit
            ),
            0,
            0,
        )
        grid_actividad.addWidget(
            self._crear_tarjeta_actividad(
                "Top productos", self.tablaTop, self.solicitar_ver_ranking.emit
            ),
            0,
            1,
        )
        grid_actividad.addWidget(self._crear_tarjeta_actividad("Alertas de stock", self.tablaAlertas), 1, 0)
        grid_actividad.addWidget(self._crear_tarjeta_actividad("Clientes con saldo", self.tablaClientes), 1, 1)

        layout_cont.addLayout(grid_actividad)

        layout_cont.addStretch()
        scroll.setWidget(contenedor)
        contenedor.setAutoFillBackground(False)
        layout_raiz.addWidget(scroll)

    def _crear_tarjeta_actividad(
        self,
        titulo: str,
        widget_lista: QWidget,
        on_ver_mas=None,
    ) -> QFrame:
        tarjeta = CardWidget()
        tarjeta.setObjectName("tarjetaActividad")
        tarjeta.setBorderRadius(8)

        lay = QVBoxLayout(tarjeta)
        lay.setContentsMargins(_px(14), _px(12), _px(14), _px(12))
        lay.setSpacing(_px(8))

        fila_header = QHBoxLayout()
        fila_header.setContentsMargins(0, 0, 0, 0)

        lbl_tit = StrongBodyLabel(titulo, tarjeta)
        lbl_tit.setMinimumWidth(_px(130))
        _tintar(lbl_tit, "texto")
        fila_header.addWidget(lbl_tit)
        fila_header.addStretch()

        if on_ver_mas is not None:
            btn_ver = TransparentPushButton("Ver más ↗", tarjeta)
            btn_ver.setFixedHeight(_px(26))
            btn_ver.clicked.connect(on_ver_mas)
            fila_header.addWidget(btn_ver)

        lay.addLayout(fila_header)
        lay.addWidget(widget_lista)
        lay.addStretch()
        return tarjeta

    def _aplicar_temas(self) -> None:
        """Repinta el dashboard con los colores del tema activo."""
        if sip.isdeleted(self):
            return
        try:
            # El hover de filaActividad usa _px() (escala propia del dashboard)
            # y tokens por tema; la hoja maestra no interpola píxeles escalados,
            # así que este QSS chico sigue viviendo en el widget.
            self.setStyleSheet(estilo_dashboard())
            self.lbl_nota_plan.setStyleSheet(f"color: {color('alerta')};")
            for tarjeta, tipo in self._kpis:
                tarjeta.set_colores(_acento(tipo), _pastilla(tipo))
                tarjeta._aplicar_estilos()
            for lista in (self.tablaVentas, self.tablaTop, self.tablaAlertas, self.tablaClientes):
                lista._aplicar_estilos()
            if self._ultimos_datos is not None:
                self._aplicar_datos_dashboard(self._ultimos_datos)
            self.grafico_tendencia.update()
        except RuntimeError:
            pass

    def _al_cambiar_periodo(self, clave: str) -> None:
        self._periodo_actual = clave
        self.recargar_datos()

    def _al_cambiar_modo_grafico(self, modo: str) -> None:
        self.grafico_tendencia.set_modo(modo)

    def al_mostrar(self) -> None:
        self.recargar_datos()

    def recargar_datos(self) -> None:
        self._id_carga += 1
        worker = WorkerCargaDashboard(
            self._id_carga,
            self._periodo_actual,
            self._estadisticas,
            self._gestor_stock,
            self._fiado,
        )
        worker.signals.datos_listos.connect(self._aplicar_datos_dashboard)
        self._worker_actual = worker
        QThreadPool.globalInstance().start(worker)

    def _aplicar_datos_dashboard(self, datos: dict[str, Any]) -> None:
        if datos.get("id_carga") != self._id_carga:
            return
        self._ultimos_datos = datos

        self.kpi_ventas.set_datos(
            formatear_dinero(datos["total_ventas"]),
            datos["var_ventas_txt"],
            datos["var_ventas_pos"],
        )
        self.kpi_pedidos.set_datos(
            str(datos["cant_pedidos"]),
            datos["var_pedidos_txt"],
            datos["var_pedidos_pos"],
        )
        self.kpi_ticket.set_datos(
            formatear_dinero(datos["ticket_promedio"]),
            datos["var_ticket_txt"],
            datos["var_ticket_pos"],
        )
        self.kpi_unidades.set_datos(
            formatear_cantidad(datos["unidades_vendidas"]),
            datos["var_unidades_txt"],
            datos["var_unidades_pos"],
        )
        self.grafico_tendencia.set_datos(datos["puntos_grafico"])

        self._cargar_tabla_ventas(datos["filas_ventas"])
        self._cargar_tabla_top_productos(datos["filas_top"])
        self._cargar_tabla_alertas(datos["filas_alertas"])
        self._cargar_tabla_clientes(datos["filas_clientes"])

    def _cargar_tabla_ventas(self, filas: list[dict[str, Any]] | None = None) -> None:
        self.tablaVentas.limpiar()
        items = filas if filas is not None else []
        if not items:
            self.tablaVentas.mostrar_vacio(
                "Sin ventas en este período" if self._estadisticas else "Sin ventas registradas"
            )
            return
        for v in items:
            self.tablaVentas.agregar_fila(
                titulo=v["titulo"],
                subtitulo=v["subtitulo"],
                derecha=v["derecha"],
                color_derecha=color("exito"),
            )

    def _cargar_tabla_top_productos(self, filas: list[dict[str, Any]] | None = None) -> None:
        self.tablaTop.limpiar()
        items = filas if filas is not None else []
        if not items:
            self.tablaTop.mostrar_vacio(
                "Sin productos en este período" if self._estadisticas else "Sin productos vendidos"
            )
            return
        for item in items:
            self.tablaTop.agregar_fila(
                titulo=item["titulo"],
                subtitulo=item["subtitulo"],
                derecha=item["derecha"],
                color_derecha=color("texto"),
            )

    def _cargar_tabla_clientes(self, filas: list[dict[str, Any]] | None = None) -> None:
        self.tablaClientes.limpiar()
        items = filas if filas is not None else []
        if not items:
            self.tablaClientes.mostrar_vacio(
                "No hay clientes con saldo pendiente" if self._fiado else "Sin saldo pendiente"
            )
            return
        for c in items:
            self.tablaClientes.agregar_fila(
                titulo=c["titulo"],
                subtitulo=c["subtitulo"],
                derecha=c["derecha"],
                color_derecha=color("error"),
            )

    def _cargar_tabla_alertas(self, filas: list[dict[str, Any]] | None = None) -> None:
        self.tablaAlertas.limpiar()
        items = filas if filas is not None else []
        if not items:
            self.tablaAlertas.mostrar_vacio(
                "No hay productos con stock crítico" if self._gestor_stock else "Stock bajo control"
            )
            return
        for p in items:
            self.tablaAlertas.agregar_fila(
                titulo=p["titulo"],
                subtitulo=p["subtitulo"],
                derecha=p["derecha"],
                color_derecha=color("error") if p.get("es_cero") else color("alerta"),
            )
