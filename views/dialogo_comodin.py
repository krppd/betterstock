"""Diálogo para cargar un ítem comodín en la venta."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    DoubleSpinBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
)

from models.venta import validar_descripcion_comodin
from ui.estilos import TAMANO_BODY, fuente
from ui.fluent import color
from utils.formato import formatear_cantidad, formatear_dinero
from views.dialogo_cantidad import CampoCantidadFluent
from views.ventana_base import VentanaBase

PRECISION_PRECIO = 2
MAXIMO_CANTIDAD = 9999.999
MAXIMO_PRECIO = 99999999.0
MAXIMO_DESCRIPCION = 80


class DialogoComodin(QDialog, VentanaBase):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ítem comodín")
        self.setObjectName("dlgComodin")
        self._aplicar_tema()

        self.txtDescripcion = LineEdit(self)
        self.txtDescripcion.setObjectName("txtDescripcionComodin")
        self.txtDescripcion.setPlaceholderText("Ej: pila AA recargada")
        self.txtDescripcion.setMaxLength(MAXIMO_DESCRIPCION)
        self.spnCantidad = CampoCantidadFluent(self)
        self.spnCantidad.setObjectName("spnCantidadComodin")
        self.spnCantidad.setMaximum(MAXIMO_CANTIDAD)
        self.spnCantidad.setValue(1)
        self.spnPrecio = DoubleSpinBox(self)
        self.spnPrecio.setObjectName("spnPrecioComodin")
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
        formulario.addRow(BodyLabel("Descripción:", self), self.txtDescripcion)
        formulario.addRow(BodyLabel("Cantidad:", self), self.spnCantidad)
        formulario.addRow(BodyLabel("Precio unitario:", self), self.spnPrecio)

        self.lblSubtotal = BodyLabel(self)
        self.lblSubtotal.setObjectName("lblSubtotal")
        self.lblSubtotal.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        self.lblSubtotal.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.botones = self._armar_botones()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addLayout(formulario)
        layout.addWidget(self.lblSubtotal)
        layout.addLayout(self.botones)

        self.txtDescripcion.textChanged.connect(self.actualizar)
        self.spnCantidad.textChanged.connect(self.actualizar)
        self.spnPrecio.valueChanged.connect(self.actualizar)
        self.actualizar()

        self.setMinimumWidth(380)
        self.txtDescripcion.setFocus()

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema claro/oscuro."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}"
        )

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnAgregar = PrimaryPushButton("Agregar", self)
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnAgregar.setDefault(True)
        self.btnCancelar.setAutoDefault(False)
        botones.addStretch(1)
        botones.addWidget(self.btnCancelar)
        botones.addWidget(self.btnAgregar)

        self.btnAgregar.clicked.connect(self.aceptar)
        self.btnCancelar.clicked.connect(self.reject)
        return botones

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
