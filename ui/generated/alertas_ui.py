

from PyQt6 import QtCore, QtGui, QtWidgets
import Recursos.Recursos_rc


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(520, 640)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblStock = QtWidgets.QLabel(parent=Form)
        self.lblStock.setObjectName("lblStock")
        self.verticalLayout.addWidget(self.lblStock)
        self.tblAlertas = QtWidgets.QTableWidget(parent=Form)
        self.tblAlertas.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tblAlertas.setObjectName("tblAlertas")
        self.tblAlertas.setColumnCount(4)
        self.tblAlertas.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tblAlertas.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tblAlertas.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tblAlertas.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tblAlertas.setHorizontalHeaderItem(3, item)
        self.tblAlertas.horizontalHeader().setDefaultSectionSize(101)
        self.verticalLayout.addWidget(self.tblAlertas)
        self.horizontalLayoutStock = QtWidgets.QHBoxLayout()
        self.horizontalLayoutStock.setObjectName("horizontalLayoutStock")
        spacerItem = QtWidgets.QSpacerItem(679, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayoutStock.addItem(spacerItem)
        self.btnExportar = QtWidgets.QPushButton(parent=Form)
        self.btnExportar.setObjectName("btnExportar")
        self.horizontalLayoutStock.addWidget(self.btnExportar)
        self.verticalLayout.addLayout(self.horizontalLayoutStock)
        self.lblVencimientos = QtWidgets.QLabel(parent=Form)
        self.lblVencimientos.setObjectName("lblVencimientos")
        self.verticalLayout.addWidget(self.lblVencimientos)
        self.tblVencimientos = QtWidgets.QTableWidget(parent=Form)
        self.tblVencimientos.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tblVencimientos.setObjectName("tblVencimientos")
        self.tblVencimientos.setColumnCount(5)
        self.tblVencimientos.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tblVencimientos.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tblVencimientos.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tblVencimientos.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tblVencimientos.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tblVencimientos.setHorizontalHeaderItem(4, item)
        self.tblVencimientos.horizontalHeader().setDefaultSectionSize(101)
        self.verticalLayout.addWidget(self.tblVencimientos)
        self.horizontalLayoutVencimientos = QtWidgets.QHBoxLayout()
        self.horizontalLayoutVencimientos.setObjectName("horizontalLayoutVencimientos")
        spacerItem1 = QtWidgets.QSpacerItem(679, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayoutVencimientos.addItem(spacerItem1)
        self.btnExportarVencimientos = QtWidgets.QPushButton(parent=Form)
        self.btnExportarVencimientos.setObjectName("btnExportarVencimientos")
        self.horizontalLayoutVencimientos.addWidget(self.btnExportarVencimientos)
        self.verticalLayout.addLayout(self.horizontalLayoutVencimientos)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        self.btnExportar.clicked.connect(self.exportar_csv)

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

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Alertas"))
        self.lblStock.setText(_translate("Form", "<html><head/><body><p><span style=\" font-size:9pt;\">Productos bajo stock mínimo</span></p></body></html>"))
        item = self.tblAlertas.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Codigo"))
        item = self.tblAlertas.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Nombre"))
        item = self.tblAlertas.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Stock Actual"))
        item = self.tblAlertas.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Stock Mínimo"))
        self.btnExportar.setText(_translate("Form", "Exportar stock"))
        self.lblVencimientos.setText(_translate("Form", "<html><head/><body><p><span style=\" font-size:9pt;\">Productos vencidos o por vencer</span></p></body></html>"))
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
