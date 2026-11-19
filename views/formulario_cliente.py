from __future__ import annotations

import math
import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    DoubleSpinBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
)

from models.cliente import Cliente
from models.validacion_identificador import es_cuit_valido
from services.excepciones import ErrorValidacion
from services.gestor_fiado import GestorFiado
from utils.formato import formatear_dinero
from views.ventana_base import VentanaBase

MAXIMO_LIMITE = 999_999_999.0

DOCUMENTOS = (
    ("Consumidor Final", 99),
    ("DNI", 96),
    ("CUIT", 80),
    ("CUIL", 86),
)

CONDICIONES_IVA = (
    ("Consumidor Final", 5),
    ("Responsable Inscripto", 1),
    ("Monotributista", 6),
    ("Exento", 4),
)


class _UiCliente:
    """Namespace con los widgets Fluent del formulario (``self.ui.*``)."""

    def __init__(self, owner) -> None:
        for atributo in (
            "txtNombre",
            "txtTelefono",
            "cmbDocTipo",
            "txtDocNro",
            "cmbCondIva",
            "txtEmail",
            "spnLimite",
            "chkActivo",
            "lblAyuda",
            "lblFactura",
            "btnGuardar",
            "btnCancelar",
        ):
            setattr(self, atributo, getattr(owner, atributo))


class FormularioCliente(QDialog, VentanaBase):
    """Alta y edición de clientes con su límite de crédito y datos fiscales."""

    def __init__(self, fiado: GestorFiado, cliente: Cliente | None = None, parent=None) -> None:
        super().__init__(parent)
        self._fiado = fiado
        self._codigo = cliente.identificador if cliente is not None else ""
        self.setWindowTitle("Editar cliente" if cliente is not None else "Nuevo cliente")
        self.setObjectName("dlgCliente")
        self.setMinimumWidth(430)

        self.txtNombre = LineEdit(self)
        self.txtNombre.setObjectName("txtNombre")
        self.txtTelefono = LineEdit(self)
        self.txtTelefono.setObjectName("txtTelefono")
        self.cmbDocTipo = ComboBox(self)
        self.cmbDocTipo.setObjectName("cmbDocTipo")
        for etiqueta, codigo in DOCUMENTOS:
            self.cmbDocTipo.addItem(etiqueta, userData=codigo)
        self.txtDocNro = LineEdit(self)
        self.txtDocNro.setObjectName("txtDocNro")
        self.txtDocNro.setPlaceholderText("Número de documento")
        self.cmbCondIva = ComboBox(self)
        self.cmbCondIva.setObjectName("cmbCondIva")
        for etiqueta, codigo in CONDICIONES_IVA:
            self.cmbCondIva.addItem(etiqueta, userData=codigo)
        self.txtEmail = LineEdit(self)
        self.txtEmail.setObjectName("txtEmail")
        self.txtEmail.setPlaceholderText("Opcional, para enviar el comprobante")
        self.spnLimite = DoubleSpinBox(self)
        self.spnLimite.setObjectName("spnLimite")
        self.spnLimite.setDecimals(2)
        self.spnLimite.setMinimum(0.0)
        self.spnLimite.setMaximum(MAXIMO_LIMITE)
        self.spnLimite.setPrefix("$ ")
        self.chkActivo = CheckBox("Activo", self)
        self.chkActivo.setObjectName("chkActivo")
        self.chkActivo.setChecked(True)
        self.lblAyuda = BodyLabel(
            f"Tope 0 = sin límite. Máximo: {formatear_dinero(Cliente.LIMITE_MAXIMO)}.",
            self,
        )
        self.lblAyuda.setObjectName("lblAyuda")
        self.lblAyuda.setWordWrap(True)
        self.lblFactura = BodyLabel(
            "La categoría de monotributo no cambia la letra: todo monotributista "
            "emite Factura C. Un Responsable Inscripto emite A o B según el cliente.",
            self,
        )
        self.lblFactura.setObjectName("lblFactura")
        self.lblFactura.setWordWrap(True)
        self.btnGuardar = PrimaryPushButton("Guardar", self)
        self.btnGuardar.setObjectName("btnGuardar")
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnCancelar.setObjectName("btnCancelar")

        fila_documento = QHBoxLayout()
        fila_documento.setSpacing(8)
        fila_documento.addWidget(self.cmbDocTipo)
        fila_documento.addWidget(self.txtDocNro, 1)

        formulario = QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.setVerticalSpacing(10)
        formulario.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        formulario.addRow(BodyLabel("Nombre:", self), self.txtNombre)
        formulario.addRow(BodyLabel("Teléfono:", self), self.txtTelefono)
        formulario.addRow(BodyLabel("Documento:", self), fila_documento)
        formulario.addRow(BodyLabel("Condición IVA:", self), self.cmbCondIva)
        formulario.addRow(BodyLabel("Email:", self), self.txtEmail)
        formulario.addRow(BodyLabel("Tope:", self), self.spnLimite)
        formulario.addRow("", self.chkActivo)
        self.chkActivo.setVisible(cliente is not None)

        botones = QHBoxLayout()
        botones.setSpacing(8)
        botones.addWidget(self.btnCancelar)
        botones.addStretch(1)
        botones.addWidget(self.btnGuardar)

        contenedor = QVBoxLayout(self)
        contenedor.setContentsMargins(20, 18, 20, 18)
        contenedor.setSpacing(12)
        contenedor.addLayout(formulario)
        contenedor.addWidget(self.lblAyuda)
        contenedor.addWidget(self.lblFactura)
        contenedor.addLayout(botones)

        if cliente is not None:
            self.txtNombre.setText(cliente.nombre)
            self.txtTelefono.setText(cliente.telefono)
            indice_doc = self.cmbDocTipo.findData(cliente.doc_tipo)
            if indice_doc >= 0:
                self.cmbDocTipo.setCurrentIndex(indice_doc)
            self.txtDocNro.setText(cliente.doc_nro)
            indice_iva = self.cmbCondIva.findData(cliente.cond_iva)
            if indice_iva >= 0:
                self.cmbCondIva.setCurrentIndex(indice_iva)
            self.txtEmail.setText(cliente.email)
            if math.isfinite(cliente.limite):
                self.spnLimite.setMaximum(
                    max(self.spnLimite.maximum(), math.ceil(cliente.limite)))
            self.spnLimite.setValue(cliente.limite)
            self.chkActivo.setChecked(cliente.activo)

        self.cmbDocTipo.currentIndexChanged.connect(self._actualizar_documento)
        self.btnGuardar.clicked.connect(self.guardar)
        self.btnCancelar.clicked.connect(self.reject)
        self._actualizar_documento()
        self.txtNombre.setFocus()

        self.ui = _UiCliente(self)
    def _actualizar_documento(self) -> None:
        tipo = int(self.cmbDocTipo.currentData())
        self.txtDocNro.setEnabled(tipo != 99)
        if tipo == 99:
            self.txtDocNro.clear()
            self.txtDocNro.setPlaceholderText("Sin documento")
        elif tipo == 80:
            self.txtDocNro.setPlaceholderText("CUIT de 11 dígitos")
        elif tipo == 86:
            self.txtDocNro.setPlaceholderText("CUIL de 11 dígitos")
        else:
            self.txtDocNro.setPlaceholderText("DNI")

    def _documento(self) -> tuple[int, str]:
        tipo = int(self.cmbDocTipo.currentData())
        numero = re.sub(r"\D", "", self.txtDocNro.text())
        if tipo != 99:
            if not numero:
                raise ErrorValidacion("Ingresá el número de documento.")
            if tipo in (80, 86) and len(numero) != 11:
                raise ErrorValidacion(
                    "El CUIT/CUIL debe tener 11 dígitos.")
        return tipo, numero or "0"

    def guardar(self) -> None:
        try:
            doc_tipo, doc_nro = self._documento()
            cond_iva = int(self.cmbCondIva.currentData())
            if cond_iva == 1 and doc_tipo != 80:
                raise ErrorValidacion(
                    "Un Responsable Inscripto necesita CUIT del cliente.")
            if cond_iva == 1 and not es_cuit_valido(doc_nro):
                raise ErrorValidacion("El CUIT del cliente no es válido.")
            self._fiado.guardar_cliente(
                self.txtNombre.text(), telefono=self.txtTelefono.text(),
                limite=self.spnLimite.value(), activo=self.chkActivo.isChecked(),
                codigo=self._codigo, doc_tipo=doc_tipo, doc_nro=doc_nro,
                cond_iva=cond_iva, email=self.txtEmail.text())
        except (ErrorValidacion, ValueError) as error:
            self.mostrar_advertencia("Cliente", str(error))
            return
        self.accept()
