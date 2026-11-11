from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

from PyQt6 import sip
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtQuickWidgets import QQuickWidget
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ComboBox,
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    SegmentedWidget,
    SubtitleLabel,
    TableWidget,
    setCustomStyleSheet,
)

from models import medio_pago
from services.estadisticas_ventas import (
    Comparacion,
    EstadisticasVentas,
    ResumenPeriodo,
)
from services.gestor_anulaciones import GestorAnulaciones
from services.plan_motor import limite, plan_actual
from ui.estilos import AMBAR_TEXTO, escala
from ui.fluent import CLARO, OSCURO, color, conectar_tema
from ui.qml.bridges.puente_tarjetas import PuenteTarjetas
from ui.tema import medida, puente_tema
from ui.widgets.grafico_ventas import GraficoVentas
from ui.widgets.notificacion import Notificacion
from utils.formato import (
    SEPARADOR_DECIMAL,
    SEPARADOR_MILES,
    formatear_cantidad,
    formatear_dinero,
)
from views.ventana_base import VentanaBase
from views.ventana_detalle_venta import VentanaDetalleVenta

HOY = "Hoy"
MES_ACTUAL = "Mes actual"
MES_ANTERIOR = "Mes anterior"
ULTIMOS_30 = "Últimos 30 días"
ULTIMOS_12_MESES = "Últimos 12 meses"
TODO_EL_HISTORIAL = "Todo el historial"

DIAS_12_MESES = 365
DIAS_POR_BARRA = 60

ALTO_TARJETAS_QML = medida("alto_tarjeta")
ALTO_BANDA_QML = medida("alto_banda")


def _ruta_qml(nombre: str) -> Path:
    raiz = getattr(sys, "_MEIPASS", None)
    if raiz is not None:
        return Path(raiz) / "ui" / "qml" / nombre
    return Path(__file__).resolve().parent.parent / "ui" / "qml" / nombre


def _numero(valor: float, decimales: int = 1) -> str:
    if decimales <= 0:
        return f"{valor:,.0f}".replace(",", SEPARADOR_MILES)
    entero, _, fraccion = f"{valor:,.{decimales}f}".partition(".")
    return f"{entero.replace(',', SEPARADOR_MILES)}{SEPARADOR_DECIMAL}{fraccion}"


def _tintar(etiqueta, token: str) -> None:
    """Aplica a una etiqueta Fluent el color de un token de ui.fluent (claro y oscuro)."""
    etiqueta.setTextColor(
        QColor(CLARO.get(token, "#000000")),
        QColor(OSCURO.get(token, "#FFFFFF")),
    )


class _TextoMetrica:
    """Texto de una métrica que se dibuja dentro de las tarjetas QML.

    Las tarjetas se renderizan en QML (``TarjetasEstadisticas.qml``); este
    objeto conserva el texto y el color de cada métrica para que la API
    pública de la vista (``ui.lblVentasValor.text()`` y compañía) siga
    funcionando igual que antes de la migración.
    """

    def __init__(self, texto: str = "") -> None:
        self._texto = texto
        self._color = ""

    def text(self) -> str:
        return self._texto

    def setText(self, texto: str) -> None:
        self._texto = texto

    def setTextColor(self, color, _oscuro=None) -> None:
        self._color = color.name() if isinstance(color, QColor) else str(color)

    def color(self) -> str:
        return self._color


class _UiEstadisticas:
    """Interfaz Fluent de la ventana de estadísticas.

    Mantiene los nombres de widget heredados (``cmbPeriodo``, ``tblVentas``,
    ``stackVentas``…) para no romper código ni tests que los consulten.
    Las cuatro tarjetas de métricas se dibujan en QML.
    """

    def __init__(self, ventana: QWidget) -> None:
        self.verticalLayout = QVBoxLayout(ventana)
        self.verticalLayout.setContentsMargins(16, 10, 16, 10)
        self.verticalLayout.setSpacing(8)

        self._armar_barra(ventana)
        self._armar_tarjetas(ventana)
        self._armar_grafico(ventana)
        self._armar_tablas(ventana)

    def _armar_barra(self, ventana: QWidget) -> None:
        barra = QHBoxLayout()
        barra.setSpacing(8)
        self.hlyPeriodo = barra

        self.lblTitulo = SubtitleLabel("Estadísticas de ventas", ventana)
        _tintar(self.lblTitulo, "texto")
        barra.addWidget(self.lblTitulo)
        barra.addStretch(1)

        self.lblPeriodo = BodyLabel("Período:", ventana)
        barra.addWidget(self.lblPeriodo)

        self.cmbPeriodo = ComboBox(ventana)
        self.cmbPeriodo.setObjectName("cmbPeriodo")
        self.cmbPeriodo.setMinimumWidth(190)
        barra.addWidget(self.cmbPeriodo)

        self.btnActualizar = PrimaryPushButton(FIF.SYNC, "Actualizar", ventana)
        barra.addWidget(self.btnActualizar)

        self.lblPlan = CaptionLabel("", ventana)
        self.verticalLayout.addLayout(barra)
        self.verticalLayout.addWidget(self.lblPlan)

        self.lblRango = BodyLabel("", ventana)
        self.lblRango.setWordWrap(True)
        self.verticalLayout.addWidget(self.lblRango)

    def _armar_tarjetas(self, ventana: QWidget) -> None:
        """Deja el hueco donde se incrusta el QML de las cuatro tarjetas."""
        self.glyTarjetas = QGridLayout()
        self.glyTarjetas.setSpacing(8)
        self.verticalLayout.addLayout(self.glyTarjetas)

        self.lblVentasTitulo = _TextoMetrica("Ventas")
        self.lblVentasValor = _TextoMetrica("0")
        self.lblVentasVariacion = _TextoMetrica("—")
        self.lblVentasDetalle = _TextoMetrica("")

        self.lblUnidadesTitulo = _TextoMetrica("Unidades")
        self.lblUnidadesValor = _TextoMetrica("0")
        self.lblUnidadesVariacion = _TextoMetrica("—")
        self.lblUnidadesDetalle = _TextoMetrica("")

        self.lblTotalTitulo = _TextoMetrica("Facturado")
        self.lblTotalValor = _TextoMetrica("$ 0,00")
        self.lblTotalVariacion = _TextoMetrica("—")
        self.lblTotalDetalle = _TextoMetrica("")

        self.lblTicketTitulo = _TextoMetrica("Ticket promedio")
        self.lblTicketValor = _TextoMetrica("$ 0,00")
        self.lblTicketVariacion = _TextoMetrica("—")
        self.lblTicketDetalle = _TextoMetrica("")

    def _armar_grafico(self, ventana: QWidget) -> None:
        self.grafico = CardWidget(ventana)
        self.grafico.setObjectName("grafico")
        self.grafico.setBorderRadius(8)
        self.grafico.setMinimumHeight(round(150 * escala()))

        self.lyGrafico = QVBoxLayout(self.grafico)
        self.lyGrafico.setContentsMargins(12, 10, 12, 10)
        self.verticalLayout.addWidget(self.grafico)

    def _armar_tablas(self, ventana: QWidget) -> None:
        fila_solapas = QHBoxLayout()
        fila_solapas.setSpacing(8)
        self.hlyVentas = fila_solapas

        self.solapas = SegmentedWidget(ventana)
        self.solapas.addItem("ventas", "Ventas")
        self.solapas.addItem("ranking", "Más vendidos")
        self.btnVentas = self.solapas.items["ventas"]
        self.btnRanking = self.solapas.items["ranking"]
        fila_solapas.addWidget(self.solapas)
        fila_solapas.addStretch(1)

        self.btnDetalle = PushButton(FIF.INFO, "Detalles", ventana)
        fila_solapas.addWidget(self.btnDetalle)
        self.verticalLayout.addLayout(fila_solapas)

        self.stackVentas = QStackedWidget(ventana)
        self.stackVentas.setObjectName("stackVentas")
        self.stackVentas.setMinimumHeight(round(260 * escala()))

        self.tblVentas = TableWidget(ventana)
        self.tblVentas.setObjectName("tblVentas")
        self.tblVentas.setColumnCount(6)
        self.tblVentas.setRowCount(0)
        self.tblVentas.setHorizontalHeaderLabels(
            ["Hora", "Unidades", "Total", "Medio", "Detalle", "Estado"])
        self._estilo_tabla(self.tblVentas)

        self.tblRanking = TableWidget(ventana)
        self.tblRanking.setObjectName("tblRanking")
        self.tblRanking.setColumnCount(4)
        self.tblRanking.setRowCount(0)
        self.tblRanking.setHorizontalHeaderLabels(
            ["Producto", "Unidades", "Total", "% del total"])
        self._estilo_tabla(self.tblRanking)

        self.stackVentas.addWidget(self._tarjeta_tabla(self.tblVentas))
        self.stackVentas.addWidget(self._tarjeta_tabla(self.tblRanking))
        self.verticalLayout.addWidget(self.stackVentas, 1)

    @staticmethod
    def _estilo_tabla(tabla: TableWidget) -> None:
        tabla.setBorderVisible(True)
        tabla.setBorderRadius(8)
        tabla.setWordWrap(False)

    @staticmethod
    def _tarjeta_tabla(tabla: TableWidget) -> CardWidget:
        tarjeta = CardWidget(tabla.parentWidget())
        tarjeta.setBorderRadius(8)
        lay = QVBoxLayout(tarjeta)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.addWidget(tabla)
        return tarjeta


class VentanaEstadisticas(QWidget, VentanaBase):
    MAXIMO_VARIACION = 999.0

    def __init__(self, estadisticas: EstadisticasVentas,
                 anulaciones: GestorAnulaciones | None = None) -> None:
        super().__init__()
        self._estadisticas = estadisticas
        self._anulaciones = anulaciones
        self._grafico: GraficoVentas | None = None
        self._ventas_mostradas = []
        self._avisadas_lectura: set[str] = set()
        self._periodo_elegido = ULTIMOS_30
        self._armando_periodos = False
        self._ya_mostrada = False
        self._comparacion_actual: Comparacion | None = None
        self._series_actual: tuple[list, list, list, list] | None = None

        self.ui = _UiEstadisticas(self)
        self._aviso_ventas_ilegibles = Notificacion(self)
        self._aviso_limite = Notificacion(self)

        self._armar_tarjetas_qml()
        self.estirar_columnas(self.ui.tblVentas)
        encabezado = self.ui.tblVentas.horizontalHeader()
        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        encabezado.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        encabezado.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        encabezado.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        for tabla in (self.ui.tblRanking,):
            self.estirar_columnas(tabla)
            encabezado_tabla = tabla.horizontalHeader()
            encabezado_tabla.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            encabezado_tabla.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            encabezado_tabla.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            encabezado_tabla.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._armar_solapas()
        self.setMinimumSize(700, 620)
        self.ui.cmbPeriodo.currentIndexChanged.connect(self._al_cambiar_periodo)
        self.ui.btnActualizar.clicked.connect(self.actualizar)
        self.ui.btnDetalle.clicked.connect(self._abrir_detalle)
        self._armar_periodos()
        self.actualizar()
        conectar_tema(self._aplicar_temas)

    def _armar_tarjetas_qml(self) -> None:
        """Incrusta las cuatro tarjetas de métricas dibujadas en QML."""
        self._quick_tarjetas = QQuickWidget(self)
        self._quick_tarjetas.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._quick_tarjetas.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self._quick_tarjetas.setClearColor(QColor(0, 0, 0, 0))

        self._puente = PuenteTarjetas(self)
        self._quick_tarjetas.rootContext().setContextProperty("puente", self._puente)

        self._tema = puente_tema(self._quick_tarjetas)
        self._quick_tarjetas.rootContext().setContextProperty("Tema", self._tema)

        self._quick_tarjetas.setMinimumHeight(ALTO_TARJETAS_QML + ALTO_BANDA_QML)
        self._quick_tarjetas.setSource(
            QUrl.fromLocalFile(str(_ruta_qml("TarjetasEstadisticas.qml"))))
        self.ui.glyTarjetas.addWidget(self._quick_tarjetas, 0, 0, 1, 4)

        self._tema.temaCambiado.connect(self._aplicar_tema_tarjetas)

    def _aplicar_tema_tarjetas(self) -> None:
        """Recarga el QML de las tarjetas para que tome la paleta del tema activo."""
        if sip.isdeleted(self):
            return
        self._quick_tarjetas.setSource(
            QUrl.fromLocalFile(str(_ruta_qml("TarjetasEstadisticas.qml"))))

    def _armar_solapas(self) -> None:
        self.ui.solapas.currentItemChanged.connect(self._al_cambiar_solapa)
        self.ui.solapas.setCurrentItem("ventas")
        self._mostrar_solapa(0)

    def _al_cambiar_solapa(self, clave: str) -> None:
        self._mostrar_solapa(0 if clave == "ventas" else 1)

    def _mostrar_solapa(self, indice: int) -> None:
        self.ui.stackVentas.setCurrentIndex(indice)
        self.ui.btnDetalle.setVisible(indice == 0)

    def _aplicar_temas(self) -> None:
        """Repinta la ventana con los colores del tema activo."""
        if sip.isdeleted(self):
            return
        try:
            self._informar_plan()
            if self._comparacion_actual is not None:
                self.ui.lblRango.setText(
                    self._descripcion_periodo_html(self._comparacion_actual.actual))
            if self._series_actual is not None and self._comparacion_actual is not None:
                self._pintar_tarjetas(self._comparacion_actual, self._series_actual)
            self._tematizar_grafico()
        except RuntimeError:
            pass

    def al_mostrar(self) -> None:
        self._armar_periodos()
        if self._ya_mostrada:
            self.actualizar()
        self._ya_mostrada = True

    def _al_cambiar_periodo(self, _indice: int) -> None:
        if self._armando_periodos:
            return
        self._periodo_elegido = self.ui.cmbPeriodo.currentText()
        self.actualizar()

    def _opciones_periodo(self) -> list[str]:
        opciones = [HOY, MES_ACTUAL, MES_ANTERIOR, ULTIMOS_30]
        maximo = limite("dias_estadisticas")
        if maximo is None:
            return opciones + [ULTIMOS_12_MESES, TODO_EL_HISTORIAL]
        if maximo >= DIAS_12_MESES:
            return opciones + [ULTIMOS_12_MESES]
        return opciones

    def _armar_periodos(self) -> bool:
        combo = self.ui.cmbPeriodo
        opciones = self._opciones_periodo()
        actuales = [combo.itemText(i) for i in range(combo.count())]
        if actuales == opciones and combo.currentText() == self._periodo_elegido:
            self._informar_plan()
            return False
        anterior = self._periodo_elegido
        self._armando_periodos = True
        try:
            combo.clear()
            for opcion in opciones:
                combo.addItem(opcion)
            indice = combo.findText(anterior)
            if indice < 0:
                indice = combo.findText(ULTIMOS_30)
            combo.setCurrentIndex(indice)
        finally:
            self._armando_periodos = False
        self._periodo_elegido = combo.currentText()
        self._informar_plan()
        return self._periodo_elegido != anterior

    def _informar_plan(self) -> None:
        maximo = limite("dias_estadisticas")
        titulo = plan_actual().get("titulo", "Gratis")
        if maximo is None:
            texto = ""
        elif maximo >= DIAS_12_MESES:
            texto = (f"El plan {titulo} muestra 12 meses de estadísticas. "
                     "Con el plan Mensual ves todo el historial.")
        else:
            texto = (f"El plan {titulo} muestra {maximo} días de estadísticas. "
                     "Con el plan Mensual ves todo el historial.")
        if self.ui.lblPlan.text() != texto:
            self.ui.lblPlan.setText(texto)
        self.ui.lblPlan.setVisible(bool(texto))
        if maximo is not None and maximo >= DIAS_12_MESES:
            setCustomStyleSheet(
                self.ui.lblPlan,
                f"color: {AMBAR_TEXTO};",
                f"color: {OSCURO.get('alerta', AMBAR_TEXTO)};",
            )
        else:
            setCustomStyleSheet(
                self.ui.lblPlan,
                f"color: {CLARO.get('texto_suave', '#888888')};",
                f"color: {OSCURO.get('texto_suave', '#B3B3B3')};",
            )

    def _periodo(self) -> tuple[date, date]:
        hoy = date.today()
        eleccion = self.ui.cmbPeriodo.currentText()
        if eleccion == HOY:
            desde, hasta = EstadisticasVentas.del_dia(hoy)
        elif eleccion == MES_ACTUAL:
            desde, hasta = EstadisticasVentas.del_mes(hoy.year, hoy.month)
        elif eleccion == MES_ANTERIOR:
            mes, anio = (hoy.month - 1 or 12, hoy.year - 1 if hoy.month == 1 else hoy.year)
            desde, hasta = EstadisticasVentas.del_mes(anio, mes)
        elif eleccion == ULTIMOS_12_MESES:
            desde, hasta = EstadisticasVentas.ultimos_dias(DIAS_12_MESES, hoy)
        elif eleccion == TODO_EL_HISTORIAL:
            desde, hasta = self._estadisticas.todo_el_historial(hoy)
        else:
            desde, hasta = hoy - timedelta(days=29), hoy
        return self._recortar_periodo(desde, hasta)

    def _recortar_periodo(self, desde: date, hasta: date) -> tuple[date, date]:
        maximo = limite("dias_estadisticas")
        if maximo is None:
            return desde, hasta
        if (hasta - desde).days + 1 <= maximo:
            return desde, hasta
        titulo = plan_actual().get("titulo", "Gratis")
        self._aviso_limite.mostrar(
            "Límite de estadísticas",
            f"El plan {titulo} muestra los últimos {maximo} días de estadísticas",
        )
        return hasta - timedelta(days=maximo - 1), hasta

    @staticmethod
    def _texto_color_variacion(variacion: float | None, nuevo: bool = False) -> tuple[str, str]:
        if nuevo:
            return "• Nuevo", color("texto_suave")
        if variacion is None:
            return "—", color("texto_suave")
        if variacion > 0:
            return f"▲ {variacion:.1f}%", color("exito")
        if variacion < 0:
            return f"▼ {abs(variacion):.1f}%", color("error")
        return "sin cambio", color("gris_medio")

    @staticmethod
    def _pintar_variacion(etiqueta, texto: str, color_texto: str) -> None:
        """Muestra la variación de una métrica con el color del tema activo."""
        etiqueta.setText(texto)
        etiqueta.setTextColor(QColor(color_texto), QColor(color_texto))

    def _pintar_tarjetas(self, comparacion: Comparacion, series: tuple[list, list, list, list]) -> None:
        actual = comparacion.actual
        self.ui.lblVentasValor.setText(str(actual.cantidad_ventas))
        self.ui.lblUnidadesValor.setText(formatear_cantidad(actual.unidades))
        self.ui.lblTotalValor.setText(formatear_dinero(actual.total))
        self.ui.lblTicketValor.setText(formatear_dinero(actual.ticket_promedio))

        ventas_var = (
            None if actual.cantidad_ventas == comparacion.anterior.cantidad_ventas
            else self._variacion_cantidad(actual.cantidad_ventas, comparacion.anterior.cantidad_ventas)
        )
        anterior = comparacion.anterior
        texto_ventas, color_ventas = self._texto_color_variacion(
            ventas_var, anterior.cantidad_ventas == 0 and actual.cantidad_ventas > 0)
        texto_unidades, color_unidades = self._texto_color_variacion(
            comparacion.variacion_unidades, anterior.unidades == 0 and actual.unidades > 0)
        texto_total, color_total = self._texto_color_variacion(
            comparacion.variacion_total, anterior.total == 0 and actual.total > 0)
        texto_ticket, color_ticket = self._texto_color_variacion(
            comparacion.variacion_ticket_promedio,
            anterior.ticket_promedio == 0 and actual.ticket_promedio > 0)
        self._pintar_variacion(self.ui.lblVentasVariacion, texto_ventas, color_ventas)
        self._pintar_variacion(self.ui.lblUnidadesVariacion, texto_unidades, color_unidades)
        self._pintar_variacion(self.ui.lblTotalVariacion, texto_total, color_total)
        self._pintar_variacion(self.ui.lblTicketVariacion, texto_ticket, color_ticket)
        self._puente.actualizar(
            str(actual.cantidad_ventas),
            texto_ventas,
            color_ventas,
            formatear_cantidad(actual.unidades),
            texto_unidades,
            color_unidades,
            formatear_dinero(actual.total),
            texto_total,
            color_total,
            formatear_dinero(actual.ticket_promedio),
            texto_ticket,
            color_ticket,
        )
        self._pintar_detalles(comparacion.actual, series)

    def _pintar_detalles(self, resumen: ResumenPeriodo, series: tuple[list, list, list, list]) -> None:
        serie_ventas, serie_unidades, serie_facturado, serie_ticket = series
        dias_periodo = len(serie_ventas)
        dias_con_ventas = sum(1 for valor in serie_ventas if valor > 0)
        detalles = (
            self._detalle_serie(serie_ventas, False),
            self._detalle_cantidades(serie_unidades),
            self._detalle_serie(serie_facturado, True),
            self._detalle_serie([v for v in serie_ticket if v > 0], True),
        )
        for detalle in detalles:
            detalle["diasConVentas"] = dias_con_ventas
            detalle["diasPeriodo"] = dias_periodo
        self._puente.actualizar_detalles(
            detalles[0],
            detalles[1],
            detalles[2],
            detalles[3],
            self._rango_periodo(resumen),
        )
        etiquetas = (
            self.ui.lblVentasDetalle,
            self.ui.lblUnidadesDetalle,
            self.ui.lblTotalDetalle,
            self.ui.lblTicketDetalle,
        )
        for etiqueta, detalle in zip(etiquetas, detalles):
            etiqueta.setText(
                f"Máx {detalle['maximo']} · Mín {detalle['minimo']} · Prom {detalle['promedio']}")

    @staticmethod
    def _detalle_serie(serie: list, dinero: bool) -> dict:
        valores = [float(valor) for valor in serie]
        if not valores:
            return {"maximo": "—", "minimo": "—", "promedio": "—"}
        maximo = max(valores)
        minimo = min(valores)
        promedio = sum(valores) / len(valores)
        if dinero:
            return {
                "maximo": formatear_dinero(maximo),
                "minimo": formatear_dinero(minimo),
                "promedio": formatear_dinero(promedio),
            }
        return {
            "maximo": _numero(maximo, 0),
            "minimo": _numero(minimo, 0),
            "promedio": _numero(promedio, 1),
        }

    @staticmethod
    def _detalle_cantidades(serie: list) -> dict:
        valores = [float(valor) for valor in serie]
        if not valores:
            return {"maximo": "—", "minimo": "—", "promedio": "—"}
        return {
            "maximo": formatear_cantidad(max(valores)),
            "minimo": formatear_cantidad(min(valores)),
            "promedio": formatear_cantidad(sum(valores) / len(valores)),
        }

    @staticmethod
    def _rango_periodo(resumen: ResumenPeriodo) -> str:
        desde, hasta = resumen.desde, resumen.hasta
        if desde == hasta:
            return f"Período del {desde.strftime('%d/%m/%Y')}"
        return f"Período del {desde.strftime('%d/%m/%Y')} al {hasta.strftime('%d/%m/%Y')}"

    @staticmethod
    def _variacion_cantidad(actual: int, anterior: int) -> float | None:
        if anterior == 0:
            return None
        return (actual - anterior) / anterior * 100

    def _descripcion_periodo_html(self, resumen: ResumenPeriodo) -> str:
        desde, hasta = resumen.desde, resumen.hasta
        rango = desde.strftime("%d/%m/%Y") if desde == hasta else (
            f"{desde.strftime('%d/%m/%Y')} al {hasta.strftime('%d/%m/%Y')}"
        )
        return (
            f'<b><span style="color:{color("texto")};">Del {rango}.</span></b> '
            f'<span style="color:{color("gris_medio")};">'
            "Se compara contra el período anterior de igual duración.</span>"
        )

    def actualizar(self, _indice=None) -> None:
        self.setUpdatesEnabled(False)
        try:
            desde, hasta = self._periodo()
            try:
                comparacion = self._estadisticas.comparar(desde, hasta)
                sin_licencia = False
            except PermissionError:
                sin_licencia = True
                resumen = self._estadisticas.resumen(desde, hasta)
                comparacion = Comparacion(actual=resumen, anterior=resumen)
            self._comparacion_actual = comparacion
            self.ui.lblRango.setText(self._descripcion_periodo_html(comparacion.actual))
            if sin_licencia:
                self.ui.lblRango.setToolTip(
                    "La comparación con el período anterior es una función premium. "
                    "Consulte los planes disponibles en Ajustes.")
            else:
                self.ui.lblRango.setToolTip("")
            series = self._series_diarias(desde, hasta)
            self._series_actual = series
            self._pintar_tarjetas(comparacion, series)
            self._puente.actualizar_series(*series)
            self._pintar_grafico(desde, hasta, comparacion)
            self._cargar_ventas(desde, hasta)
            self._pintar_ranking(desde, hasta, comparacion.actual.total)
        finally:
            self.setUpdatesEnabled(True)
        if self._armar_periodos():
            self.actualizar()

    def _series_diarias(self, desde: date, hasta: date) -> tuple[list, list, list, list]:
        dias = [desde + timedelta(days=i) for i in range((hasta - desde).days + 1)]
        ventas = {dia: 0 for dia in dias}
        unidades = {dia: 0 for dia in dias}
        facturado = {dia: 0.0 for dia in dias}
        for venta in self._estadisticas.ventas_del_periodo(desde, hasta):
            if venta.anulada or venta.fecha not in ventas:
                continue
            ventas[venta.fecha] += 1
            unidades[venta.fecha] += venta.unidades
            facturado[venta.fecha] = round(facturado[venta.fecha] + venta.total, 2)
        serie_ventas = [ventas[dia] for dia in dias]
        serie_unidades = [unidades[dia] for dia in dias]
        serie_facturado = [facturado[dia] for dia in dias]
        serie_ticket = [round(facturado[dia] / ventas[dia], 2) if ventas[dia] else 0.0 for dia in dias]
        return serie_ventas, serie_unidades, serie_facturado, serie_ticket

    def _pintar_grafico(self, desde: date, hasta: date, comparacion: Comparacion) -> None:
        if desde == hasta:
            pares = self._ventas_por_hora(desde)
            titulo = "Ventas por hora"
        elif (hasta - desde).days + 1 > DIAS_POR_BARRA:
            try:
                pares = [(dia.strftime("%m/%y"), valor)
                         for dia, valor in self._estadisticas.total_por_mes(desde, hasta)]
            except PermissionError:
                pares = [(f"{dia.day:02d}", valor)
                         for dia, valor in self._estadisticas.total_por_dia(desde, hasta)]
            titulo = "Ventas por mes"
        else:
            pares = [(f"{dia.day:02d}", valor)
                     for dia, valor in self._estadisticas.total_por_dia(desde, hasta)]
            titulo = "Ventas por día"
        if self._grafico is None:
            self._grafico = GraficoVentas(pares, comparacion.variacion_total, titulo)
            self.ui.lyGrafico.addWidget(self._grafico)
        else:
            self._grafico.actualizar_puntos(pares, comparacion.variacion_total, titulo)
        self._tematizar_grafico()

    def _tematizar_grafico(self) -> None:
        """Adapta los colores del gráfico de matplotlib al tema activo."""
        if self._grafico is None:
            return
        fondo = color("fondo_tarjeta")
        self._grafico._fig.set_facecolor(fondo)
        self._grafico._ax.set_facecolor(fondo)
        self._grafico._ax.title.set_color(color("texto"))
        self._grafico._ax.tick_params(axis="both", colors=color("gris_medio"))
        for borde in self._grafico._ax.spines.values():
            borde.set_color(color("borde_suave"))
        self._grafico._canvas.draw_idle()

    def _ventas_por_hora(self, dia: date) -> list[tuple[str, float]]:
        por_hora = {hora: 0.0 for hora in range(24)}
        for venta in self._estadisticas.ventas_del_periodo(dia, dia):
            if venta.anulada:
                continue
            try:
                hora = int(venta.hora[:2])
            except ValueError:
                continue
            if 0 <= hora <= 23:
                por_hora[hora] = round(por_hora[hora] + venta.total, 2)
        return [(f"{hora:02d}", por_hora[hora]) for hora in range(24)]

    def _cargar_ventas(self, desde: date, hasta: date) -> None:
        self._ventas_mostradas = self._estadisticas.ventas_del_periodo(desde, hasta)
        filas = [
            [
                f"{v.fecha_texto} {v.hora}",
                formatear_cantidad(v.unidades),
                formatear_dinero(v.total),
                medio_pago.nombre_de(v.medio_pago),
                ", ".join(f"{r.nombre} x{formatear_cantidad(r.cantidad)}" for r in v.detalle),
                "ANULADA" if v.anulada else "",
            ]
            for v in self._ventas_mostradas
        ]
        colores = [color("error") if v.anulada else None for v in self._ventas_mostradas]
        self.llenar_tabla(self.ui.tblVentas, filas, colores)
        self._avisar_ventas_ilegibles()

    def _pintar_ranking(self, desde: date, hasta: date, total: float) -> None:
        filas = [
            [
                producto.nombre,
                formatear_cantidad(producto.unidades),
                formatear_dinero(producto.total),
                self._porcentaje(producto.total, total),
            ]
            for producto in self._estadisticas.mas_vendidos(desde, hasta)
        ]
        self.llenar_tabla(self.ui.tblRanking, filas)

    @staticmethod
    def _porcentaje(parcial: float, total: float) -> str:
        if not total:
            return "—"
        return f"{_numero(parcial / total * 100)} %"

    def _avisar_ventas_ilegibles(self) -> None:
        nuevos = [
            error for error in self._estadisticas.errores_lectura()
            if error["id"] not in self._avisadas_lectura
        ]
        if not nuevos:
            return
        for error in nuevos:
            self._avisadas_lectura.add(error["id"])
        fechas = ", ".join(f"{error['fecha']} {error['hora']}" for error in nuevos[:3])
        self._aviso_ventas_ilegibles.mostrar(
            "Ventas ilegibles",
            f"No se pudieron leer {len(nuevos)} venta(s) ({fechas}). No están en el "
            "historial ni en las estadísticas hasta que se reparen.",
        )

    def _abrir_detalle(self, _item=None) -> None:
        fila = self._fila_seleccionada()
        if fila is None:
            self.mostrar_advertencia("Detalles", "Seleccioná una venta de la tabla.")
            return
        VentanaDetalleVenta(
            self._ventas_mostradas[fila], self, self._anulaciones).exec()

    def _fila_seleccionada(self) -> int | None:
        seleccionadas = sorted({i.row() for i in self.ui.tblVentas.selectedIndexes()})
        if not seleccionadas:
            return None
        return seleccionadas[0] if seleccionadas[0] < len(self._ventas_mostradas) else None
