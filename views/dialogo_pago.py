from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
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
        self.setMinimumWidth(320)
        self.lblDeuda = QLabel(f"Debe: {formatear_dinero(self._deuda)}")
        self.lblDeuda.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        self.lblTotal = QLabel()
        self.lblTotal.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        self.spnImporte = QDoubleSpinBox()
        self.spnImporte.setDecimals(2)
        self.spnImporte.setMinimum(0.01)
        self.spnImporte.setPrefix("$ ")
        self.cmbMedio = QComboBox()
        for etiqueta, codigo in MEDIOS:
            if codigo != METODO_FIADO:
                self.cmbMedio.addItem(etiqueta, codigo)
        self.btnGuardar = QPushButton("Registrar pago")
        self.btnCancelar = QPushButton("Cancelar")
        formulario = QFormLayout()
        formulario.addRow("Importe:", self.spnImporte)
        formulario.addRow("Pagó con:", self.cmbMedio)
        contenedor = QVBoxLayout(self)
        contenedor.addWidget(self.lblDeuda)
        contenedor.addWidget(self.lblTotal)
        contenedor.addLayout(formulario)
        contenedor.addWidget(self.btnGuardar)
        contenedor.addWidget(self.btnCancelar)
        self.btnGuardar.clicked.connect(self.guardar)
        self.btnCancelar.clicked.connect(self.reject)
        self._actualizar_recargo()
        self.spnImporte.setValue(max(self._total, 0.01))

    def _actualizar_recargo(self) -> None:
        self._total = round(self._deuda, 2)
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
