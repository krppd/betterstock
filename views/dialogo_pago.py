"""Diálogo para registrar el pago de una deuda de fiado."""

from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    CheckBox,
    ComboBox,
    DoubleSpinBox,
    PrimaryPushButton,
    PushButton,
)

from models.medio_pago import MEDIOS, METODO_FIADO
from services.excepciones import ErrorValidacion
from services.gestor_fiado import GestorFiado
from ui.estilos import TAMANO_BODY, fuente
from utils.formato import formatear_dinero
from views.ventana_base import VentanaBase


class DialogoPago(QDialog, VentanaBase):
    def __init__(self, fiado: GestorFiado, codigo_cliente: str, usuario: str = "", parent=None) -> None:
        super().__init__(parent)
        self._fiado = fiado
        self._codigo = codigo_cliente
        self._usuario = usuario
        cliente = fiado.buscar_cliente(codigo_cliente)
        self._deuda = fiado.saldo(codigo_cliente) if cliente is not None else 0.0
        nombre = cliente.nombre if cliente is not None else ""
        self._recargo = 0.0
        self._total = self._deuda
        self.setWindowTitle(f"Pago de {nombre}")
        self.setObjectName("dlgPago")
        self.setMinimumWidth(320)

        self.lblDeuda = BodyLabel(f"Debe: {formatear_dinero(self._deuda)}", self)
        self.lblDeuda.setObjectName("lblDeuda")
        self.lblDeuda.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        self.lblRecargo = BodyLabel(self)
        self.lblRecargo.setObjectName("lblRecargo")
        self.lblTotal = BodyLabel(self)
        self.lblTotal.setObjectName("lblTotal")
        self.lblTotal.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        self.chkRecargo = CheckBox("Incluir recargo", self)
        self.chkRecargo.setObjectName("chkRecargo")
        self.chkRecargo.setChecked(self._recargo > 0)
        for widget in (self.lblRecargo, self.lblTotal, self.chkRecargo):
            widget.setVisible(self._recargo > 0)

        self.spnImporte = DoubleSpinBox(self)
        self.spnImporte.setObjectName("spnImporte")
        self.spnImporte.setDecimals(2)
        self.spnImporte.setMinimum(0.01)
        self.spnImporte.setPrefix("$ ")
        self.cmbMedio = ComboBox(self)
        self.cmbMedio.setObjectName("cmbMedio")
        for etiqueta, codigo in MEDIOS:
            if codigo != METODO_FIADO:
                self.cmbMedio.addItem(etiqueta, userData=codigo)
        self.btnGuardar = PrimaryPushButton("Registrar pago", self)
        self.btnGuardar.setObjectName("btnGuardar")
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnCancelar.setObjectName("btnCancelar")

        formulario = QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.setVerticalSpacing(10)
        formulario.addRow(BodyLabel("Importe:", self), self.spnImporte)
        formulario.addRow(BodyLabel("Pagó con:", self), self.cmbMedio)

        tarjeta = CardWidget(self)
        tarjeta.setObjectName("tarjetaResumen")
        resumen = QVBoxLayout(tarjeta)
        resumen.setContentsMargins(16, 12, 16, 12)
        resumen.setSpacing(6)
        resumen.addWidget(self.lblDeuda)
        resumen.addWidget(self.lblRecargo)
        resumen.addWidget(self.chkRecargo)
        resumen.addWidget(self.lblTotal)

        contenedor = QVBoxLayout(self)
        contenedor.setContentsMargins(20, 18, 20, 18)
        contenedor.setSpacing(12)
        contenedor.addWidget(tarjeta)
        contenedor.addLayout(formulario)
        contenedor.addWidget(self.btnGuardar)
        contenedor.addWidget(self.btnCancelar)
        self.chkRecargo.toggled.connect(self._actualizar_recargo)
        self.btnGuardar.clicked.connect(self.guardar)
        self.btnCancelar.clicked.connect(self.reject)
        self._actualizar_recargo()
        self.spnImporte.setValue(max(self._total, 0.01))

    def _actualizar_recargo(self) -> None:
        """El checkbox decide si el recargo entra en el total y hasta cuánto se puede cobrar."""
        self._total = round(
            self._deuda + (self._recargo if self.chkRecargo.isChecked() else 0.0), 2)
        self.lblRecargo.setText(
            f"Recargo por atraso: {formatear_dinero(self._recargo)}")
        self.lblTotal.setText(f"Total: {formatear_dinero(self._total)}")
        self.spnImporte.setMaximum(max(self._total, 0.01))

    def guardar(self) -> None:
        self.btnGuardar.setEnabled(False)
        try:
            self._fiado.registrar_pago(
                self._codigo, self.spnImporte.value(), date.today(),
                self.cmbMedio.currentData(), usuario=self._usuario)
        except ErrorValidacion as error:
            self.btnGuardar.setEnabled(True)
            self.mostrar_advertencia("Pago", str(error))
            return
        self.accept()
