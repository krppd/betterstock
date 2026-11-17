from __future__ import annotations

from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget

from models.usuario import Usuario
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_stock import GestorStock
from ui.estilos import TAMANO_SMALL, fuente
from ui.generated.reportes_ui import Ui_Form as Ui_ReportesForm
from utils.formato import formatear_cantidad, formatear_dinero
from views.ventana_base import VentanaBase


class VentanaReportes(QWidget, VentanaBase):
    """Reportes de movimientos por rango de fechas."""

    def __init__(
        self, gestor_stock: GestorStock,
        estadisticas: EstadisticasVentas | None = None,
        permiso: str = Usuario.PERMISO_ADMIN,
    ) -> None:
        super().__init__()
        self._gestor_stock = gestor_stock
        self._estadisticas = estadisticas
        self._admin = Usuario.es_admin(permiso)
        self.ui = Ui_ReportesForm()
        self.ui.setupUi(self)
        self.estirar_columnas(self.ui.tableWidget)
        self.ui.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ui.tableWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMinimumSize(565, 350)
        self.ui.dateDesde.setDate(QtCore.QDate.currentDate().addDays(-30))
        self.ui.dateHasta.setDate(QtCore.QDate.currentDate())
        self.ui.btnFiltrar.clicked.connect(self.filtrar_reportes)

        self.ui.lblTotal.setFont(fuente(TAMANO_SMALL, negrita=True, tabular=True))
        self.ui.lblTotal.setVisible(self._admin)

        self.filtrar_reportes()

    def al_mostrar(self) -> None:
        self.filtrar_reportes()

    def filtrar_reportes(self) -> None:
        productos = self._gestor_stock.productos_por_codigo()
        movimientos = self._gestor_stock.filtrar_movimientos(
            desde=self.ui.dateDesde.date().toPyDate(),
            hasta=self.ui.dateHasta.date().toPyDate(),
            tipo=self.ui.cmbTipo.currentText(),
        )

        filas = []
        for m in movimientos:
            producto = productos.get(m.codigo_producto)
            nombre = producto.nombre if producto else "Desconocido"
            precio = producto.precio_venta if producto else 0.0
            filas.append([m.fecha_texto, nombre, m.tipo, formatear_cantidad(m.cantidad),
                          formatear_dinero(precio)])
        self.llenar_tabla(self.ui.tableWidget, filas)

        total = self._gestor_stock.stock_valorizado()
        self.ui.lblTotal.setText(
            f"Stock total valorizado: {formatear_dinero(total)}" if self._admin else "")
