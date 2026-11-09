from __future__ import annotations

import datetime
from datetime import date, timedelta
from typing import Any

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
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config import RECURSOS_DIR
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from ui.estilos import (
    ESCALA_NORMAL,
    TAMANO_BODY,
    TAMANO_MICRO,
    TAMANO_SMALL,
    TAMANO_SUBTITLE,
    TAMANO_TITLE,
    escala,
    fuente,
)
from ui.tema import color
from utils.formato import formatear_cantidad, formatear_dinero

def _px(valor: int) -> int:
    return round(valor * escala())


def estilo_dashboard() -> str:
    return f"""
* {{
    font-family: "Inter", sans-serif;
}}
QScrollArea#scrollDashboard {{
    background-color: {color('blanco')};
    border: none;
}}
QScrollArea#scrollDashboard QScrollBar:vertical {{
    width: {_px(8)}px;
    background: transparent;
    margin: {_px(4)}px {_px(2)}px;
}}
QScrollArea#scrollDashboard QScrollBar::handle:vertical {{
    background-color: {color('borde_destacado')};
    border-radius: {_px(4)}px;
    min-height: {_px(40)}px;
}}
QScrollArea#scrollDashboard QScrollBar::handle:vertical:hover {{
    background-color: {color('gris_apagado')};
}}
QScrollArea#scrollDashboard QScrollBar::add-line:vertical,
QScrollArea#scrollDashboard QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QWidget#contenidoDashboard {{
    background-color: {color('blanco')};
}}

QFrame#tarjetaMetrica, QFrame#tarjetaGrafico, QFrame#tarjetaActividad {{
    background-color: {color('blanco')};
    border: 1px solid {color('borde_suave')};
    border-radius: {_px(10)}px;
}}

QFrame#pillGroupRango {{
    background-color: {color('fondo_insignia')};
    border: 1px solid {color('borde_suave')};
    border-radius: {_px(8)}px;
    padding: {_px(2)}px;
}}
QPushButton#btnPillRango {{
    background-color: transparent;
    border: none;
    border-radius: {_px(6)}px;
    color: {color('gris_medio')};
    font-size: {_px(11)}px;
    font-weight: 500;
    padding: {_px(4)}px {_px(8)}px;
}}
QPushButton#btnPillRango:hover {{
    color: {color('texto_oscuro')};
}}
QPushButton#btnPillRango[seleccionado="true"] {{
    background-color: {color('blanco')};
    color: {color('verde_profundo')};
    font-weight: 700;
    border: 1px solid {color('borde_destacado')};
}}

"""


class IconoPastel(QWidget):
    """Badge de 36x36 px con fondo pastel e icono vectorial nítido."""

    def __init__(self, tipo: str, color_icono: str | None = None, fondo: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.tipo = tipo
        self.color_icono = QColor(color_icono or color("verde_acento"))
        self.color_fondo = QColor(fondo or color("pastilla_positiva"))
        self.setFixedSize(_px(36), _px(36))

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


class KPICard(QFrame):
    """Tarjeta de métrica clave moderna con borde sutil, icono y tendencia."""

    def __init__(self, titulo: str, tipo_icono: str, color_acento: str, color_fondo: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("tarjetaMetrica")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(_px(112))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(_px(12), _px(12), _px(12), _px(12))
        layout.setSpacing(_px(4))

        fila_sup = QHBoxLayout()
        fila_sup.setSpacing(_px(6))

        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setWordWrap(True)
        self.lbl_titulo.setStyleSheet(f"color: {color('gris_medio')}; font-size: {_px(11)}px; font-weight: 600;")

        self.icono = IconoPastel(tipo_icono, color_acento, color_fondo, self)

        fila_sup.addWidget(self.lbl_titulo)
        fila_sup.addStretch()
        fila_sup.addWidget(self.icono)
        layout.addLayout(fila_sup)

        fila_inf = QHBoxLayout()
        fila_inf.setSpacing(_px(6))

        self.lbl_valor = QLabel("--")
        self.lbl_valor.setFont(fuente(TAMANO_SUBTITLE, negrita=True, tabular=True))
        self.lbl_valor.setStyleSheet(f"color: {color('texto_oscuro')}; background: transparent;")

        self.badge_tendencia = QLabel("+0%")
        self.badge_tendencia.setStyleSheet(
            f"background-color: {color('pastilla_positiva')}; color: {color('verde_acento')}; font-size: {_px(11)}px; "
            f"font-weight: 700; border: 1px solid {color('borde_positivo')}; border-radius: {_px(6)}px; padding: {_px(2)}px {_px(6)}px;"
        )
        self.badge_tendencia.setFixedHeight(_px(22))

        fila_inf.addWidget(self.lbl_valor)
        fila_inf.addWidget(self.badge_tendencia)
        fila_inf.addStretch()
        layout.addLayout(fila_inf)

    def minimumSizeHint(self) -> QSize:
        return QSize(_px(150), _px(90))

    def set_datos(self, valor: str, tendencia: str = "", positiva: bool = True) -> None:
        self._valor_crudo = valor
        if "," in valor:
            entero, _, dec = valor.partition(",")
            txt_html = (
                f"<span style='font-size: {_px(22)}px; font-weight: 700; color: {color('texto_oscuro')};'>{entero}</span>"
                f"<span style='font-size: {_px(14)}px; font-weight: 600; color: {color('gris_medio')};'>,{dec}</span>"
            )
        else:
            txt_html = f"<span style='font-size: {_px(22)}px; font-weight: 700; color: {color('texto_oscuro')};'>{valor}</span>"
        self.lbl_valor.setText(txt_html)
        self.lbl_valor.adjustSize()
        if tendencia:
            self.badge_tendencia.setText(tendencia)
            self.badge_tendencia.adjustSize()
            if positiva:
                self.badge_tendencia.setStyleSheet(
                    f"background-color: {color('pastilla_positiva')}; color: {color('verde_acento')}; font-size: {_px(11)}px; "
                    f"font-weight: 700; border: 1px solid {color('borde_positivo')}; border-radius: {_px(6)}px; padding: {_px(2)}px {_px(6)}px;"
                )
            else:
                self.badge_tendencia.setStyleSheet(
                    f"background-color: {color('pastilla_negativa')}; color: {color('rojo_oscuro')}; font-size: {_px(11)}px; "
                    f"font-weight: 700; border: 1px solid {color('borde_negativo')}; border-radius: {_px(6)}px; padding: {_px(2)}px {_px(6)}px;"
                )
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
        pad_izq = float(_px(68))
        pad_der = float(_px(25))
        pad_arr = float(_px(22))
        pad_abj = float(_px(36))

        ancho_util = max(10.0, w - pad_izq - pad_der)
        alto_util = max(10.0, h - pad_arr - pad_abj)

        if not self._datos:
            p.setPen(QColor(color("gris_medio")))
            p.setFont(fuente(TAMANO_BODY))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin movimientos registrados en este período")
            p.end()
            return

        valores = [d[1] for d in self._datos]
        val_max = max(valores) if valores and max(valores) > 0 else 100.0

        lineas = 4
        alt_txt = float(_px(18))
        for i in range(lineas + 1):
            y = pad_arr + (alto_util * (i / lineas))
            val = val_max * (1.0 - (i / lineas))

            p.setPen(QPen(QColor(color("fondo_insignia")), 1, Qt.PenStyle.SolidLine))
            p.drawLine(QPointF(pad_izq, y), QPointF(w - pad_der, y))

            p.setPen(QColor(color("gris_linea")))
            p.setFont(fuente(TAMANO_SMALL, tabular=True))
            p.drawText(
                QRectF(0, y - alt_txt / 2.0, pad_izq - float(_px(8)), alt_txt),
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

            if n <= 10 or idx % max(1, n // 7) == 0:
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

            c_v = QColor(color("verde_grafico"))
            grad = QLinearGradient(0, pad_arr, 0, pad_arr + alto_util)
            grad.setColorAt(0.0, QColor(c_v.red(), c_v.green(), c_v.blue(), 55))
            grad.setColorAt(1.0, QColor(c_v.red(), c_v.green(), c_v.blue(), 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawPath(area_path)

            p.setPen(QPen(QColor(color("verde_grafico")), float(_px(2.5)), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

            p.setBrush(QBrush(QColor(color("blanco"))))
            p.setPen(QPen(QColor(color("verde_grafico")), float(_px(2))))
            radio_pt = float(_px(3.5))
            for pt in puntos:
                p.drawEllipse(pt, radio_pt, radio_pt)

        elif self._modo == "barras" or n == 1:
            ancho_barra = min(float(_px(36)), max(float(_px(12)), (ancho_util / n) * 0.55))
            for idx, pt in enumerate(puntos):
                x_b = pt.x() - (ancho_barra / 2.0)
                y_b = pt.y()
                h_b = (pad_arr + alto_util) - y_b
                rect_b = QRectF(x_b, y_b, ancho_barra, h_b)

                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(color("verde_grafico"))))
                p.drawRoundedRect(rect_b, float(_px(4)), float(_px(4)))

                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(color("verde_grafico"))))
                p.drawRoundedRect(rect_b, 4, 4)

        p.end()


class PillGroup(QFrame):
    """Segmented Control (pill buttons) de opciones exclusivas."""

    cambio_seleccion = pyqtSignal(str)

    def __init__(self, opciones: list[tuple[str, str]], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pillGroupRango")
        self._botones: dict[str, QPushButton] = {}
        self._clave_activa = opciones[0][0] if opciones else ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        for clave, texto in opciones:
            btn = QPushButton(texto, self)
            btn.setObjectName("btnPillRango")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("seleccionado", "true" if clave == self._clave_activa else "false")
            btn.clicked.connect(lambda _, c=clave: self.seleccionar(c))
            layout.addWidget(btn)
            self._botones[clave] = btn

    def seleccionar(self, clave: str) -> None:
        if clave not in self._botones or clave == self._clave_activa:
            return
        self._clave_activa = clave
        for c, btn in self._botones.items():
            btn.setProperty("seleccionado", "true" if c == clave else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.cambio_seleccion.emit(clave)


class FilaActividad(QFrame):
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
        col_der = color_derecha or color("texto_oscuro")
        bg_b = badge_bg or color("fondo_insignia")
        fg_b = badge_fg or color("gris_linea")
        self.setObjectName("filaActividad")
        self.setStyleSheet(
            "QFrame#filaActividad { "
            "background: transparent; "
            f"border-bottom: 1px solid {color('fondo_insignia')}; "
            f"padding: {_px(6)}px 0px; "
            "} "
            "QFrame#filaActividad:hover { "
            f"background-color: {color('fondo_suave')}; "
            f"border-radius: {_px(6)}px; "
            "}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(_px(6), _px(4), _px(6), _px(4))
        lay.setSpacing(_px(8))

        col_izq = QVBoxLayout()
        col_izq.setContentsMargins(0, 0, 0, 0)
        col_izq.setSpacing(_px(2))

        lbl_tit = QLabel(titulo, self)
        lbl_tit.setFont(fuente(TAMANO_BODY, negrita=True))
        lbl_tit.setStyleSheet(f"color: {color('texto_oscuro')}; background: transparent; border: none;")
        col_izq.addWidget(lbl_tit)

        if subtitulo:
            lbl_sub = QLabel(subtitulo, self)
            lbl_sub.setFont(fuente(TAMANO_SMALL))
            lbl_sub.setStyleSheet(f"color: {color('gris_medio')}; background: transparent; border: none;")
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
            lbl_badge.setFont(fuente(TAMANO_MICRO, negrita=True))
            lbl_badge.setStyleSheet(
                f"background-color: {bg_b}; color: {fg_b}; "
                f"border-radius: {_px(6)}px; padding: {_px(2)}px {_px(6)}px; border: none;"
            )
            lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(lbl_badge)


class ListaActividadWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(_px(2))
        self._filas: list[QWidget] = []
        self._lbl_vacio = QLabel(self)
        self._lbl_vacio.setFont(fuente(TAMANO_SMALL))
        self._lbl_vacio.setStyleSheet(f"color: {color('gris_apagado')}; padding: {_px(14)}px 0px; background: transparent;")
        self._lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lay.addWidget(self._lbl_vacio)
        self._lbl_vacio.hide()

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
            color_derecha or color("texto_oscuro"),
            badge,
            badge_bg or color("fondo_insignia"),
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
                totales_dia = self._estadisticas.total_por_dia(desde, hasta)
                for dia, total in totales_dia:
                    puntos_grafico.append((dia.strftime("%d/%m"), float(total)))
            except Exception:
                pass

        if not puntos_grafico:
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
        self.signals.datos_listos.emit(datos)


class DashboardPrincipalWidget(QWidget):
    """Vista principal con métricas clave, gráfico interactivo y pestañas de actividad."""

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

        self.setStyleSheet(estilo_dashboard())
        self._construir_ui()
        self.recargar_datos()

    def _construir_ui(self) -> None:
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setObjectName("scrollDashboard")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

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

        self.lbl_saludo = QLabel(f"{saludo}, {self._usuario.capitalize()}")
        self.lbl_saludo.setFont(fuente(TAMANO_TITLE if escala() == ESCALA_NORMAL else TAMANO_SUBTITLE, negrita=True))
        self.lbl_saludo.setStyleSheet(f"color: {color('texto_oscuro')};")
        fila_sup_header.addWidget(self.lbl_saludo)

        fila_sup_header.addStretch()

        self.lbl_logo = QLabel()
        ruta_logo = RECURSOS_DIR / "logo_sf_crop.png"
        if not ruta_logo.is_file():
            ruta_logo = RECURSOS_DIR / "logo_sf.png"
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

        self.lbl_nota_plan = QLabel("Gratis: 12 meses de estadísticas. Con el plan Mensual ves todo el historial.")
        self.lbl_nota_plan.setStyleSheet(f"color: {color('ambar_texto')}; font-size: {_px(12)}px; font-weight: 500;")
        col_header.addWidget(self.lbl_nota_plan)

        layout_cont.addLayout(col_header)

        grid_kpi = QGridLayout()
        grid_kpi.setHorizontalSpacing(_px(14))
        grid_kpi.setVerticalSpacing(_px(14))
        grid_kpi.setVerticalSpacing(10)

        self.kpi_ventas = KPICard("Ventas del período", "ventas", color("verde_acento"), color("pastilla_positiva"))
        self.kpi_pedidos = KPICard("Ventas realizadas", "pedidos", color("acento_teal"), color("pastilla_teal"))
        self.kpi_ticket = KPICard("Ticket promedio", "ticket", color("acento_ambar"), color("pastilla_alerta"))
        self.kpi_unidades = KPICard("Unidades vendidas", "unidades", color("acento_sky"), color("pastilla_sky"))

        grid_kpi.addWidget(self.kpi_ventas, 0, 0)
        grid_kpi.addWidget(self.kpi_pedidos, 0, 1)
        grid_kpi.addWidget(self.kpi_ticket, 0, 2)
        grid_kpi.addWidget(self.kpi_unidades, 0, 3)
        layout_cont.addLayout(grid_kpi)

        tarjeta_grafico = QFrame()
        tarjeta_grafico.setObjectName("tarjetaGrafico")

        lay_grafico = QVBoxLayout(tarjeta_grafico)
        lay_grafico.setContentsMargins(_px(16), _px(12), _px(16), _px(12))
        lay_grafico.setSpacing(_px(10))

        header_graf = QHBoxLayout()
        header_graf.setSpacing(_px(8))

        lbl_tit_graf = QLabel("Tendencia de ingresos")
        lbl_tit_graf.setFont(fuente(TAMANO_TITLE if escala() == ESCALA_NORMAL else TAMANO_SUBTITLE, negrita=True))
        lbl_tit_graf.setStyleSheet(f"color: {color('texto_oscuro')};")
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
        grid_actividad.addWidget(self._crear_tarjeta_actividad("Últimas ventas", self.tablaVentas), 0, 0)
        grid_actividad.addWidget(self._crear_tarjeta_actividad("Top productos", self.tablaTop), 0, 1)
        grid_actividad.addWidget(self._crear_tarjeta_actividad("Alertas de stock", self.tablaAlertas), 1, 0)
        grid_actividad.addWidget(self._crear_tarjeta_actividad("Clientes con saldo", self.tablaClientes), 1, 1)

        layout_cont.addLayout(grid_actividad)

        layout_cont.addStretch()
        scroll.setWidget(contenedor)
        layout_raiz.addWidget(scroll)

    def _crear_tarjeta_actividad(self, titulo: str, widget_lista: QWidget) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaActividad")

        lay = QVBoxLayout(tarjeta)
        lay.setContentsMargins(_px(16), _px(12), _px(16), _px(12))
        lay.setSpacing(_px(8))

        lbl_tit = QLabel(titulo)
        lbl_tit.setFont(fuente(TAMANO_BODY, negrita=True))
        lbl_tit.setStyleSheet(f"color: {color('texto_oscuro')};")
        lay.addWidget(lbl_tit)
        lay.addWidget(widget_lista)
        lay.addStretch()
        return tarjeta

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
                color_derecha=color("verde_acento"),
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
                color_derecha=color("texto_oscuro"),
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
                color_derecha=color("rojo_alerta"),
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
                color_derecha=color("rojo_alerta") if p.get("es_cero") else color("ambar_alerta"),
            )
