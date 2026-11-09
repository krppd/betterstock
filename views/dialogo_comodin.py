from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from models.venta import validar_descripcion_comodin
from ui.estilos import TAMANO_BODY, fuente
from ui.manual.campo_cantidad import CampoCantidad
from utils.formato import formatear_cantidad, formatear_dinero
from views.ventana_base import VentanaBase

PRECISION_PRECIO = 2
MAXIMO_CANTIDAD = 9999.999
MAXIMO_PRECIO = 99999999.0
MAXIMO_DESCRIPCION = 80


class DialogoComodin(QDialog, VentanaBase):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ítem comodín")

        self.txtDescripcion = QLineEdit(self)
        self.txtDescripcion.setPlaceholderText("Ej: pila AA recargada")
        self.txtDescripcion.setMaxLength(MAXIMO_DESCRIPCION)
        self.spnCantidad = CampoCantidad(self)
        self.spnCantidad.setMaximum(MAXIMO_CANTIDAD)
        self.spnCantidad.setValue(1)
        self.spnPrecio = QDoubleSpinBox(self)
        self.spnPrecio.setRange(0.0, MAXIMO_PRECIO)
        self.spnPrecio.setDecimals(PRECISION_PRECIO)
        self.spnPrecio.setSingleStep(100.0)
        self.spnPrecio.setGroupSeparatorShown(True)
        self.spnPrecio.setPrefix("$ ")

        formulario = QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.setVerticalSpacing(10)
        formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        formulario.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        formulario.addRow("Descripción:", self.txtDescripcion)
        formulario.addRow("Cantidad:", self.spnCantidad)
        formulario.addRow("Precio unitario:", self.spnPrecio)

        self.lblSubtotal = QLabel(self)
        self.lblSubtotal.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        self.lblSubtotal.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.btnAgregar = self.botones.button(QDialogButtonBox.StandardButton.Ok)
        self.btnAgregar.setText("Agregar")
        self.btnAgregar.setDefault(True)
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setAutoDefault(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(formulario)
        layout.addWidget(self.lblSubtotal)
        layout.addWidget(self.botones)

        self.txtDescripcion.textChanged.connect(self.actualizar)
        self.spnCantidad.textChanged.connect(self.actualizar)
        self.spnPrecio.valueChanged.connect(self.actualizar)
        self.botones.accepted.connect(self.aceptar)
        self.botones.rejected.connect(self.reject)
        self.actualizar()

        self.setMinimumWidth(380)
        self.txtDescripcion.setFocus()

    @property
    def descripcion(self) -> str:
        return self.txtDescripcion.text().strip()

    @property
    def cantidad(self) -> float:
        return self.spnCantidad.value()

    @property
    def precio_unitario(self) -> float:
        return self.spnPrecio.value()

    @property
    def resultado(self) -> tuple[str, float, float]:
        return self.descripcion, self.cantidad, self.precio_unitario

    def subtotal(self) -> float:
        return self.cantidad * self.precio_unitario

    def actualizar(self, *_args: object) -> None:
        self.lblSubtotal.setText(f"Subtotal: {formatear_dinero(self.subtotal())}")
        self.btnAgregar.setEnabled(bool(self.descripcion))

    def aceptar(self) -> None:
        try:
            validar_descripcion_comodin(self.descripcion)
        except ValueError as error:
            self.mostrar_advertencia("Comodín", str(error))
            self.txtDescripcion.setFocus()
            return
        if not self.spnCantidad.es_valido() or self.cantidad <= 0:
            self.mostrar_advertencia("Comodín", "La cantidad debe ser mayor a 0.")
            self.spnCantidad.setFocus()
            return
        if self.cantidad > MAXIMO_CANTIDAD:
            self.mostrar_advertencia(
                "Comodín",
                f"La cantidad no puede superar {formatear_cantidad(MAXIMO_CANTIDAD)} unidades.")
            self.spnCantidad.setFocus()
            return
        self.accept()