from __future__ import annotations

import math

from PyQt6.QtWidgets import QCheckBox, QDialog, QDoubleSpinBox, QFormLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from models.cliente import Cliente
from services.excepciones import ErrorValidacion
from services.gestor_fiado import GestorFiado
from utils.formato import formatear_dinero
from views.ventana_base import VentanaBase

MAXIMO_LIMITE = 999_999_999.0


class FormularioCliente(QDialog, VentanaBase):
    def __init__(self, fiado: GestorFiado, cliente: Cliente | None = None, parent=None) -> None:
        super().__init__(parent)
        self._fiado = fiado
        self._codigo = cliente.identificador if cliente is not None else ""
        self.setWindowTitle("Editar cliente" if cliente is not None else "Nuevo cliente")
        self.setMinimumWidth(340)
        self.txtNombre = QLineEdit()
        self.txtTelefono = QLineEdit()
        self.spnLimite = QDoubleSpinBox()
        self.spnLimite.setDecimals(2)
        self.spnLimite.setMinimum(0.0)
        self.spnLimite.setMaximum(MAXIMO_LIMITE)
        self.spnLimite.setPrefix("$ ")
        self.chkActivo = QCheckBox("Activo")
        self.chkActivo.setChecked(True)
        self.lblAyuda = QLabel(
            f"Tope 0 = sin límite. Máximo: {formatear_dinero(Cliente.LIMITE_MAXIMO)}.")
        self.btnGuardar = QPushButton("Guardar")
        self.btnCancelar = QPushButton("Cancelar")
        formulario = QFormLayout()
        formulario.addRow("Nombre:", self.txtNombre)
        formulario.addRow("Teléfono:", self.txtTelefono)
        formulario.addRow("Tope:", self.spnLimite)
        if cliente is not None:
            formulario.addRow("", self.chkActivo)
        contenedor = QVBoxLayout(self)
        contenedor.addLayout(formulario)
        contenedor.addWidget(self.lblAyuda)
        contenedor.addWidget(self.btnGuardar)
        contenedor.addWidget(self.btnCancelar)
        if cliente is not None:
            self.txtNombre.setText(cliente.nombre)
            self.txtTelefono.setText(cliente.telefono)
            if math.isfinite(cliente.limite):
                self.spnLimite.setMaximum(
                    max(self.spnLimite.maximum(), math.ceil(cliente.limite)))
            self.spnLimite.setValue(cliente.limite)
            self.chkActivo.setChecked(cliente.activo)
        self.btnGuardar.clicked.connect(self.guardar)
        self.btnCancelar.clicked.connect(self.reject)
        self.txtNombre.setFocus()

    def guardar(self) -> None:
        try:
            self._fiado.guardar_cliente(
                self.txtNombre.text(), telefono=self.txtTelefono.text(),
                limite=self.spnLimite.value(), activo=self.chkActivo.isChecked(),
                codigo=self._codigo)
        except (ErrorValidacion, ValueError) as error:
            self.mostrar_advertencia("Cliente", str(error))
            return
        self.accept()
