from PyQt6 import QtCore, QtWidgets

from ui.estilos import TAMANO_BODY, TAMANO_SMALL, fuente
from ui.widgets.etiqueta_rodante import EtiquetaRodante


class Ui_ClientesForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(760, 560)

        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(20, 10, 20, 10)
        self.verticalLayout.setSpacing(6)

        self.hlyBuscar = QtWidgets.QHBoxLayout()
        self.hlyBuscar.setObjectName("hlyBuscar")

        self.lblBuscar = QtWidgets.QLabel(parent=Form)
        self.lblBuscar.setObjectName("lblBuscar")
        self.hlyBuscar.addWidget(self.lblBuscar)

        self.txtBuscar = QtWidgets.QLineEdit(parent=Form)
        self.txtBuscar.setObjectName("txtBuscar")
        self.txtBuscar.setMinimumHeight(30)
        self.hlyBuscar.addWidget(self.txtBuscar, 1)

        self.lblDeudaTotal = EtiquetaRodante(parent=Form)
        font_deuda = fuente(TAMANO_SMALL, negrita=True, tabular=True)
        self.lblDeudaTotal.setFont(font_deuda)
        self.lblDeudaTotal.setObjectName("lblDeudaTotal")
        self.hlyBuscar.addWidget(self.lblDeudaTotal)

        self.verticalLayout.addLayout(self.hlyBuscar)

        self.tblClientes = QtWidgets.QTableWidget(parent=Form)
        self.tblClientes.setColumnCount(5)
        self.tblClientes.setObjectName("tblClientes")
        self.tblClientes.setRowCount(0)
        for indice, encabezado in enumerate(["Código", "Nombre", "Teléfono", "Debe", "Tope"]):
            item = QtWidgets.QTableWidgetItem()
            item.setText(encabezado)
            self.tblClientes.setHorizontalHeaderItem(indice, item)
        self.tblClientes.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblClientes.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.verticalLayout.addWidget(self.tblClientes, 2)

        self.hlyBotones = QtWidgets.QHBoxLayout()
        self.hlyBotones.setObjectName("hlyBotones")

        self.btnNuevo = QtWidgets.QPushButton(parent=Form)
        self.btnNuevo.setObjectName("btnNuevo")
        self.btnNuevo.setMinimumHeight(34)
        self.hlyBotones.addWidget(self.btnNuevo)

        self.btnEditar = QtWidgets.QPushButton(parent=Form)
        self.btnEditar.setObjectName("btnEditar")
        self.btnEditar.setMinimumHeight(34)
        self.hlyBotones.addWidget(self.btnEditar)

        self.btnPago = QtWidgets.QPushButton(parent=Form)
        font_pago = fuente(TAMANO_BODY, negrita=True)
        self.btnPago.setFont(font_pago)
        self.btnPago.setObjectName("btnPago")
        self.btnPago.setMinimumHeight(34)
        self.hlyBotones.addWidget(self.btnPago)

        self.btnWhatsApp = QtWidgets.QPushButton(parent=Form)
        self.btnWhatsApp.setObjectName("btnWhatsApp")
        self.btnWhatsApp.setMinimumHeight(34)
        self.hlyBotones.addWidget(self.btnWhatsApp)

        self.verticalLayout.addLayout(self.hlyBotones)

        self.lblCuenta = QtWidgets.QLabel(parent=Form)
        font_cuenta = fuente(TAMANO_SMALL, negrita=True)
        self.lblCuenta.setFont(font_cuenta)
        self.lblCuenta.setObjectName("lblCuenta")
        self.verticalLayout.addWidget(self.lblCuenta)

        self.tblCuenta = QtWidgets.QTableWidget(parent=Form)
        self.tblCuenta.setColumnCount(6)
        self.tblCuenta.setObjectName("tblCuenta")
        self.tblCuenta.setRowCount(0)
        for indice, encabezado in enumerate(["Fecha", "Tipo", "Importe", "Pagó con", "Detalle", "Usuario"]):
            item = QtWidgets.QTableWidgetItem()
            item.setText(encabezado)
            self.tblCuenta.setHorizontalHeaderItem(indice, item)
        self.tblCuenta.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblCuenta.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.verticalLayout.addWidget(self.tblCuenta, 2)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Cuentas de clientes"))
        self.lblBuscar.setText(_translate("Form", "Buscar:"))
        self.txtBuscar.setPlaceholderText(_translate("Form", "Nombre o código..."))
        self.lblDeudaTotal.setText(_translate("Form", ""))
        self.btnNuevo.setText(_translate("Form", "Nuevo cliente"))
        self.btnEditar.setText(_translate("Form", "Editar"))
        self.btnPago.setText(_translate("Form", "Registrar pago"))
        self.btnWhatsApp.setText(_translate("Form", "Enviar por WhatsApp"))
        self.lblCuenta.setText(_translate("Form", "Cuenta"))
