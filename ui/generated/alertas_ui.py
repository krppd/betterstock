from PyQt6 import QtCore, QtGui, QtWidgets
from qfluentwidgets import (
    BodyLabel,
    FluentIcon as FIF,
    PushButton,
    TableWidget,
)
import Recursos.Recursos_rc


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

        self.horizontalLayoutStock = QtWidgets.QHBoxLayout()
        self.horizontalLayoutStock.setObjectName("horizontalLayoutStock")
        spacerItem = QtWidgets.QSpacerItem(679, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayoutStock.addItem(spacerItem)
        self.btnExportar = PushButton(FIF.DOWNLOAD, "Exportar stock", parent=Form)
        self.btnExportar.setObjectName("btnExportar")
        self.horizontalLayoutStock.addWidget(self.btnExportar)
        self.verticalLayout.addLayout(self.horizontalLayoutStock)

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

        self.horizontalLayoutVencimientos = QtWidgets.QHBoxLayout()
        self.horizontalLayoutVencimientos.setObjectName("horizontalLayoutVencimientos")
        spacerItem1 = QtWidgets.QSpacerItem(679, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayoutVencimientos.addItem(spacerItem1)
        self.btnExportarVencimientos = PushButton(FIF.DOWNLOAD, "Exportar vencimientos", parent=Form)
        self.btnExportarVencimientos.setObjectName("btnExportarVencimientos")
        self.horizontalLayoutVencimientos.addWidget(self.btnExportarVencimientos)
        self.verticalLayout.addLayout(self.horizontalLayoutVencimientos)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        # --- INICIO CODIGO MANUAL ---
        self.btnExportar.clicked.connect(self.exportar_csv)
        # --- FIN CODIGO MANUAL ---

    # --- INICIO CODIGO MANUAL ---
    def exportar_csv(self):
        import csv
        from PyQt6 import QtWidgets

        path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Guardar Alertas CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                headers = []
                for column in range(self.tblAlertas.columnCount()):
                    header_item = self.tblAlertas.horizontalHeaderItem(column)
                    headers.append(header_item.text() if header_item else "")
                writer.writerow(headers)

                for row in range(self.tblAlertas.rowCount()):
                    row_data = []
                    for column in range(self.tblAlertas.columnCount()):
                        item = self.tblAlertas.item(row, column)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QtWidgets.QMessageBox.information(None, "Éxito", "Alertas exportadas a CSV correctamente.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "Error", f"No se pudo exportar el archivo:\n{str(e)}")
    # --- FIN CODIGO MANUAL ---

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
        self.btnExportar.setText(_translate("Form", "Exportar stock"))
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
        self.btnExportarVencimientos.setText(_translate("Form", "Exportar vencimientos"))
