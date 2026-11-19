from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    DoubleSpinBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
)

from models.caja_movimiento import CajaMovimiento
from views.ventana_base import VentanaBase

IMPORTE_MAXIMO = 99_999_999.99


class DialogoMovimientoCaja(QDialog, VentanaBase):
    """Alta de un ingreso o egreso de caja."""

    def __init__(self, parent: QWidget | None = None, tipo_defecto: str = CajaMovimiento.TIPO_EGRESO) -> None:
        super().__init__(parent)
        self.setWindowTitle("Movimiento de caja")
        self.setObjectName("dlgMovimientoCaja")
        self._datos: tuple[str, str, str, float] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        formulario = QFormLayout()
        formulario.setSpacing(10)

        self.cmbTipo = ComboBox(self)
        self.cmbTipo.setObjectName("cmbTipo")
        self.cmbTipo.addItem("Egreso (retiro de efectivo)", userData=CajaMovimiento.TIPO_EGRESO)
        self.cmbTipo.addItem("Ingreso (entrada de efectivo)", userData=CajaMovimiento.TIPO_INGRESO)
        if tipo_defecto == CajaMovimiento.TIPO_INGRESO:
            self.cmbTipo.setCurrentIndex(1)
        formulario.addRow(BodyLabel("Tipo:", self), self.cmbTipo)

        self.txtConcepto = LineEdit(self)
        self.txtConcepto.setObjectName("txtConcepto")
        self.txtConcepto.setPlaceholderText("Ej: Pago de flete, compras menores, cambio")
        formulario.addRow(BodyLabel("Concepto:", self), self.txtConcepto)

        self.txtCategoria = LineEdit(self)
        self.txtCategoria.setObjectName("txtCategoria")
        self.txtCategoria.setPlaceholderText("Opcional (ej: Limpieza, Flete, Retiro)")
        formulario.addRow(BodyLabel("Categoría:", self), self.txtCategoria)

        self.spnImporte = DoubleSpinBox(self)
        self.spnImporte.setObjectName("spnImporte")
        self.spnImporte.setDecimals(2)
        self.spnImporte.setMinimum(0.01)
        self.spnImporte.setMaximum(IMPORTE_MAXIMO)
        self.spnImporte.setPrefix("$ ")
        formulario.addRow(BodyLabel("Importe:", self), self.spnImporte)

        layout.addLayout(formulario)
        layout.addStretch(1)

        botones = QHBoxLayout()
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnAceptar = PrimaryPushButton("Guardar", self)
        self.btnCancelar.setAutoDefault(False)
        self.btnAceptar.setDefault(True)
        botones.addWidget(self.btnCancelar)
        botones.addStretch(1)
        botones.addWidget(self.btnAceptar)
        layout.addLayout(botones)

        self.btnCancelar.clicked.connect(self.reject)
        self.btnAceptar.clicked.connect(self.guardar)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.txtConcepto.setFocus()

    @property
    def datos(self) -> tuple[str, str, str, float] | None:
        return self._datos

    def guardar(self) -> None:
        concepto = self.txtConcepto.text().strip()
        if not concepto:
            self.mostrar_advertencia("Movimiento de caja", "El concepto es obligatorio.")
            self.txtConcepto.setFocus()
            return

        importe = self.spnImporte.value()
        if importe <= 0:
            self.mostrar_advertencia("Movimiento de caja", "El importe debe ser mayor a cero.")
            self.spnImporte.setFocus()
            return

        tipo = self.cmbTipo.currentData()
        categoria = self.txtCategoria.text().strip()
        self._datos = (tipo, concepto, categoria, importe)
        self.accept()
