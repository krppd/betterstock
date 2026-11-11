from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    FluentIcon as FIF,
    FluentIconBase,
    PushButton,
    SubtitleLabel,
    TableWidget,
    isDarkTheme,
)

from models.movimiento import MOTIVO_DEVOLUCION_PREFIJO
from services.gestor_stock import GestorStock
from utils.formato import formatear_cantidad
from views.ventana_base import VentanaBase


class _FluentComboBox(ComboBox):
    """ComboBox adaptado a la firma estándar de Qt addItem(text, userData)."""

    def addItem(self, text: str, icon_or_data: Any = None, userData: Any = None) -> None:
        if userData is None and icon_or_data is not None:
            if not isinstance(icon_or_data, (QIcon, FluentIconBase)):
                super().addItem(text, userData=icon_or_data)
                return
        super().addItem(text, icon=icon_or_data, userData=userData)


class _UiCompat:
    """Proxy de compatibilidad para evitar roturas en código o tests que inspeccionen self.ui."""

    def __init__(self, tbl_historial: TableWidget) -> None:
        self.tblHistorial = tbl_historial
        self.frame = QFrame()
        self.frame.setVisible(False)
        self.frame_2 = QFrame()
        self.label = QLabel("Historial")
        self.label_2 = QLabel()
        self.label_2.setVisible(False)
        self.gridLayout_2 = QGridLayout(self.frame_2)


class VentanaMovimientos(QWidget, VentanaBase):
    ir_a_reportes = pyqtSignal()
    ir_a_clientes = pyqtSignal()

    def __init__(self, gestor_stock: GestorStock) -> None:
        super().__init__()
        self._gestor_stock = gestor_stock
        self._iniciar_interfaz()
        self.ui.tblHistorial.setHorizontalHeaderItem(1, QTableWidgetItem("Cantidad"))
        self._cargar_motivos()
        self.cargar_historial()

    def _iniciar_interfaz(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(24, 20, 24, 20)
        layout_principal.setSpacing(14)

        barra_superior = QHBoxLayout()
        barra_superior.setSpacing(10)

        titulo = SubtitleLabel("Historial de movimientos", self)
        barra_superior.addWidget(titulo)
        barra_superior.addStretch(1)

        self.btn_reportes = PushButton(FIF.PIE_SINGLE, "Ver reportes", self)
        self.btn_clientes = PushButton(FIF.PEOPLE, "Cuentas de clientes", self)

        self.btn_reportes.clicked.connect(self.ir_a_reportes.emit)
        self.btn_clientes.clicked.connect(self.ir_a_clientes.emit)

        barra_superior.addWidget(self.btn_reportes)
        barra_superior.addWidget(self.btn_clientes)
        layout_principal.addLayout(barra_superior)

        tarjeta = CardWidget(self)
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(16, 16, 16, 16)
        layout_tarjeta.setSpacing(12)

        layout_filtro = QHBoxLayout()
        layout_filtro.setSpacing(8)
        lbl_motivo = BodyLabel("Motivo:", tarjeta)
        self.cmbMotivo = _FluentComboBox(tarjeta)
        self.cmbMotivo.setObjectName("cmbMotivo")
        self.cmbMotivo.setMinimumWidth(220)
        self.cmbMotivo.currentIndexChanged.connect(self.cargar_historial)

        layout_filtro.addWidget(lbl_motivo)
        layout_filtro.addWidget(self.cmbMotivo)
        layout_filtro.addStretch(1)
        layout_tarjeta.addLayout(layout_filtro)

        self.tblHistorial = TableWidget(tarjeta)
        self.tblHistorial.setObjectName("tblHistorial")
        self.tblHistorial.setColumnCount(5)
        self.tblHistorial.setHorizontalHeaderLabels(["Fecha", "Cantidad", "Producto", "Tipo", "Motivo"])
        self.tblHistorial.setBorderVisible(True)
        self.tblHistorial.setBorderRadius(8)
        self.tblHistorial.setWordWrap(False)

        layout_tarjeta.addWidget(self.tblHistorial, 1)
        layout_principal.addWidget(tarjeta, 1)

        self.ui = _UiCompat(self.tblHistorial)
        self.estirar_columnas(self.ui.tblHistorial)
        self.setMinimumSize(560, 480)

    def _acomodar_widgets(self) -> None:
        """Compatibilidad con versiones anteriores."""
        pass

    def _cargar_motivos(self) -> None:
        actual = self.cmbMotivo.currentData() or ""
        self.cmbMotivo.blockSignals(True)
        self.cmbMotivo.clear()
        self.cmbMotivo.addItem("Todos los motivos", "")
        if self._gestor_stock.hay_devoluciones_en_movimientos():
            self.cmbMotivo.addItem(MOTIVO_DEVOLUCION_PREFIJO, MOTIVO_DEVOLUCION_PREFIJO)
        for motivo in self._gestor_stock.motivos_de_movimientos():
            self.cmbMotivo.addItem(motivo, motivo)
        indice = self.cmbMotivo.findData(actual)
        self.cmbMotivo.setCurrentIndex(max(indice, 0))
        self.cmbMotivo.blockSignals(False)

    def al_mostrar(self) -> None:
        self._cargar_motivos()
        self.cargar_historial()

    def cargar_historial(self, *_args: Any) -> None:
        motivo = self.cmbMotivo.currentData() or ""
        movimientos = self._gestor_stock.listar_movimientos_recientes(motivo)
        filas = [
            [m.fecha_texto, formatear_cantidad(m.cantidad), m.codigo_producto, m.tipo,
             m.motivo]
            for m in movimientos
        ]
        self.llenar_tabla(self.ui.tblHistorial, filas)

        oscuro = isDarkTheme()
        color_entrada = "#4caf50" if oscuro else "#2e7d32"
        color_salida = "#ff6b6b" if oscuro else "#c62828"
        color_ajuste = "#64b5f6" if oscuro else "#1565c0"

        for i, m in enumerate(movimientos):
            item_tipo = self.ui.tblHistorial.item(i, 3)
            if item_tipo:
                if m.tipo == "Entrada":
                    item_tipo.setForeground(QBrush(QColor(color_entrada)))
                elif m.tipo == "Salida":
                    item_tipo.setForeground(QBrush(QColor(color_salida)))
                elif m.tipo == "Ajuste":
                    item_tipo.setForeground(QBrush(QColor(color_ajuste)))

            if MOTIVO_DEVOLUCION_PREFIJO in m.motivo:
                item_motivo = self.ui.tblHistorial.item(i, 4)
                if item_motivo:
                    item_motivo.setForeground(QBrush(QColor(color_salida)))
