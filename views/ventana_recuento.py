from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    TableWidget,
    TransparentPushButton,
    qconfig,
)

from models.producto import Producto
from services.excepciones import ErrorNegocio
from services.gestor_stock import GestorStock
from services.recuento import ServicioRecuento
from ui.estilos import TAMANO_SMALL, fuente
from ui.fluent import color
from ui.widgets.notificacion import Notificacion
from utils.formato import es_cantidad, formatear_cantidad, redondear_cantidad
from views.ventana_base import VentanaBase


class VentanaRecuento(QDialog, VentanaBase):
    """Carga de conteos de inventario y aplicación de las diferencias."""

    COLUMNA_CONTADO = 3
    COLUMNA_DIFERENCIA = 4
    MAXIMO_DIFERENCIAS_EN_RESUMEN = 10

    def __init__(self, gestor_stock: GestorStock, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._gestor_stock = gestor_stock
        self._servicio = ServicioRecuento(gestor_stock)
        self._productos: list[Producto] = []
        self._conteos: dict[str, str] = {}
        self.setWindowTitle("Recuento de inventario")
        self.setMinimumSize(760, 480)
        self.resize(900, 580)
        self._armar_interfaz()
        self.cargar_productos()

    def _armar_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.txtBuscar = SearchLineEdit(self)
        self.txtBuscar.setPlaceholderText("Buscar por código o nombre")
        layout.addWidget(self.txtBuscar)

        ayuda = BodyLabel(
            "Ingresá la cantidad contada. Solo se aplican las filas con un conteo cargado.",
            self)
        ayuda.setWordWrap(True)
        layout.addWidget(ayuda)

        self.tabla = TableWidget(self)
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["Código", "Producto", "Stock sistema", "Contado", "Diferencia"])
        self.tabla.setBorderRadius(8)
        self.tabla.setBorderVisible(True)
        self.tabla.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.AnyKeyPressed)
        self.tabla.verticalHeader().setVisible(False)
        self.estirar_columnas(self.tabla)
        encabezado = self.tabla.horizontalHeader()
        for columna in (0, 2, 3, 4):
            encabezado.setSectionResizeMode(
                columna, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tabla, 1)

        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnLimpiar = TransparentPushButton(FIF.SYNC, "Limpiar conteos", self)
        self.btnCerrar = PushButton("Cerrar", self)
        self.btnAplicar = PrimaryPushButton(FIF.ACCEPT, "Aplicar recuento", self)
        self.btnAplicar.setObjectName("btnGuardar")
        for boton in (self.btnLimpiar, self.btnCerrar, self.btnAplicar):
            boton.setAutoDefault(False)
        botones.addWidget(self.btnLimpiar)
        botones.addStretch(1)
        botones.addWidget(self.btnCerrar)
        botones.addWidget(self.btnAplicar)
        layout.addLayout(botones)

        self.txtBuscar.textChanged.connect(self.cargar_productos)
        self.txtBuscar.searchSignal.connect(self.cargar_productos)
        self.tabla.itemChanged.connect(self._al_editar_conteo)
        self.btnLimpiar.clicked.connect(self.limpiar_conteos)
        self.btnCerrar.clicked.connect(self.reject)
        self.btnAplicar.clicked.connect(self.aplicar_recuento)
        qconfig.themeChanged.connect(self._repintar_colores)

    def _repintar_colores(self) -> None:
        """Repinta la tabla con los colores del tema, sin volver a consultar la base."""
        for fila in range(self.tabla.rowCount()):
            self._colorear_diferencia(self.tabla.item(fila, 3))

    def cargar_productos(self) -> None:
        self._productos = self._gestor_stock.buscar_productos(self.txtBuscar.text())
        self.tabla.blockSignals(True)
        try:
            self.tabla.setRowCount(0)
            for fila, producto in enumerate(self._productos):
                self.tabla.insertRow(fila)
                self._poner_item(fila, 0, producto.codigo)
                self._poner_item(fila, 1, producto.nombre)
                self._poner_item(
                    fila, 2, formatear_cantidad(producto.stock_actual),
                    tabular=True, alinear_derecha=True)
                self._poner_item(
                    fila, self.COLUMNA_CONTADO, self._conteos.get(producto.codigo, ""),
                    tabular=True, alinear_derecha=True, editable=True)
                self._poner_item(
                    fila, self.COLUMNA_DIFERENCIA,
                    self._texto_diferencia(producto, self._conteos.get(producto.codigo, "")),
                    tabular=True, alinear_derecha=True)
                self._colorear_diferencia(
                    self.tabla.item(fila, self.COLUMNA_DIFERENCIA))
        finally:
            self.tabla.blockSignals(False)

    def _poner_item(
        self,
        fila: int,
        columna: int,
        texto: str,
        *,
        tabular: bool = False,
        alinear_derecha: bool = False,
        editable: bool = False,
    ) -> QTableWidgetItem:
        item = QTableWidgetItem(texto)
        item.setFont(fuente(TAMANO_SMALL, tabular=tabular))
        item.setToolTip(texto)
        if alinear_derecha:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.tabla.setItem(fila, columna, item)
        return item

    def _al_editar_conteo(self, item: QTableWidgetItem) -> None:
        if item.column() != self.COLUMNA_CONTADO:
            return
        codigo_item = self.tabla.item(item.row(), 0)
        if codigo_item is None:
            return
        codigo = codigo_item.text()
        texto = item.text().strip()
        if texto:
            self._conteos[codigo] = texto
        else:
            self._conteos.pop(codigo, None)
        self._actualizar_diferencia(item.row())

    def _actualizar_diferencia(self, fila: int) -> None:
        codigo_item = self.tabla.item(fila, 0)
        diferencia_item = self.tabla.item(fila, self.COLUMNA_DIFERENCIA)
        if codigo_item is None or diferencia_item is None:
            return
        producto = next(
            (p for p in self._productos if p.codigo == codigo_item.text()), None)
        diferencia_item.setText(
            self._texto_diferencia(producto, self._conteos.get(codigo_item.text(), "")))
        self._colorear_diferencia(diferencia_item)

    def _texto_diferencia(self, producto: Producto | None, texto: str) -> str:
        if producto is None or not texto.strip():
            return ""
        if not es_cantidad(texto):
            return "Inválido"
        return self._formatear_diferencia(
            redondear_cantidad(texto) - redondear_cantidad(producto.stock_actual))

    def _formatear_diferencia(self, diferencia: float) -> str:
        diferencia = redondear_cantidad(diferencia)
        if diferencia == 0:
            return "0"
        signo = "+" if diferencia > 0 else "-"
        return f"{signo}{formatear_cantidad(abs(diferencia))}"

    def _colorear_diferencia(self, item: QTableWidgetItem | None) -> None:
        if item is None:
            return
        texto = item.text()
        if texto == "Inválido" or texto.startswith("-"):
            item.setForeground(QBrush(QColor(color("error"))))
        elif texto.startswith("+"):
            item.setForeground(QBrush(QColor(color("exito"))))
        elif texto == "0":
            item.setForeground(QBrush(QColor(color("gris_medio"))))
        else:
            item.setData(Qt.ItemDataRole.ForegroundRole, None)

    def _leer_conteos(self) -> dict[str, float] | None:
        conteos: dict[str, float] = {}
        negativos: list[str] = []
        invalidos: list[str] = []
        for codigo, texto in self._conteos.items():
            texto = texto.strip()
            if not texto:
                continue
            if es_cantidad(texto):
                conteos[codigo] = redondear_cantidad(texto)
            elif redondear_cantidad(texto) < 0:
                negativos.append(codigo)
            else:
                invalidos.append(codigo)
        problemas: list[str] = []
        if negativos:
            problemas.append(
                "Los siguientes conteos no pueden ser negativos: "
                + ", ".join(sorted(negativos)))
        if invalidos:
            problemas.append(
                "Los siguientes conteos no son números válidos: "
                + ", ".join(sorted(invalidos)))
        if problemas:
            self.mostrar_advertencia("Recuento", "\n".join(problemas))
            return None
        if not conteos:
            self.mostrar_advertencia("Recuento", "No hay conteos cargados para aplicar.")
            return None
        return conteos

    def _cambios(self, conteos: dict[str, float]) -> list[tuple[Producto, float]]:
        productos = self._gestor_stock.productos_por_codigo()
        cambios: list[tuple[Producto, float]] = []
        for codigo, contado in conteos.items():
            producto = productos.get(codigo)
            if producto is not None and redondear_cantidad(producto.stock_actual) != contado:
                cambios.append((producto, contado))
        return cambios

    def _armar_resumen(self, cambios: list[tuple[Producto, float]]) -> str:
        cantidad = len(cambios)
        encabezado = (
            f"Se va a actualizar {cantidad} producto."
            if cantidad == 1
            else f"Se van a actualizar {cantidad} productos.")
        lineas = [encabezado, ""]
        for producto, contado in cambios[:self.MAXIMO_DIFERENCIAS_EN_RESUMEN]:
            lineas.append(
                f"• {producto.codigo} - {producto.nombre}: "
                f"{formatear_cantidad(producto.stock_actual)} → "
                f"{formatear_cantidad(contado)} "
                f"({self._formatear_diferencia(contado - producto.stock_actual)})")
        if cantidad > self.MAXIMO_DIFERENCIAS_EN_RESUMEN:
            lineas.append(f"+{cantidad - self.MAXIMO_DIFERENCIAS_EN_RESUMEN} más")
        return "\n".join(lineas)

    def aplicar_recuento(self) -> None:
        conteos = self._leer_conteos()
        if conteos is None:
            return
        cambios = self._cambios(conteos)
        if not cambios:
            self.mostrar_informacion(
                "Recuento", "Los conteos cargados coinciden con el stock del sistema.")
            return
        if not self.confirmar("Aplicar recuento", self._armar_resumen(cambios)):
            return
        try:
            movimientos = self._servicio.aplicar(conteos)
        except ErrorNegocio as error:
            self.mostrar_advertencia("Error", str(error))
            return
        self._conteos.clear()
        self.cargar_productos()
        cantidad = len(movimientos)
        mensaje = (
            "Se actualizó 1 producto."
            if cantidad == 1
            else f"Se actualizaron {cantidad} productos.")
        Notificacion(self).mostrar("Recuento aplicado", mensaje)

    def limpiar_conteos(self) -> None:
        self._conteos.clear()
        self.cargar_productos()
