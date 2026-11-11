from PyQt6 import QtCore, QtGui, QtWidgets
from qfluentwidgets import (
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    TableWidget,
)
import Recursos.Recursos_rc


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(801, 490)
        self.layoutWidget = QtWidgets.QWidget(parent=Form)
        self.layoutWidget.setObjectName("layoutWidget")
        self.layoutWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(12)
        self.verticalLayout.setObjectName("verticalLayout")

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(8)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.label = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label.setObjectName("label")
        self.label.hide()
        self.horizontalLayout.addWidget(self.label)

        self.txtBuscar = SearchLineEdit(parent=self.layoutWidget)
        self.txtBuscar.setPlaceholderText("Buscar por código, nombre o categoría...")
        self.txtBuscar.setClearButtonEnabled(True)
        self.txtBuscar.setMinimumWidth(260)
        self.txtBuscar.setObjectName("txtBuscar")
        self.horizontalLayout.addWidget(self.txtBuscar)

        self.btnNuevo = PrimaryPushButton(FIF.ADD, "Nuevo Producto", parent=self.layoutWidget)
        self.btnNuevo.setObjectName("btnNuevo")
        self.horizontalLayout.addWidget(self.btnNuevo)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tblProductos = TableWidget(parent=self.layoutWidget)
        self.tblProductos.setColumnCount(6)
        self.tblProductos.setObjectName("tblProductos")
        self.tblProductos.setRowCount(0)
        self.tblProductos.setBorderRadius(8)
        self.tblProductos.setBorderVisible(True)

        for col in range(6):
            item = QtWidgets.QTableWidgetItem()
            self.tblProductos.setHorizontalHeaderItem(col, item)

        self.verticalLayout.addWidget(self.tblProductos)

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(8)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        self.btnEditar = PushButton(FIF.EDIT, "Editar", parent=self.layoutWidget)
        self.btnEditar.setObjectName("btnEditar")
        self.horizontalLayout_2.addWidget(self.btnEditar)

        self.btnEliminar = PushButton(FIF.DELETE, "Eliminar", parent=self.layoutWidget)
        self.btnEliminar.setObjectName("btnEliminar")
        self.horizontalLayout_2.addWidget(self.btnEliminar)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Productos"))
        self.label.setText(_translate("Form", "Buscar: "))
        self.btnNuevo.setText(_translate("Form", "Nuevo Producto"))
        item = self.tblProductos.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Código"))
        item = self.tblProductos.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Nombre"))
        item = self.tblProductos.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Categoria"))
        item = self.tblProductos.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Stock Actual"))
        item = self.tblProductos.horizontalHeaderItem(4)
        item.setText(_translate("Form", "Stock Minimo"))
        item = self.tblProductos.horizontalHeaderItem(5)
        item.setText(_translate("Form", "Precio"))
        self.btnEliminar.setText(_translate("Form", "Eliminar"))
        self.btnEditar.setText(_translate("Form", "Editar"))
