from PyQt6 import QtCore, QtWidgets

from ui.estilos import TAMANO_BODY, TAMANO_DISPLAY, TAMANO_MICRO, VERDE_TEXTO, fuente
from ui.widgets.etiqueta_rodante import EtiquetaRodante

MAXIMO_MONTO = 1_000_000_000_000.0


class Ui_CobroForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowTitle("Cobrar")
        Form.setFixedSize(380, 600)

        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(20, 24, 20, 20)
        self.verticalLayout.setSpacing(10)

        self.lblTotalPagar = QtWidgets.QLabel(parent=Form)
        self.lblTotalPagar.setFont(fuente(TAMANO_BODY, negrita=True))
        self.lblTotalPagar.setObjectName("lblTotalPagar")
        self.verticalLayout.addWidget(self.lblTotalPagar)

        self.lblTotalCobrar = EtiquetaRodante(parent=Form, alineacion=QtCore.Qt.AlignmentFlag.AlignCenter)
        font_cobrar = fuente(TAMANO_DISPLAY, negrita=True, tabular=True)
        self.lblTotalCobrar.setFont(font_cobrar)
        self.lblTotalCobrar.setStyleSheet(f"color: {VERDE_TEXTO};")
        self.lblTotalCobrar.setObjectName("lblTotalCobrar")
        self.lblTotalCobrar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout.addWidget(self.lblTotalCobrar)

        self.lblDetalle = QtWidgets.QLabel(parent=Form)
        font_detalle = fuente(TAMANO_MICRO)
        self.lblDetalle.setFont(font_detalle)
        self.lblDetalle.setObjectName("lblDetalle")
        self.lblDetalle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblDetalle.setWordWrap(True)
        self.lblDetalle.setVisible(False)
        self.verticalLayout.addWidget(self.lblDetalle)

        self.linea = QtWidgets.QFrame(parent=Form)
        self.linea.setObjectName("linea")
        self.linea.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.linea.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.verticalLayout.addWidget(self.linea)

        self.lblMetodo = QtWidgets.QLabel(parent=Form)
        self.lblMetodo.setObjectName("lblMetodo")
        self.verticalLayout.addWidget(self.lblMetodo)

        self.cmbMetodo = QtWidgets.QComboBox(parent=Form)
        self.cmbMetodo.setObjectName("cmbMetodo")
        self.cmbMetodo.setMinimumHeight(30)
        self.verticalLayout.addWidget(self.cmbMetodo)

        self.lblMedioParcial = QtWidgets.QLabel(parent=Form)
        self.lblMedioParcial.setObjectName("lblMedioParcial")
        self.lblMedioParcial.setVisible(False)
        self.verticalLayout.addWidget(self.lblMedioParcial)

        self.cmbMedioParcial = QtWidgets.QComboBox(parent=Form)
        self.cmbMedioParcial.setObjectName("cmbMedioParcial")
        self.cmbMedioParcial.setMinimumHeight(30)
        self.cmbMedioParcial.setVisible(False)
        self.verticalLayout.addWidget(self.cmbMedioParcial)

        self.lblCliente = QtWidgets.QLabel(parent=Form)
        self.lblCliente.setObjectName("lblCliente")
        self.verticalLayout.addWidget(self.lblCliente)

        self.cmbCliente = QtWidgets.QComboBox(parent=Form)
        self.cmbCliente.setObjectName("cmbCliente")
        self.cmbCliente.setMinimumHeight(30)
        self.verticalLayout.addWidget(self.cmbCliente)

        self.lblSaldo = QtWidgets.QLabel(parent=Form)
        self.lblSaldo.setObjectName("lblSaldo")
        self.verticalLayout.addWidget(self.lblSaldo)

        self.lblMonto = QtWidgets.QLabel(parent=Form)
        self.lblMonto.setObjectName("lblMonto")
        self.verticalLayout.addWidget(self.lblMonto)

        self.spnMonto = QtWidgets.QDoubleSpinBox(parent=Form)
        self.spnMonto.setObjectName("spnMonto")
        self.spnMonto.setDecimals(2)
        self.spnMonto.setMinimum(0.0)
        self.spnMonto.setMaximum(MAXIMO_MONTO)
        self.spnMonto.setMinimumHeight(30)
        self.verticalLayout.addWidget(self.spnMonto)

        self.lblVuelto = EtiquetaRodante(parent=Form, alineacion=QtCore.Qt.AlignmentFlag.AlignCenter)
        font_vuelto = fuente(TAMANO_BODY, negrita=True, tabular=True)
        self.lblVuelto.setFont(font_vuelto)
        self.lblVuelto.setObjectName("lblVuelto")
        self.lblVuelto.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout.addWidget(self.lblVuelto)

        self.lblDatos = QtWidgets.QLabel(parent=Form)
        self.lblDatos.setObjectName("lblDatos")
        self.verticalLayout.addWidget(self.lblDatos)

        self.txtDatos = QtWidgets.QLineEdit(parent=Form)
        self.txtDatos.setObjectName("txtDatos")
        self.txtDatos.setMaxLength(60)
        self.txtDatos.setMinimumHeight(30)
        self.verticalLayout.addWidget(self.txtDatos)

        self.lblPagos = QtWidgets.QLabel(parent=Form)
        self.lblPagos.setFont(fuente(TAMANO_BODY))
        self.lblPagos.setObjectName("lblPagos")
        self.lblPagos.setWordWrap(True)
        self.lblPagos.setVisible(False)
        self.verticalLayout.addWidget(self.lblPagos)

        self.hlyPagos = QtWidgets.QHBoxLayout()
        self.hlyPagos.setObjectName("hlyPagos")

        self.btnAgregar = QtWidgets.QPushButton(parent=Form)
        self.btnAgregar.setObjectName("btnAgregar")
        self.btnAgregar.setMinimumHeight(30)
        self.hlyPagos.addWidget(self.btnAgregar)

        self.btnQuitar = QtWidgets.QPushButton(parent=Form)
        self.btnQuitar.setObjectName("btnQuitar")
        self.btnQuitar.setMinimumHeight(30)
        self.hlyPagos.addWidget(self.btnQuitar)

        self.verticalLayout.addLayout(self.hlyPagos)

        spacer = QtWidgets.QSpacerItem(
            20, 10, QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacer)

        self.hlyBotones = QtWidgets.QHBoxLayout()
        self.hlyBotones.setObjectName("hlyBotones")

        self.btnCancelar = QtWidgets.QPushButton(parent=Form)
        self.btnCancelar.setObjectName("btnCancelar")
        self.btnCancelar.setMinimumHeight(36)
        self.hlyBotones.addWidget(self.btnCancelar)

        self.btnCobrar = QtWidgets.QPushButton(parent=Form)
        font_cobrar = fuente(TAMANO_BODY, negrita=True)
        self.btnCobrar.setFont(font_cobrar)
        self.btnCobrar.setObjectName("btnCobrar")
        self.btnCobrar.setMinimumHeight(36)
        self.hlyBotones.addWidget(self.btnCobrar)

        self.verticalLayout.addLayout(self.hlyBotones)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Cobrar"))
        self.lblTotalPagar.setText(_translate("Form", "TOTAL A COBRAR:"))
        self.lblTotalCobrar.setText(_translate("Form", "$ 0,00"))
        self.lblDetalle.setText(_translate("Form", ""))
        self.lblMetodo.setText(_translate("Form", "Medio de pago:"))
        self.lblMedioParcial.setText(_translate("Form", "Medio del pago parcial:"))
        self.lblCliente.setText(_translate("Form", "Cliente:"))
        self.lblSaldo.setText(_translate("Form", ""))
        self.lblMonto.setText(_translate("Form", "Monto recibido:"))
        self.lblVuelto.setText(_translate("Form", "Vuelto: $ 0,00"))
        self.lblDatos.setText(_translate("Form", ""))
        self.txtDatos.setText(_translate("Form", ""))
        self.lblPagos.setText(_translate("Form", ""))
        self.btnAgregar.setText(_translate("Form", "Registrar dinero parcial"))
        self.btnQuitar.setText(_translate("Form", "Quitar"))
        self.btnCancelar.setText(_translate("Form", "Cancelar"))
        self.btnCobrar.setText(_translate("Form", "Cobrar"))
