from __future__ import annotations

from PyQt6 import QtCore
from PyQt6.QtWidgets import QHeaderView, QWidget
from qfluentwidgets import qconfig

from services.gestor_stock import GestorStock
from ui.generated.alertas_ui import Ui_Form as Ui_AlertasForm
from utils.formato import formatear_cantidad
from views.ventana_base import VentanaBase


class VentanaAlertas(QWidget, VentanaBase):
    """Muestra los productos bajo stock mínimo."""

    def __init__(self, gestor_stock: GestorStock) -> None:
        super().__init__()
        self._gestor_stock = gestor_stock
        self.ui = Ui_AlertasForm()
        self.ui.setupUi(self)
        self._acomodar(self.ui.tblAlertas, (0, 2, 3))
        self.ui.verticalLayout.setStretch(1, 1)
        self.setMinimumSize(480, 420)
        self.ui.btnExportar.setVisible(False)
        self.ui.btnExportarVencimientos.setVisible(False)
        self.ui.lblVencimientos.setVisible(False)
        self.ui.tblVencimientos.setVisible(False)

        if hasattr(qconfig, "themeChanged"):
            qconfig.themeChanged.connect(self.cargar_alertas)

        self.cargar_alertas()

    @staticmethod
    def _acomodar(tabla, ajustadas: tuple[int, ...]) -> None:
        VentanaBase.estirar_columnas(tabla)
        encabezado = tabla.horizontalHeader()
        for columna in ajustadas:
            encabezado.setSectionResizeMode(
                columna, QHeaderView.ResizeMode.ResizeToContents)
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabla.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tabla.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def al_mostrar(self) -> None:
        self.cargar_alertas()

    def cargar_alertas(self) -> None:
        self._cargar_stock()

    def _cargar_stock(self) -> None:
        filas = [
            [p.codigo, p.nombre, formatear_cantidad(p.stock_actual),
             formatear_cantidad(p.stock_minimo)]
            for p in self._gestor_stock.productos_criticos()
        ]
        self.llenar_tabla(self.ui.tblAlertas, filas)
