from __future__ import annotations

import math
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from ui.tema import color

COLOR_SUBIDA = color("verde")
COLOR_BAJADA = color("rojo_serie")
COLOR_IGUAL = color("serie_azul")
COLOR_VACIO = color("tendencia_neutra")
PROPORCION_VACIO = 0.04
MARGEN_EJE_Y = 1.18
ANCHO_POR_ETIQUETA = 47


class _EjeXCategorias:

    def __init__(self) -> None:
        self._items: list[str] = []

    def clear(self) -> None:
        self._items.clear()

    def append(self, item: str) -> None:
        self._items.append(item)

    def categories(self) -> list[str]:
        return list(self._items)


class _ChartProxy:

    def __init__(self, titulo: str) -> None:
        self._titulo = titulo

    def title(self) -> str:
        return self._titulo


class GraficoVentas(QWidget):
    """Gráfico de barras con Matplotlib."""

    def __init__(
        self,
        puntos: list[tuple[str, float]],
        variacion: float | None,
        titulo: str = "Ventas por día",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._puntos = list(puntos)
        self._titulo = titulo
        self._variacion = variacion
        self._eje_x = _EjeXCategorias()
        self._paso = 1
        self._bars: list = []

        self.setMinimumHeight(150)

        self._fig = Figure(facecolor=color("blanco"), edgecolor="none")
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._ax = self._fig.add_subplot(111)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

        self._canvas.mpl_connect("motion_notify_event", self._al_mover_mouse)

        self.actualizar_puntos(puntos, variacion, titulo)

    def chart(self) -> _ChartProxy:
        return _ChartProxy(self._titulo)

    @staticmethod
    def _color(variacion: float | None) -> str:
        if variacion is None:
            return COLOR_IGUAL
        if variacion > 0:
            return COLOR_SUBIDA
        if variacion < 0:
            return COLOR_BAJADA
        return COLOR_IGUAL

    def _paso_etiquetas(self) -> int:
        ancho = self.width()
        if ancho <= 0:
            return 1
        return max(1, math.ceil(len(self._puntos) * ANCHO_POR_ETIQUETA / ancho))

    def _aplicar_etiquetas(self) -> None:
        self._paso = self._paso_etiquetas()
        self._eje_x.clear()
        for indice, (etiqueta, _) in enumerate(self._puntos):
            self._eje_x.append(etiqueta if indice % self._paso == 0 else "")

        if not self._puntos:
            return

        self._ax.set_xticks(range(0, len(self._puntos), self._paso))
        self._ax.set_xticklabels(
            [etiqueta for etiqueta in self._eje_x.categories() if etiqueta],
            color=color("gris_medio"), fontsize=8)

    def resizeEvent(self, evento: QResizeEvent) -> None:
        super().resizeEvent(evento)
        if self._puntos and self._paso_etiquetas() != self._paso:
            self._aplicar_etiquetas()
            if self.isVisible():
                self._canvas.draw_idle()

    def actualizar_puntos(
        self,
        puntos: list[tuple[str, float]],
        variacion: float | None,
        titulo: str = "Ventas por día",
    ) -> None:
        self._puntos = list(puntos)
        self._variacion = variacion
        self._titulo = titulo

        self._ax.clear()
        self._ax.set_facecolor(color("blanco"))
        self._ax.set_title(self._titulo, fontsize=10, fontweight="bold",
                           color=color("texto_oscuro"), pad=4)

        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.spines["left"].set_color(color("borde_suave"))
        self._ax.spines["bottom"].set_color(color("borde_suave"))

        self._ax.yaxis.grid(True, linestyle=":", alpha=0.8,
                            color=color("borde_suave"), zorder=0)
        self._ax.xaxis.grid(False)

        x_indices = list(range(len(self._puntos)))
        valores = [p[1] for p in self._puntos]
        max_val = max(valores, default=0.0) * MARGEN_EJE_Y or 1.0

        col_base = self._color(self._variacion)
        col_vacio = COLOR_VACIO

        alturas_reales = [v if v > 0 else 0.0 for v in valores]
        alturas_vacias = [0.0 if v > 0 else max_val * PROPORCION_VACIO for v in valores]

        bar_w = 0.58 if len(self._puntos) > 10 else 0.38
        self._bars = list(self._ax.bar(x_indices, alturas_reales, width=bar_w, color=col_base, zorder=3))
        self._ax.bar(x_indices, alturas_vacias, width=bar_w, color=col_vacio, zorder=3)

        def formato_moneda(x, pos):
            if x <= 0:
                return "$0"
            if x >= 1000:
                val_str = f"{int(x):,}".replace(",", ".")
                return f"${val_str}"
            return f"${int(x)}"

        self._ax.yaxis.set_major_formatter(ticker.FuncFormatter(formato_moneda))
        self._ax.tick_params(axis="y", colors=color("gris_medio"), labelsize=8)
        self._ax.tick_params(axis="x", colors=color("gris_medio"), labelsize=8, length=0)
        self._ax.set_ylim(0, max_val)

        self._annot = self._ax.annotate(
            "",
            xy=(0, 0),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.4", fc=color("texto_oscuro"), ec="none", alpha=0.95),
            fontsize=8,
            fontweight="bold",
            color=color("blanco"),
            zorder=10,
        )
        self._annot.set_visible(False)

        self._aplicar_etiquetas()
        self._fig.subplots_adjust(left=0.08, right=0.98, top=0.80, bottom=0.18)
        self._canvas.draw_idle()

    def _al_mover_mouse(self, event) -> None:
        if event.inaxes == self._ax and self._bars:
            for bar, (label, val) in zip(self._bars, self._puntos):
                cont, _ = bar.contains(event)
                if cont:
                    cx = bar.get_x() + bar.get_width() / 2.0
                    cy = bar.get_height() if val > 0 else 0.05
                    self._annot.xy = (cx, cy)
                    val_str = f"{int(val):,}".replace(",", ".") if val >= 1000 else f"{int(val)}"
                    self._annot.set_text(f"{label}: ${val_str}")
                    self._annot.set_visible(True)
                    self._canvas.draw_idle()
                    return
        if self._annot.get_visible():
            self._annot.set_visible(False)
            self._canvas.draw_idle()
