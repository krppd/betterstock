from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    SimpleCardWidget,
    SubtitleLabel,
)

from models.caja_movimiento import CajaMovimiento
from models.cierre import CierreRegistrado
from ui.estilos import (
    TAMANO_BODY,
    TAMANO_SMALL,
    TAMANO_SUBTITLE,
    escala,
    fuente,
)
from ui.fluent import CLARO, OSCURO, color


def _px(valor: int) -> int:
    return round(valor * escala())


def _tinta(nombre: str) -> tuple[QColor, QColor]:
    """Devuelve el par (claro, oscuro) de un token Fluent para labels adaptativos."""
    return QColor(CLARO[nombre]), QColor(OSCURO[nombre])


def _fuente(punto: int, *, negrita: bool = False, tabular: bool = False,
            tachado: bool = False):
    """Fuente del tema con soporte para texto tachado (movimientos anulados)."""
    resultado = fuente(punto, negrita=negrita, tabular=tabular)
    if tachado:
        resultado.setStrikeOut(True)
    return resultado


class TarjetaMovimientoCaja(SimpleCardWidget):
    """Tarjeta Fluent de un movimiento de caja (activo o anulado)."""

    def __init__(
        self,
        movimiento: CajaMovimiento,
        indice: int,
        on_click: Callable[[int], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self.movimiento = movimiento
        self.indice = indice
        self._on_click = on_click
        self._seleccionada = False
        self._color_borde = QColor(CLARO["borde_suave"])

        super().__init__(parent)

        self.setObjectName("tarjetaMovimiento")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setBorderRadius(_px(12))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(_px(12), _px(8), _px(12), _px(8))
        lay.setSpacing(_px(8))

        col_izq = QVBoxLayout()
        col_izq.setContentsMargins(0, 0, 0, 0)
        col_izq.setSpacing(_px(2))

        tipo_texto = movimiento.tipo.capitalize()
        hora_texto = movimiento.hora[:5] if len(movimiento.hora) >= 5 else movimiento.hora
        self.lbl_arriba = BodyLabel(f"{hora_texto} · {tipo_texto}", self)
        self.lbl_arriba.setFont(_fuente(TAMANO_SMALL, negrita=True, tachado=movimiento.anulado))
        col_izq.addWidget(self.lbl_arriba)

        estado_texto = "Anulado" if movimiento.anulado else "Activo"
        self.lbl_abajo = BodyLabel(f"{movimiento.concepto} · {estado_texto}", self)
        self.lbl_abajo.setFont(_fuente(TAMANO_SMALL, tachado=movimiento.anulado))
        col_izq.addWidget(self.lbl_abajo)

        lay.addLayout(col_izq, 1)

        col_der = QHBoxLayout()
        col_der.setContentsMargins(0, 0, 0, 0)
        col_der.setSpacing(_px(6))

        if movimiento.anulado:
            self.lbl_badge = QLabel("Anulado", self)
            self.lbl_badge.setFont(fuente(TAMANO_SMALL, negrita=True))
            self.lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col_der.addWidget(self.lbl_badge)

        signo = "-" if movimiento.es_egreso else "+"
        monto_str = f"{signo}$ {movimiento.importe:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.lbl_importe = SubtitleLabel(monto_str, self)
        self.lbl_importe.setFont(_fuente(TAMANO_SUBTITLE, negrita=True, tabular=True,
                                         tachado=movimiento.anulado))
        self.lbl_importe.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        col_der.addWidget(self.lbl_importe)

        lay.addLayout(col_der)
        self._aplicar_estilo()

    @property
    def seleccionada(self) -> bool:
        return self._seleccionada

    def set_seleccionada(self, seleccionada: bool) -> None:
        self._seleccionada = seleccionada
        self._aplicar_estilo()

    def click(self) -> None:
        if self._on_click is not None:
            self._on_click(self.indice)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.click()
        super().mousePressEvent(event)

    def paintEvent(self, evento) -> None:
        """Dibuja el relleno y el borde de la tarjeta con los colores del tema."""
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.setPen(QPen(self._color_borde, 2 if self._seleccionada else 1))
        pintor.setBrush(self.backgroundColor)
        radio = self.borderRadius
        pintor.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), radio, radio)

    def _updateBackgroundColor(self) -> None:
        """Mantiene el color propio de la tarjeta (no el genérico de la carta)."""
        self._aplicar_estilo()

    def _aplicar_estilo(self) -> None:
        if self.movimiento.anulado:
            self.lbl_arriba.setTextColor(*_tinta("gris_apagado"))
            self.lbl_abajo.setTextColor(*_tinta("gris_apagado"))
            self.lbl_importe.setTextColor(*_tinta("gris_apagado"))
            fondo = color("fondo_suave")
            borde = color("gris_medio") if self._seleccionada else color("borde_suave")
        else:
            self.lbl_arriba.setTextColor(*_tinta("texto"))
            self.lbl_abajo.setTextColor(*_tinta("gris_medio"))
            self.lbl_importe.setTextColor(
                *_tinta("error" if self.movimiento.es_egreso else "exito"))
            fondo = color("pastilla_positiva") if self._seleccionada else color("fondo_tarjeta")
            borde = color("acento") if self._seleccionada else color("borde_suave")

        self._color_borde = QColor(borde)
        self.setBackgroundColor(QColor(fondo))

        if hasattr(self, "lbl_badge"):
            self.lbl_badge.setStyleSheet(
                f"background-color: {color('pastilla_negativa')}; color: {color('error')}; "
                f"border: 1px solid {color('borde')}; border-radius: {_px(6)}px; "
                f"padding: {_px(2)}px {_px(6)}px;"
            )

        self.update()


class TarjetaHistorialCierre(SimpleCardWidget):
    """Tarjeta Fluent con el resumen de un cierre de caja."""

    def __init__(
        self,
        cierre: CierreRegistrado,
        ciego: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.cierre = cierre
        self.setObjectName("tarjetaHistorialCierre")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setBorderRadius(_px(8))

        from utils.formato import formatear_dinero

        lay = QHBoxLayout(self)
        lay.setContentsMargins(_px(14), _px(10), _px(14), _px(10))
        lay.setSpacing(_px(12))

        col_izq = QVBoxLayout()
        col_izq.setContentsMargins(0, 0, 0, 0)
        col_izq.setSpacing(_px(3))

        hora_val = getattr(cierre, "hora", None) or ""
        hora_txt = f" {hora_val[:5]}" if len(hora_val) >= 5 else (f" {hora_val}" if hora_val else "")
        usuario = cierre.usuario or "—"
        lbl_arr = BodyLabel(f"{cierre.fecha_texto}{hora_txt} · {usuario}", self)
        lbl_arr.setFont(fuente(TAMANO_BODY, negrita=True))
        lbl_arr.setTextColor(*_tinta("texto"))
        col_izq.addWidget(lbl_arr)

        ventas_txt = f"{cierre.cantidad_ventas} {'venta' if cierre.cantidad_ventas == 1 else 'ventas'}"
        if ciego:
            sub = f"{ventas_txt} · Declarado {formatear_dinero(cierre.declarado)}"
        else:
            sub = f"{ventas_txt} · Esperado {formatear_dinero(cierre.total_esperado)}"
        lbl_abj = BodyLabel(sub, self)
        lbl_abj.setFont(fuente(TAMANO_SMALL))
        lbl_abj.setTextColor(*_tinta("gris_medio"))
        col_izq.addWidget(lbl_abj)

        lay.addLayout(col_izq, 1)

        col_der = QVBoxLayout()
        col_der.setContentsMargins(0, 0, 0, 0)
        col_der.setSpacing(_px(2))

        lbl_monto = SubtitleLabel(formatear_dinero(cierre.declarado), self)
        lbl_monto.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        lbl_monto.setTextColor(*_tinta("texto"))
        lbl_monto.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        col_der.addWidget(lbl_monto)

        if cierre.cuadra:
            txt_estado = "Cuadra"
            col_estado = "exito"
        elif cierre.sobrante > 0:
            txt_estado = f"+{formatear_dinero(cierre.sobrante)} sobrante"
            col_estado = "exito"
        else:
            txt_estado = f"-{formatear_dinero(cierre.faltante)} faltante"
            col_estado = "error"

        lbl_estado = BodyLabel(txt_estado, self)
        lbl_estado.setFont(fuente(TAMANO_SMALL, negrita=True))
        lbl_estado.setTextColor(*_tinta(col_estado))
        lbl_estado.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        col_der.addWidget(lbl_estado)

        lay.addLayout(col_der)

        self._aplicar_estilo()

    def _updateBackgroundColor(self) -> None:
        self._aplicar_estilo()

    def _aplicar_estilo(self) -> None:
        self.setBackgroundColor(QColor(color("fondo_tarjeta")))
        self.update()
