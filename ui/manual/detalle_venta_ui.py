from PyQt6 import QtCore, QtWidgets

from ui.estilos import TAMANO_BODY, TAMANO_SMALL, VERDE, fuente


class Ui_DetalleVentaForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowTitle("detalle de la venta")
        Form.setMinimumSize(720, 550)

        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(16, 16, 16, 16)
        self.verticalLayout.setSpacing(10)

        self.lblCabecera = QtWidgets.QLabel(parent=Form)
        font_cabecera = fuente(TAMANO_BODY, negrita=True)
        self.lblCabecera.setFont(font_cabecera)
        self.lblCabecera.setObjectName("lblCabecera")
        self.verticalLayout.addWidget(self.lblCabecera)

        self.lblMedio = QtWidgets.QLabel(parent=Form)
        self.lblMedio.setObjectName("lblMedio")
        self.lblMedio.setWordWrap(True)
        self.verticalLayout.addWidget(self.lblMedio)

        self.tblDetalle = QtWidgets.QTableWidget(parent=Form)
        self.tblDetalle.setColumnCount(6)
        self.tblDetalle.setObjectName("tblDetalle")
        self.tblDetalle.setRowCount(0)
        self.tblDetalle.horizontalHeader().setDefaultSectionSize(90)
        self.tblDetalle.horizontalHeader().setStretchLastSection(True)
        self.tblDetalle.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblDetalle.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tblDetalle.setAlternatingRowColors(True)
        self.verticalLayout.addWidget(self.tblDetalle, 3)

        self.lblResumen = QtWidgets.QLabel(parent=Form)
        font_resumen = fuente(TAMANO_SMALL, tabular=True)
        self.lblResumen.setFont(font_resumen)
        self.lblResumen.setObjectName("lblResumen")
        self.lblResumen.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.verticalLayout.addWidget(self.lblResumen)

        self.tblDatos = QtWidgets.QTableWidget(parent=Form)
        self.tblDatos.setColumnCount(2)
        self.tblDatos.setObjectName("tblDatos")
        self.tblDatos.setRowCount(0)
        self.tblDatos.horizontalHeader().setDefaultSectionSize(130)
        self.tblDatos.horizontalHeader().setStretchLastSection(True)
        self.tblDatos.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblDatos.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tblDatos.setFixedHeight(160)
        self.verticalLayout.addWidget(self.tblDatos)

        self.hlyBotones = QtWidgets.QHBoxLayout()
        self.hlyBotones.setObjectName("hlyBotones")

        self.lblAyuda = QtWidgets.QLabel(parent=Form)
        self.lblAyuda.setObjectName("lblAyuda")
        self.lblAyuda.setWordWrap(True)
        self.hlyBotones.addWidget(self.lblAyuda, 1)

        self.btnDevolucion = QtWidgets.QPushButton(parent=Form)
        self.btnDevolucion.setObjectName("btnDevolucion")
        self.btnDevolucion.setMinimumHeight(36)
        self.hlyBotones.addWidget(self.btnDevolucion)

        self.btnAnular = QtWidgets.QPushButton(parent=Form)
        self.btnAnular.setObjectName("btnAnular")
        self.btnAnular.setMinimumHeight(36)
        self.hlyBotones.addWidget(self.btnAnular)

        self.btnPdf = QtWidgets.QPushButton(parent=Form)
        self.btnPdf.setObjectName("btnPdf")
        self.btnPdf.setMinimumHeight(36)
        self.hlyBotones.addWidget(self.btnPdf)

        self.btnCerrar = QtWidgets.QPushButton(parent=Form)
        font_cerrar = fuente(TAMANO_BODY, negrita=True)
        self.btnCerrar.setFont(font_cerrar)
        self.btnCerrar.setObjectName("btnCerrar")
        self.btnCerrar.setMinimumHeight(36)
        self.btnCerrar.setStyleSheet(f"background-color: {VERDE}; color: white;")
        self.hlyBotones.addWidget(self.btnCerrar)

        self.verticalLayout.addLayout(self.hlyBotones)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "detalle de la venta"))
        self.lblCabecera.setText(_translate("Form", "Venta"))
        self.btnDevolucion.setText(_translate("Form", "Devolución parcial"))
        self.btnDevolucion.setToolTip(_translate("Form", "Devolver ítems de la venta sin anular el ticket completo"))
        self.btnAnular.setText(_translate("Form", "Anular venta"))
        self.btnAnular.setToolTip(_translate("Form", "Anular la venta con el código del supervisor"))
        self.btnPdf.setText(_translate("Form", "Exportar PDF"))
        self.btnPdf.setToolTip(_translate("Form", "Exportar el detalle de la venta a un archivo PDF"))
        self.btnCerrar.setText(_translate("Form", "Cerrar"))

        headers = ["código", "producto", "cantidad", "precio", "subtotal", "iva"]
        for i, header in enumerate(headers):
            item = QtWidgets.QTableWidgetItem()
            item.setText(_translate("Form", header))
            self.tblDetalle.setHorizontalHeaderItem(i, item)
