from __future__ import annotations

import re

from PyQt6.QtCore import QEasingCurve, QEvent, QObject, QParallelAnimationGroup, QPoint, QPropertyAnimation, QTimer, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.estilos import escala as escala_activa
from ui.tema import color, familia

DURACION_AVISO = 8000
DURACION_LIMITE = 10000

ESPACIO_EXTRA = 10

_INSTANCIAS: list["Notificacion"] = []
_PATRON_FILA = re.compile(r"^(.*?)\s*\(([^()]+(?:\([^()]+\))?)\)$")


class IconoCapsula(QWidget):

    def __init__(self, tipo: str, color_fondo: str, color_acento: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fondo = QColor(color_fondo)
        self._acento = QColor(color_acento)
        self._tipo = tipo
        self._ajustar_tamano()

    def _ajustar_tamano(self) -> None:
        esc = min(escala_activa(), 1.4)
        tam = round(28 * esc)
        self.setFixedSize(tam, tam)

    def actualizar(self, tipo: str, color_fondo: str, color_acento: str) -> None:
        self._tipo = tipo
        self._fondo = QColor(color_fondo)
        self._acento = QColor(color_acento)
        self._ajustar_tamano()
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._fondo))
        w = self.width()
        h = self.height()
        r = round(8 * (w / 28.0))
        p.drawRoundedRect(0, 0, w, h, r, r)

        factor = w / 28.0
        p.setPen(QPen(self._acento, 1.8 * factor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.translate(7 * factor, 7 * factor)
        p.scale((14 / 24) * factor, (14 / 24) * factor)
        path = QPainterPath()
        if self._tipo == "limite":
            path.moveTo(13, 2); path.lineTo(4, 13); path.lineTo(11, 13)
            path.lineTo(11, 22); path.lineTo(20, 11); path.lineTo(13, 11)
            path.closeSubpath()
        elif self._tipo == "critico":
            path.moveTo(12, 3.5); path.lineTo(21.5, 19.5); path.lineTo(2.5, 19.5)
            path.closeSubpath()
            path.moveTo(12, 8.5); path.lineTo(12, 13)
            path.moveTo(12, 16); path.lineTo(12, 16.8)
        elif self._tipo == "vencimiento":
            path.addEllipse(3, 3, 18, 18)
            path.moveTo(12, 8); path.lineTo(12, 12); path.lineTo(15, 14)
        else:
            path.moveTo(5, 13); path.lineTo(9, 17); path.lineTo(19, 7)
        p.drawPath(path)


class Notificacion(QWidget):

    DURACION_MS = 10000
    MARGEN = 16
    ANCHO_MINIMO = 390
    DESPLAZAMIENTO_ENTRADA = 24
    MILISEGUNDOS_MOVIMIENTO = 280

    def __init__(self, parent: QWidget | None = None, duracion_ms: int = DURACION_MS) -> None:
        super().__init__(parent)
        self._duracion_personalizada: int | None = duracion_ms if duracion_ms != self.DURACION_MS else None
        self._saliendo = False
        self._desplazamiento = 0
        self._tipo = "aviso"
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWindowFlags(Qt.WindowType.SubWindow)
        self.setStyleSheet("Notificacion{background: transparent;}")

        layout_exterior = QVBoxLayout(self)
        layout_exterior.setContentsMargins(8, 8, 8, 8)
        layout_exterior.setSpacing(0)

        self._tarjeta = QFrame(self)
        self._tarjeta.setObjectName("tarjeta")
        self._sombra = QGraphicsDropShadowEffect(self._tarjeta)
        self._sombra.setBlurRadius(20)
        self._sombra.setOffset(0, 4)
        self._sombra.setColor(QColor(0, 0, 0, 28))
        self._tarjeta.setGraphicsEffect(self._sombra)
        layout_exterior.addWidget(self._tarjeta)

        self._layout_interior = QHBoxLayout(self._tarjeta)
        self._layout_interior.setContentsMargins(10, 8, 12, 8)
        self._layout_interior.setSpacing(10)

        self._barra_acento = QFrame(self._tarjeta)
        self._barra_acento.setObjectName("barraAcento")
        self._barra_acento.setFixedWidth(4)
        self._barra_acento.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._layout_interior.addWidget(self._barra_acento)

        self._icono = IconoCapsula("aviso", color("pastilla_positiva"), color("verde_profundo"), self._tarjeta)
        self._layout_interior.addWidget(self._icono, 0, Qt.AlignmentFlag.AlignVCenter)

        self._columna = QVBoxLayout()
        self._columna.setContentsMargins(0, 0, 0, 0)
        self._columna.setSpacing(2)

        row_top = QHBoxLayout()
        row_top.setContentsMargins(0, 0, 0, 0)
        row_top.setSpacing(4)

        self._titulo = QLabel("Aviso", self._tarjeta)
        self._titulo.setObjectName("titulo")
        row_top.addWidget(self._titulo)
        row_top.addStretch()

        self._btn_cerrar = QLabel("✕", self._tarjeta)
        self._btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_cerrar.setStyleSheet(f"color: {color('gris_apagado')}; font-size: 10pt; font-family: '{familia()}';")
        row_top.addWidget(self._btn_cerrar)
        self._columna.addLayout(row_top)

        self._cuerpo = QLabel("", self._tarjeta)
        self._cuerpo.setObjectName("cuerpo")
        self._cuerpo.setWordWrap(True)
        self._columna.addWidget(self._cuerpo)

        self._contenedor_filas = QWidget(self._tarjeta)
        self._contenedor_filas.setStyleSheet("background: transparent;")
        self._layout_filas = QVBoxLayout(self._contenedor_filas)
        self._layout_filas.setContentsMargins(0, 2, 0, 0)
        self._layout_filas.setSpacing(3)
        self._columna.addWidget(self._contenedor_filas)

        self._layout_interior.addLayout(self._columna, 1)

        self._aplicar_estilo("aviso")

        self._temporizador = QTimer(self)
        self._temporizador.setSingleShot(True)
        self._temporizador.timeout.connect(self._empezar_a_ocultar)

        self._entrada = QParallelAnimationGroup(self)
        self._movimiento = QPropertyAnimation(self, b"pos", self)
        self._movimiento.setDuration(self.MILISEGUNDOS_MOVIMIENTO)
        self._movimiento.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._entrada.addAnimation(self._movimiento)

        self._salida = QParallelAnimationGroup(self)
        self._retirar = QPropertyAnimation(self, b"pos", self)
        self._retirar.setDuration(self.MILISEGUNDOS_MOVIMIENTO + 40)
        self._retirar.setEasingCurve(QEasingCurve.Type.InCubic)
        self._salida.addAnimation(self._retirar)
        self._salida.finished.connect(self._al_terminar_animacion)

        if parent is not None:
            parent.installEventFilter(self)
        _INSTANCIAS.append(self)
        self.hide()

    def eventFilter(self, objeto: QObject, evento: QEvent) -> bool:
        if objeto is self.parent() and evento.type() == QEvent.Type.Resize and self.isVisible():
            self._reubicar()
        return super().eventFilter(objeto, evento)

    def _obtener_tokens_tipo(self, tipo: str) -> tuple[str, str, str]:
        if tipo == "limite":
            return color("ambar_texto"), color("pastilla_alerta"), color("borde_alerta")
        if tipo == "critico":
            return color("rojo"), color("pastilla_negativa"), color("borde_negativo")
        if tipo == "vencimiento":
            return color("naranja_texto"), color("pastilla_naranja"), color("borde_suave")
        return color("verde_profundo"), color("pastilla_positiva"), color("borde_suave")

    def _aplicar_estilo(self, tipo: str) -> None:
        acento, fondo_capsula, borde_tarjeta = self._obtener_tokens_tipo(tipo)
        self._acento = acento
        self._icono.actualizar(tipo, fondo_capsula, acento)
        esc = min(escala_activa(), 1.4)
        tam = round(11 * esc)
        tam_cerrar = round(10 * esc)
        pad_h = round(10 * esc)
        pad_v = round(8 * esc)
        rad = round(12 * min(esc, 1.25))
        ancho_barra = max(3, round(3.5 * esc))
        rad_barra = round(2 * esc)

        self._barra_acento.setFixedWidth(ancho_barra)
        self._tarjeta.setStyleSheet(
            f"QFrame#tarjeta {{ background-color: {color('blanco')};"
            f" border: 1px solid {borde_tarjeta};"
            f" border-radius: {rad}px; }}"
            f"QFrame#barraAcento {{ background-color: {acento}; border-radius: {rad_barra}px; border: none; margin: {round(3 * esc)}px 0px; }}"
            f"QLabel#titulo {{ color: {acento}; font-size: {tam}pt; font-weight: bold; font-family: '{familia()}'; }}"
            f"QLabel#cuerpo {{ color: {color('gris_linea')}; font-size: {tam}pt; font-family: '{familia()}'; }}"
        )
        self._btn_cerrar.setStyleSheet(
            f"color: {color('gris_apagado')}; font-size: {tam_cerrar}pt; font-family: '{familia()}';"
        )
        self._layout_interior.setContentsMargins(pad_h, pad_v, pad_h, pad_v)
        self._layout_interior.setSpacing(round(10 * esc))
        self._columna.setSpacing(round(3 * esc))

    def _calcular_ancho_tarjeta(self) -> int:
        escala_geom = min(escala_activa(), 1.5)
        ancho_deseado = round(self.ANCHO_MINIMO * escala_geom) + round(20 * escala_geom)
        padre = self.parentWidget()
        if padre is not None and padre.width() > 0:
            ancho_maximo = max(180, padre.width() - self.MARGEN)
            return min(ancho_deseado, ancho_maximo)
        return ancho_deseado

    @staticmethod
    def _extraer_filas(texto: str) -> tuple[str, list[dict]]:
        lineas = [l.strip() for l in texto.splitlines() if l.strip()]
        intro = []
        filas = []
        for l in lineas:
            if l.startswith("•") or l.startswith("-") or l.startswith("*"):
                limpio = l.lstrip("•-* ").strip()
                m = _PATRON_FILA.match(limpio)
                if m:
                    nombre = m.group(1).strip()
                    detalle = m.group(2).strip()
                    critico = bool(
                        re.search(r"stock\s*0\b", detalle, re.I)
                        or "vencido" in detalle.lower()
                        or "vence hoy" in detalle.lower()
                        or re.search(r"vence en [0-3]\b", detalle, re.I)
                    )
                    filas.append({"nombre": nombre, "badge": detalle, "critico": critico})
                else:
                    filas.append({"nombre": limpio, "badge": "", "critico": False})
            elif l.startswith("+") and "más" in l:
                filas.append({"nombre": l, "badge": "", "critico": False})
            else:
                intro.append(l)
        cuerpo = "\n".join(intro)
        return cuerpo, filas

    def _limpiar_filas(self) -> None:
        while self._layout_filas.count():
            item = self._layout_filas.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            sublayout = item.layout()
            if sublayout is not None:
                while sublayout.count():
                    subitem = sublayout.takeAt(0)
                    if subitem.widget() is not None:
                        subitem.widget().deleteLater()

    def mostrar(self, titulo: str, texto: str, desplazamiento: int = 0, tipo: str = "aviso") -> None:
        self._saliendo = False
        self._desplazamiento = desplazamiento
        tit_bajo = titulo.lower()
        if tipo == "aviso":
            if any(palabra in tit_bajo for palabra in ("tope", "límite", "limite", "plan")):
                tipo = "limite"
            elif "vencimiento" in tit_bajo:
                tipo = "vencimiento"
            elif any(palabra in tit_bajo for palabra in ("stock", "fallo", "error", "crítico", "critico")):
                tipo = "critico"

        self._tipo = tipo
        self._aplicar_estilo(tipo)
        self._titulo.setText(titulo)

        cuerpo, filas = self._extraer_filas(texto)
        self._limpiar_filas()

        if filas:
            self._cuerpo.setText(cuerpo)
            self._cuerpo.setVisible(bool(cuerpo))
            self._contenedor_filas.setVisible(True)
            esc = min(escala_activa(), 1.4)
            tam_filas = round(10.5 * esc)
            tam_badge = round(9 * esc)
            pad_v = round(2.5 * esc)
            pad_h = round(6 * esc)
            rad_badge = round(4 * esc)

            self._layout_filas.setSpacing(round(4 * esc))
            for item in filas:
                r = QHBoxLayout()
                r.setContentsMargins(0, 0, 0, 0)
                r.setSpacing(round(6 * esc))
                dot = QLabel("•")
                dot.setStyleSheet(f"color: {self._acento}; font-size: {tam_filas}pt;")
                r.addWidget(dot)
                lbl_n = QLabel(item["nombre"])
                lbl_n.setStyleSheet(f"color: {color('panel_borde')}; font-size: {tam_filas}pt; font-family: '{familia()}';")
                lbl_n.setToolTip(item["nombre"])
                r.addWidget(lbl_n, 1)

                if item.get("badge"):
                    lbl_b = QLabel(item["badge"])
                    es_crit = item.get("critico", False)
                    col_bg = color("pastilla_negativa") if es_crit else color("fondo_insignia")
                    col_fg = color("rojo") if es_crit else color("gris_medio")
                    col_brd = color("borde_negativo") if es_crit else color("borde_suave")
                    lbl_b.setStyleSheet(
                        f"background-color: {col_bg}; color: {col_fg};"
                        f" border: 1px solid {col_brd}; border-radius: {rad_badge}px;"
                        f" padding: {pad_v}px {pad_h}px; font-size: {tam_badge}pt; font-weight: 500; font-family: '{familia()}';"
                    )
                    r.addWidget(lbl_b)
                self._layout_filas.addLayout(r)
        else:
            self._cuerpo.setText(cuerpo or texto)
            self._cuerpo.setVisible(True)
            self._contenedor_filas.setVisible(False)

        ancho = self._calcular_ancho_tarjeta()
        self.setFixedWidth(ancho)
        self.adjustSize()

        self._temporizador.stop()
        destino = self._posicion_final()
        self._entrada.stop()
        self._movimiento.setStartValue(QPoint(destino.x() + self.DESPLAZAMIENTO_ENTRADA, destino.y()))
        self._movimiento.setEndValue(destino)
        self.show()
        self.raise_()
        self._entrada.start()
        duracion = self._duracion_personalizada or (
            DURACION_LIMITE if tipo in ("limite", "advertencia") else DURACION_AVISO
        )
        self._temporizador.start(duracion)

    def espacio_guardado(self) -> int:
        return self.height() + ESPACIO_EXTRA

    def mousePressEvent(self, evento) -> None:
        self._temporizador.stop()
        self.hide()
        self._desregistrar()

    def _desregistrar(self) -> None:
        if self in _INSTANCIAS:
            _INSTANCIAS.remove(self)

    def _posicion_final(self) -> QPoint:
        padre = self.parentWidget()
        if padre is None:
            return self.pos()
        pos_x = max(0, padre.width() - self.width() - self.MARGEN)
        return QPoint(pos_x, self.MARGEN + self._desplazamiento)

    def _reubicar(self) -> None:
        if not self._saliendo:
            ancho = self._calcular_ancho_tarjeta()
            self.setFixedWidth(ancho)
            self.adjustSize()
            self.move(self._posicion_final())

    def _empezar_a_ocultar(self) -> None:
        padre = self.parentWidget()
        salida_x = padre.width() - self.MARGEN if padre is not None else self.x() + self.width()
        self._saliendo = True
        self._salida.stop()
        self._retirar.setStartValue(self.pos())
        self._retirar.setEndValue(QPoint(salida_x, self.y()))
        self._salida.start()

    def _al_terminar_animacion(self) -> None:
        if self._saliendo:
            self._saliendo = False
            self.hide()
            self._desregistrar()
