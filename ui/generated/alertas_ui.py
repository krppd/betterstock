from PyQt6 import QtCore, QtWidgets
from qfluentwidgets import (
    BodyLabel,
    TableWidget,
)
import Recursos.Recursos_rc  # noqa: F401 - registra los recursos (íconos) en runtime


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(520, 640)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setSpacing(12)

        self.lblStock = BodyLabel(parent=Form)
        self.lblStock.setObjectName("lblStock")
        self.verticalLayout.addWidget(self.lblStock)

        self.tblAlertas = TableWidget(parent=Form)
        self.tblAlertas.setObjectName("tblAlertas")
        self.tblAlertas.setColumnCount(4)
        self.tblAlertas.setRowCount(0)
        self.tblAlertas.setBorderRadius(8)
        self.tblAlertas.setBorderVisible(True)
        for col in range(4):
            item = QtWidgets.QTableWidgetItem()
            self.tblAlertas.setHorizontalHeaderItem(col, item)
        self.verticalLayout.addWidget(self.tblAlertas)

        self.lblVencimientos = BodyLabel(parent=Form)
        self.lblVencimientos.setObjectName("lblVencimientos")
        self.verticalLayout.addWidget(self.lblVencimientos)

        self.tblVencimientos = TableWidget(parent=Form)
        self.tblVencimientos.setObjectName("tblVencimientos")
        self.tblVencimientos.setColumnCount(5)
        self.tblVencimientos.setRowCount(0)
        self.tblVencimientos.setBorderRadius(8)
        self.tblVencimientos.setBorderVisible(True)
        for col in range(5):
            item = QtWidgets.QTableWidgetItem()
            self.tblVencimientos.setHorizontalHeaderItem(col, item)
        self.verticalLayout.addWidget(self.tblVencimientos)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Alertas"))
        self.lblStock.setText(_translate("Form", "Productos bajo stock mínimo"))
        item = self.tblAlertas.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Codigo"))
        item = self.tblAlertas.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Nombre"))
        item = self.tblAlertas.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Stock Actual"))
        item = self.tblAlertas.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Stock Mínimo"))
        self.lblVencimientos.setText(_translate("Form", "Productos vencidos o por vencer"))
        item = self.tblVencimientos.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Codigo"))
        item = self.tblVencimientos.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Nombre"))
        item = self.tblVencimientos.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Vence"))
        item = self.tblVencimientos.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Situación"))
        item = self.tblVencimientos.horizontalHeaderItem(4)
        item.setText(_translate("Form", "Stock Actual"))
