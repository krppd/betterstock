from PyQt6 import QtCore, QtWidgets

from ui.estilos import TAMANO_SMALL, TAMANO_SUBTITLE, fuente


class Ui_PagosMPForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowTitle("Pagos de MercadoPago")
        Form.setMinimumSize(840, 440)

        self.hlyMain = QtWidgets.QHBoxLayout(Form)
        self.hlyMain.setObjectName("hlyMain")

        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(16, 16, 8, 16)
        self.verticalLayout.setSpacing(10)

        self.hlyToken = QtWidgets.QHBoxLayout()
        self.hlyToken.setObjectName("hlyToken")

        self.lblToken = QtWidgets.QLabel(parent=Form)
        self.lblToken.setObjectName("lblToken")
        self.hlyToken.addWidget(self.lblToken)

        self.txtToken = QtWidgets.QLineEdit(parent=Form)
        self.txtToken.setObjectName("txtToken")
        self.txtToken.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.txtToken.setPlaceholderText("Token de solo lectura")
        self.hlyToken.addWidget(self.txtToken)

        self.btnGuardarToken = QtWidgets.QPushButton(parent=Form)
        self.btnGuardarToken.setObjectName("btnGuardarToken")
        self.hlyToken.addWidget(self.btnGuardarToken)

        self.btnActualizar = QtWidgets.QPushButton(parent=Form)
        self.btnActualizar.setObjectName("btnActualizar")
        self.hlyToken.addWidget(self.btnActualizar)

        self.verticalLayout.addLayout(self.hlyToken)

        self.lblInfo = QtWidgets.QLabel(parent=Form)
        self.lblInfo.setFont(fuente(TAMANO_SMALL))
        self.lblInfo.setObjectName("lblInfo")
        self.lblInfo.setWordWrap(True)
        self.verticalLayout.addWidget(self.lblInfo)

        self.tblPagos = QtWidgets.QTableWidget(parent=Form)
        self.tblPagos.setObjectName("tblPagos")
        self.tblPagos.setColumnCount(5)
        self.tblPagos.setRowCount(0)
        for i, texto in enumerate(["ID", "Fecha", "Monto", "Estado", "Medio"]):
            item = QtWidgets.QTableWidgetItem()
            item.setText(texto)
            self.tblPagos.setHorizontalHeaderItem(i, item)
        self.tblPagos.horizontalHeader().setStretchLastSection(True)
        self.tblPagos.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblPagos.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.verticalLayout.addWidget(self.tblPagos)

        self.hlyBotones = QtWidgets.QHBoxLayout()
        self.hlyBotones.setObjectName("hlyBotones")

        spacer = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.hlyBotones.addItem(spacer)

        self.btnCancelar = QtWidgets.QPushButton(parent=Form)
        self.btnCancelar.setObjectName("btnCancelar")
        self.hlyBotones.addWidget(self.btnCancelar)

        self.btnElegir = QtWidgets.QPushButton(parent=Form)
        self.btnElegir.setObjectName("btnElegir")
        self.hlyBotones.addWidget(self.btnElegir)

        self.verticalLayout.addLayout(self.hlyBotones)

        self.hlyMain.addLayout(self.verticalLayout, 3)

        self.vlyQR = QtWidgets.QVBoxLayout()
        self.vlyQR.setObjectName("vlyQR")
        self.vlyQR.setContentsMargins(8, 16, 16, 16)
        self.vlyQR.setSpacing(8)

        self.lblQRTitulo = QtWidgets.QLabel(parent=Form)
        font_qr = fuente(TAMANO_SUBTITLE, negrita=True)
        self.lblQRTitulo.setFont(font_qr)
        self.lblQRTitulo.setObjectName("lblQRTitulo")
        self.lblQRTitulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.vlyQR.addWidget(self.lblQRTitulo)

        self.lblQR = QtWidgets.QLabel(parent=Form)
        self.lblQR.setObjectName("lblQR")
        self.lblQR.setMinimumSize(180, 180)
        self.lblQR.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.vlyQR.addWidget(self.lblQR)

        self.lblQRPie = QtWidgets.QLabel(parent=Form)
        self.lblQRPie.setFont(fuente(TAMANO_SMALL))
        self.lblQRPie.setObjectName("lblQRPie")
        self.lblQRPie.setWordWrap(True)
        self.lblQRPie.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.vlyQR.addWidget(self.lblQRPie)

        spacer_qr = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.vlyQR.addItem(spacer_qr)

        self.hlyMain.addLayout(self.vlyQR, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Pagos de MercadoPago"))
        self.lblToken.setText(_translate("Form", "Token:"))
        self.btnGuardarToken.setText(_translate("Form", "Guardar"))
        self.btnActualizar.setText(_translate("Form", "Actualizar"))
        self.lblQRTitulo.setText(_translate("Form", "QR para cobrar"))
        self.lblQRPie.setText(_translate("Form", "De demostración: reemplazar por el QR real del comercio."))
        self.lblInfo.setText(_translate(
            "Form", "Elegí el pago a ojo comparando el monto con el total de la venta."))
        self.btnCancelar.setText(_translate("Form", "Cancelar"))
        self.btnElegir.setText(_translate("Form", "Elegir"))