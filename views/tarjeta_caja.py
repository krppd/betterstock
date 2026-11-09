from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from models.caja_movimiento import CajaMovimiento
from models.cierre import CierreRegistrado
from ui.estilos import (
    TAMANO_BODY,
    TAMANO_MICRO,
    TAMANO_SMALL,
    TAMANO_SUBTITLE,
    escala,
    fuente,
)
from ui.tema import color


def _px(valor: int) -> int:
    return round(valor * escala())


class TarjetaMovimientoCaja(QFrame):
    def __init__(
        self,
        movimiento: CajaMovimiento,
        indice: int,
        on_click: Callable[[int], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.movimiento = movimiento
        self.indice = indice
        self._on_click = on_click
        self._seleccionada = False

        self.setObjectName("tarjetaMovimiento")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(_px(12), _px(8), _px(12), _px(8))
        lay.setSpacing(_px(8))

        col_izq = QVBoxLayout()
        col_izq.setContentsMargins(0, 0, 0, 0)
        col_izq.setSpacing(_px(2))

        tipo_texto = movimiento.tipo.capitalize()
        hora_texto = movimiento.hora[:5] if len(movimiento.hora) >= 5 else movimiento.hora
        self.lbl_arriba = QLabel(f"{hora_texto} · {tipo_texto}", self)
        fuente_arr = fuente(TAMANO_SMALL, negrita=True)
        if movimiento.anulado:
            fuente_arr.setStrikeOut(True)
        self.lbl_arriba.setFont(fuente_arr)
        col_izq.addWidget(self.lbl_arriba)

        estado_texto = "Anulado" if movimiento.anulado else "Activo"
        self.lbl_abajo = QLabel(f"{movimiento.concepto} · {estado_texto}", self)
        fuente_abj = fuente(TAMANO_SMALL)
        if movimiento.anulado:
            fuente_abj.setStrikeOut(True)
        self.lbl_abajo.setFont(fuente_abj)
        col_izq.addWidget(self.lbl_abajo)

        lay.addLayout(col_izq, 1)

        col_der = QHBoxLayout()
        col_der.setContentsMargins(0, 0, 0, 0)
        col_der.setSpacing(_px(6))

        if movimiento.anulado:
            self.lbl_badge = QLabel("Anulado", self)
            self.lbl_badge.setFont(fuente(TAMANO_MICRO, negrita=True))
            self.lbl_badge.setStyleSheet(
                f"background-color: {color('pastilla_negativa')}; color: {color('rojo_oscuro')}; "
                f"border: 1px solid {color('borde_negativo')}; border-radius: {_px(6)}px; "
                f"padding: {_px(2)}px {_px(6)}px;"
            )
            self.lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col_der.addWidget(self.lbl_badge)

        signo = "-" if movimiento.es_egreso else "+"
        monto_str = f"{signo}$ {movimiento.importe:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.lbl_importe = QLabel(monto_str, self)
        fuente_imp = fuente(TAMANO_SUBTITLE, negrita=True, tabular=True)
        if movimiento.anulado:
            fuente_imp.setStrikeOut(True)
        self.lbl_importe.setFont(fuente_imp)
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

    def _aplicar_estilo(self) -> None:
        radio = _px(12)
        if self.movimiento.anulado:
            color_txt = color("gris_apagado")
            color_imp = color("gris_apagado")
            if self._seleccionada:
                fondo = color("fondo_insignia")
                borde = f"2px solid {color('gris_medio')}"
            else:
                fondo = color("fondo_suave")
                borde = f"1px solid {color('borde_suave')}"
        else:
            color_txt = color("texto_oscuro")
            color_imp = color("rojo_oscuro") if self.movimiento.es_egreso else color("verde_acento")
            if self._seleccionada:
                fondo = color("pastilla_positiva")
                borde = f"2px solid {color('verde_acento')}"
            else:
                fondo = color("blanco")
                borde = f"1px solid {color('borde_suave')}"

        self.setStyleSheet(
            f"QFrame#tarjetaMovimiento {{ "
            f"background-color: {fondo}; "
            f"border: {borde}; "
            f"border-radius: {radio}px; "
            f"}} "
            f"QFrame#tarjetaMovimiento:hover {{ "
            f"border-color: {color('borde_destacado')}; "
            f"}}"
        )
        self.lbl_arriba.setStyleSheet(f"color: {color_txt}; background: transparent; border: none;")
        self.lbl_abajo.setStyleSheet(f"color: {color('gris_medio') if not self.movimiento.anulado else color_txt}; background: transparent; border: none;")
        self.lbl_importe.setStyleSheet(f"color: {color_imp}; background: transparent; border: none;")


class TarjetaHistorialCierre(QFrame):
    def __init__(
        self,
        cierre: CierreRegistrado,
        ciego: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.cierre = cierre
        self.setObjectName("tarjetaHistorialCierre")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(_px(12), _px(8), _px(12), _px(8))
        lay.setSpacing(_px(8))

        col_izq = QVBoxLayout()
        col_izq.setContentsMargins(0, 0, 0, 0)
        col_izq.setSpacing(_px(2))

        dia_mes = cierre.fecha.strftime("%d/%m")
        usuario = cierre.usuario or "—"
        lbl_arr = QLabel(f"{dia_mes} · {cierre.fecha_texto} {usuario}", self)
        lbl_arr.setFont(fuente(TAMANO_SMALL, negrita=True))
        lbl_arr.setStyleSheet(f"color: {color('texto_oscuro')}; background: transparent; border: none;")
        col_izq.addWidget(lbl_arr)

        ventas_txt = f"{cierre.cantidad_ventas} {'venta' if cierre.cantidad_ventas == 1 else 'ventas'}"
        from utils.formato import formatear_dinero
        if ciego:
            sub = f"{ventas_txt} · Declarado {formatear_dinero(cierre.declarado)}"
        else:
            sub = f"{ventas_txt} · Esperado {formatear_dinero(cierre.total_esperado)}"
        lbl_abj = QLabel(sub, self)
        lbl_abj.setFont(fuente(TAMANO_SMALL))
        lbl_abj.setStyleSheet(f"color: {color('gris_medio')}; background: transparent; border: none;")
        col_izq.addWidget(lbl_abj)

        lay.addLayout(col_izq, 1)

        from utils.formato import formatear_dinero
        if cierre.cuadra:
            txt_der = f"{formatear_dinero(cierre.declarado)} · cuadra"
            col_der = color("verde_acento")
        elif cierre.sobrante > 0:
            txt_der = f"sobrante {formatear_dinero(cierre.sobrante)}"
            col_der = color("verde_acento")
        else:
            txt_der = f"faltante {formatear_dinero(cierre.faltante)}"
            col_der = color("rojo_oscuro")

        lbl_der = QLabel(txt_der, self)
        lbl_der.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        lbl_der.setStyleSheet(f"color: {col_der}; background: transparent; border: none;")
        lbl_der.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(lbl_der)

        radio = _px(12)
        self.setStyleSheet(
            f"QFrame#tarjetaHistorialCierre {{ "
            f"background-color: {color('blanco')}; "
            f"border: 1px solid {color('borde_suave')}; "
            f"border-radius: {radio}px; "
            f"}} "
            f"QFrame#tarjetaHistorialCierre:hover {{ "
            f"background-color: {color('fondo_suave')}; "
            f"border-color: {color('borde_destacado')}; "
            f"}}"
        )
