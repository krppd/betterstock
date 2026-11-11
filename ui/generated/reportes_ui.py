from PyQt6 import QtCore, QtGui, QtWidgets
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    DateEdit,
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    TableWidget,
)
import Recursos.Recursos_rc


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(565, 550)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setSpacing(10)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setSpacing(8)
        self.lblDesde = BodyLabel(parent=Form)
        self.lblDesde.setObjectName("lblDesde")
        self.horizontalLayout.addWidget(self.lblDesde)
        self.dateDesde = DateEdit(parent=Form)
        self.dateDesde.setObjectName("dateDesde")
        self.dateDesde.setCalendarPopup(True)
        self.dateDesde.setSymbolVisible(False)
        self.horizontalLayout.addWidget(self.dateDesde)
        spacerItem = QtWidgets.QSpacerItem(24, 20, QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.lblHasta = BodyLabel(parent=Form)
        self.lblHasta.setObjectName("lblHasta")
        self.horizontalLayout.addWidget(self.lblHasta)
        self.dateHasta = DateEdit(parent=Form)
        self.dateHasta.setObjectName("dateHasta")
        self.dateHasta.setCalendarPopup(True)
        self.dateHasta.setSymbolVisible(False)
        self.horizontalLayout.addWidget(self.dateHasta)
        spacerItem1 = QtWidgets.QSpacerItem(24, 20, QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.lblTipo = BodyLabel(parent=Form)
        self.lblTipo.setObjectName("lblTipo")
        self.horizontalLayout.addWidget(self.lblTipo)
        self.cmbTipo = ComboBox(parent=Form)
        self.cmbTipo.setObjectName("cmbTipo")
        self.cmbTipo.addItem("")
        self.cmbTipo.addItem("")
        self.cmbTipo.addItem("")
        self.cmbTipo.addItem("")
        self.horizontalLayout.addWidget(self.cmbTipo)
        spacerItem2 = QtWidgets.QSpacerItem(18, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.btnFiltrar = PrimaryPushButton(FIF.SEARCH, "Filtrar", parent=Form)
        self.btnFiltrar.setObjectName("btnFiltrar")
        self.horizontalLayout.addWidget(self.btnFiltrar)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tableWidget = TableWidget(parent=Form)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setBorderRadius(8)
        self.tableWidget.setBorderVisible(True)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        self.verticalLayout.addWidget(self.tableWidget)

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout_2.setSpacing(8)
        self.lblTotal = BodyLabel(parent=Form)
        self.lblTotal.setObjectName("lblTotal")
        self.horizontalLayout_2.addWidget(self.lblTotal)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.btnExportarPDF = PushButton(FIF.PRINT, "Exportar PDF", parent=Form)
        self.btnExportarPDF.setObjectName("btnExportarPDF")
        self.horizontalLayout_2.addWidget(self.btnExportarPDF)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.btnExportarCSV = PushButton(FIF.SAVE, "Exportar CSV", parent=Form)
        self.btnExportarCSV.setObjectName("btnExportarCSV")
        self.horizontalLayout_2.addWidget(self.btnExportarCSV)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        # --- INICIO CODIGO MANUAL ---
        self.btnExportarCSV.clicked.connect(self.exportar_csv)
        self.btnExportarPDF.clicked.connect(self.exportar_pdf)
        # --- FIN CODIGO MANUAL ---

    # --- INICIO CODIGO MANUAL ---
    def exportar_csv(self):
        import csv
        from PyQt6 import QtWidgets

        path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Guardar Reporte CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                headers = []
                for column in range(self.tableWidget.columnCount()):
                    header_item = self.tableWidget.horizontalHeaderItem(column)
                    headers.append(header_item.text() if header_item else "")
                writer.writerow(headers)

                for row in range(self.tableWidget.rowCount()):
                    row_data = []
                    for column in range(self.tableWidget.columnCount()):
                        item = self.tableWidget.item(row, column)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QtWidgets.QMessageBox.information(None, "Éxito", "Reporte exportado a CSV correctamente.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "Error", f"No se pudo exportar el archivo:\n{str(e)}")
    # --- FIN CODIGO MANUAL ---
    # --- INICIO CODIGO MANUAL ---
    def exportar_pdf(self):
        from PyQt6 import QtWidgets, QtGui
        from PyQt6.QtPrintSupport import QPrinter

        path, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Guardar Reporte PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)

            html = "<h1 style='text-align: center;'>Reporte de Movimientos</h1>"
            html += "<table border='1' cellspacing='0' cellpadding='4' width='100%'>"

            html += "<tr>"
            for column in range(self.tableWidget.columnCount()):
                header_item = self.tableWidget.horizontalHeaderItem(column)
                text = header_item.text() if header_item else ""
                html += f"<th style='background-color: #f2f2f2;'>{text}</th>"
            html += "</tr>"

            for row in range(self.tableWidget.rowCount()):
                html += "<tr>"
                for column in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, column)
                    text = item.text() if item else ""
                    html += f"<td>{text}</td>"
                html += "</tr>"

            html += "</table>"

            total_text = self.lblTotal.text()
            html += f"<br><br><h3>{total_text}</h3>"

            document = QtGui.QTextDocument()
            document.setHtml(html)
            document.print(printer)

            QtWidgets.QMessageBox.information(None, "Éxito", "Reporte exportado a PDF correctamente.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "Error", f"No se pudo exportar el archivo:\n{str(e)}")
    # --- FIN CODIGO MANUAL ---

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Reportes"))
        self.lblDesde.setText(_translate("Form", "Desde:"))
        self.dateDesde.setDisplayFormat(_translate("Form", "dd/MM/yyyy"))
        self.lblHasta.setText(_translate("Form", "Hasta:"))
        self.dateHasta.setDisplayFormat(_translate("Form", "dd/MM/yyyy"))
        self.lblTipo.setText(_translate("Form", "Tipo:"))
        self.cmbTipo.setItemText(0, _translate("Form", "Todos"))
        self.cmbTipo.setItemText(1, _translate("Form", "Entrada"))
        self.cmbTipo.setItemText(2, _translate("Form", "Salida"))
        self.cmbTipo.setItemText(3, _translate("Form", "Ajuste"))
        self.btnFiltrar.setText(_translate("Form", "Filtrar"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Fecha"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Producto"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Tipo"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Cantidad"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("Form", "Precio"))
        self.lblTotal.setText(_translate("Form", "Stock total valorizado: $0.00"))
        self.btnExportarPDF.setText(_translate("Form", "Exportar PDF"))
        self.btnExportarCSV.setText(_translate("Form", "Exportar CSV"))
