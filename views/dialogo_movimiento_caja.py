from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.caja_movimiento import CajaMovimiento
from views.ventana_base import VentanaBase


class DialogoMovimientoCaja(QDialog, VentanaBase):
    def __init__(self, parent: QWidget | None = None, tipo_defecto: str = CajaMovimiento.TIPO_EGRESO) -> None:
        super().__init__(parent)
        self.setWindowTitle("Movimiento de caja")
        self._datos: tuple[str, str, str, float] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        formulario = QFormLayout()

        self.cmbTipo = QComboBox(self)
        self.cmbTipo.addItem("Egreso (retiro de efectivo)", CajaMovimiento.TIPO_EGRESO)
        self.cmbTipo.addItem("Ingreso (entrada de efectivo)", CajaMovimiento.TIPO_INGRESO)
        if tipo_defecto == CajaMovimiento.TIPO_INGRESO:
            self.cmbTipo.setCurrentIndex(1)
        formulario.addRow("Tipo:", self.cmbTipo)

        self.txtConcepto = QLineEdit(self)
        self.txtConcepto.setPlaceholderText("Ej: Pago de flete, compras menores, cambio")
        formulario.addRow("Concepto:", self.txtConcepto)

        self.txtCategoria = QLineEdit(self)
        self.txtCategoria.setPlaceholderText("Opcional (ej: Limpieza, Flete, Retiro)")
        formulario.addRow("Categoría:", self.txtCategoria)

        self.spnImporte = QDoubleSpinBox(self)
        self.spnImporte.setDecimals(2)
        self.spnImporte.setMinimum(0.01)
        self.spnImporte.setMaximum(99_999_999.99)
        self.spnImporte.setPrefix("$ ")
        formulario.addRow("Importe:", self.spnImporte)

        layout.addLayout(formulario)
        layout.addStretch(1)

        botones = QHBoxLayout()
        self.btnCancelar = QPushButton("Cancelar", self)
        self.btnAceptar = QPushButton("Guardar", self)
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
