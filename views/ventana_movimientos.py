from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.movimiento import MOTIVO_DEVOLUCION_PREFIJO
from services.gestor_stock import GestorStock
from ui.generated.movimientos_ui import Ui_Form as Ui_MovimientosForm
from utils.formato import formatear_cantidad
from views.ventana_base import VentanaBase


class VentanaMovimientos(QWidget, VentanaBase):
    ir_a_reportes = pyqtSignal()
    ir_a_clientes = pyqtSignal()

    def __init__(self, gestor_stock: GestorStock) -> None:
        super().__init__()
        self._gestor_stock = gestor_stock
        self.ui = Ui_MovimientosForm()
        self.ui.setupUi(self)
        self._acomodar_widgets()
        self.ui.tblHistorial.setHorizontalHeaderItem(1, QTableWidgetItem("Cantidad"))
        self._cargar_motivos()
        self.cargar_historial()

    def _acomodar_widgets(self) -> None:
        self.ui.frame.setVisible(False)
        self.ui.label_2.setVisible(False)
        botones = QHBoxLayout()
        btn_reportes = QPushButton("Ver reportes")
        btn_clientes = QPushButton("Cuentas de clientes")
        btn_reportes.clicked.connect(self.ir_a_reportes.emit)
        btn_clientes.clicked.connect(self.ir_a_clientes.emit)
        botones.addWidget(btn_reportes)
        botones.addWidget(btn_clientes)
        self.cmbMotivo = QComboBox()
        self.cmbMotivo.setObjectName("cmbMotivo")
        self.cmbMotivo.currentIndexChanged.connect(self.cargar_historial)
        filtro = QHBoxLayout()
        filtro.addWidget(QLabel("Motivo:"))
        filtro.addWidget(self.cmbMotivo, 1)
        self.ui.gridLayout_2.addLayout(filtro, 0, 0, 1, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 10, 16, 19)
        layout.addLayout(botones)
        layout.addWidget(self.ui.frame_2, 1)
        self.estirar_columnas(self.ui.tblHistorial)
        self.setMinimumSize(560, 480)

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

    def cargar_historial(self) -> None:
        motivo = self.cmbMotivo.currentData() or ""
        filas = [
            [m.fecha_texto, formatear_cantidad(m.cantidad), m.codigo_producto, m.tipo,
             m.motivo]
            for m in self._gestor_stock.listar_movimientos_recientes(motivo)
        ]
        self.llenar_tabla(self.ui.tblHistorial, filas)
