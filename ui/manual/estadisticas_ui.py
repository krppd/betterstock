from PyQt6 import QtCore, QtWidgets

from ui.estilos import (
    BORDE,
    GRIS_BOTON,
    GRIS_HOVER,
    GRIS_TEXTO,
    TAMANO_MICRO,
    TAMANO_SUBTITLE,
    TEXTO,
    fuente,
)


class Ui_EstadisticasForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(780, 660)

        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(16, 16, 16, 16)
        self.verticalLayout.setSpacing(10)

        self.grafico = QtWidgets.QWidget(parent=Form)
        self.lyGrafico = QtWidgets.QVBoxLayout(self.grafico)
        self.lyGrafico.setContentsMargins(0, 0, 0, 0)
        self.grafico.setObjectName("grafico")
        self.grafico.setMinimumHeight(190)
        self.verticalLayout.addWidget(self.grafico)

        self.hlyPeriodo = QtWidgets.QHBoxLayout()
        self.hlyPeriodo.setObjectName("hlyPeriodo")

        self.lblPeriodo = QtWidgets.QLabel(parent=Form)
        self.lblPeriodo.setObjectName("lblPeriodo")
        self.hlyPeriodo.addWidget(self.lblPeriodo)

        self.cmbPeriodo = QtWidgets.QComboBox(parent=Form)
        self.cmbPeriodo.setObjectName("cmbPeriodo")
        self.cmbPeriodo.addItems(["Hoy", "Mes actual", "Mes anterior", "Últimos 30 días"])
        self.hlyPeriodo.addWidget(self.cmbPeriodo)

        spacer = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.hlyPeriodo.addItem(spacer)

        self.btnActualizar = QtWidgets.QPushButton(parent=Form)
        self.btnActualizar.setObjectName("btnActualizar")
        self.btnActualizar.setMinimumHeight(32)
        self.hlyPeriodo.addWidget(self.btnActualizar)

        self.verticalLayout.addLayout(self.hlyPeriodo)

        self.lblPlan = QtWidgets.QLabel(parent=Form)
        self.lblPlan.setObjectName("lblPlan")
        self.lblPlan.setFont(fuente(TAMANO_MICRO))
        self.lblPlan.setStyleSheet(f"color: {GRIS_TEXTO};")
        self.verticalLayout.addWidget(self.lblPlan)

        self.lblRango = QtWidgets.QLabel(parent=Form)
        font_rango = fuente(TAMANO_MICRO)
        font_rango.setItalic(True)
        self.lblRango.setFont(font_rango)
        self.lblRango.setObjectName("lblRango")
        self.lblRango.setStyleSheet(
            "QLabel#lblRango { background-color: #FFFFFF; "
            "border: 1px solid #E2E8F0; border-radius: 8px; "
            "padding: 6px 10px; }"
        )
        self.verticalLayout.addWidget(self.lblRango)

        self.glyTarjetas = QtWidgets.QGridLayout()
        self.glyTarjetas.setObjectName("glyTarjetas")
        self.glyTarjetas.setSpacing(8)

        self.lblVentasTitulo = QtWidgets.QLabel(parent=Form)
        self.lblVentasValor = QtWidgets.QLabel(parent=Form)
        self.lblVentasVariacion = QtWidgets.QLabel(parent=Form)

        self.lblUnidadesTitulo = QtWidgets.QLabel(parent=Form)
        self.lblUnidadesValor = QtWidgets.QLabel(parent=Form)
        self.lblUnidadesVariacion = QtWidgets.QLabel(parent=Form)

        self.lblTotalTitulo = QtWidgets.QLabel(parent=Form)
        self.lblTotalValor = QtWidgets.QLabel(parent=Form)
        self.lblTotalVariacion = QtWidgets.QLabel(parent=Form)

        self.lblTicketTitulo = QtWidgets.QLabel(parent=Form)
        self.lblTicketValor = QtWidgets.QLabel(parent=Form)
        self.lblTicketVariacion = QtWidgets.QLabel(parent=Form)

        tarjetas = [
            (self.lblVentasTitulo, self.lblVentasValor, self.lblVentasVariacion),
            (self.lblUnidadesTitulo, self.lblUnidadesValor, self.lblUnidadesVariacion),
            (self.lblTotalTitulo, self.lblTotalValor, self.lblTotalVariacion),
            (self.lblTicketTitulo, self.lblTicketValor, self.lblTicketVariacion),
        ]
        for columna, (titulo, valor, variacion) in enumerate(tarjetas):
            marco = QtWidgets.QFrame(parent=Form)
            marco.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            lay = QtWidgets.QVBoxLayout(marco)
            lay.setContentsMargins(10, 8, 10, 8)
            lay.setSpacing(2)

            font_titulo = fuente(TAMANO_MICRO)
            titulo.setFont(font_titulo)
            titulo.setStyleSheet(f"color: {GRIS_TEXTO};")
            lay.addWidget(titulo)

            font_valor = fuente(TAMANO_SUBTITLE, negrita=True, tabular=True)
            valor.setFont(font_valor)
            valor.setStyleSheet(f"color: {TEXTO};")
            lay.addWidget(valor)

            font_var = fuente(TAMANO_MICRO)
            variacion.setFont(font_var)
            lay.addWidget(variacion)

            self.glyTarjetas.addWidget(marco, 0, columna)

        self.verticalLayout.addLayout(self.glyTarjetas)

        self.hlyVentas = QtWidgets.QHBoxLayout()
        self.hlyVentas.setObjectName("hlyVentas")

        self.btnVentas = QtWidgets.QPushButton(parent=Form)
        self.btnVentas.setObjectName("btnVentas")
        self.btnVentas.setCheckable(True)
        self.hlyVentas.addWidget(self.btnVentas)

        self.btnRanking = QtWidgets.QPushButton(parent=Form)
        self.btnRanking.setObjectName("btnRanking")
        self.btnRanking.setCheckable(True)
        self.hlyVentas.addWidget(self.btnRanking)

        spacer_ventas = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.hlyVentas.addItem(spacer_ventas)

        self.btnDetalle = QtWidgets.QPushButton(parent=Form)
        self.btnDetalle.setObjectName("btnDetalle")
        self.btnDetalle.setMinimumHeight(28)
        self.btnDetalle.setMaximumWidth(120)
        self.btnDetalle.setStyleSheet(
            "QPushButton#btnDetalle { background-color: #FFFFFF; "
            f"border: 1px solid {BORDE}; border-radius: 6px; "
            "padding: 6px 12px; }"
            f"QPushButton#btnDetalle:hover {{ background-color: {GRIS_BOTON}; }}"
            f"QPushButton#btnDetalle:pressed {{ background-color: {GRIS_HOVER}; }}"
        )
        self.hlyVentas.addWidget(self.btnDetalle)

        self.verticalLayout.addLayout(self.hlyVentas)

        self.stackVentas = QtWidgets.QStackedWidget(parent=Form)
        self.stackVentas.setObjectName("stackVentas")

        self.tblVentas = QtWidgets.QTableWidget(parent=self.stackVentas)
        self.tblVentas.setObjectName("tblVentas")
        self.tblVentas.setColumnCount(6)
        self.tblVentas.setRowCount(0)
        for i, texto in enumerate(["Hora", "Unidades", "Total", "Medio", "Detalle", "Estado"]):
            item = QtWidgets.QTableWidgetItem()
            item.setText(texto)
            self.tblVentas.setHorizontalHeaderItem(i, item)
        self.tblVentas.horizontalHeader().setStretchLastSection(True)
        self.tblVentas.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tblVentas.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.stackVentas.addWidget(self.tblVentas)

        self.tblRanking = QtWidgets.QTableWidget(parent=self.stackVentas)
        self.tblRanking.setObjectName("tblRanking")
        self.tblRanking.setColumnCount(4)
        self.tblRanking.setRowCount(0)
        for i, texto in enumerate(["Producto", "Unidades", "Total", "% del total"]):
            item = QtWidgets.QTableWidgetItem()
            item.setText(texto)
            self.tblRanking.setHorizontalHeaderItem(i, item)
        self.tblRanking.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tblRanking.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.stackVentas.addWidget(self.tblRanking)

        self.verticalLayout.addWidget(self.stackVentas, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Estadísticas de ventas"))
        self.lblPeriodo.setText(_translate("Form", "Período:"))
        self.lblPlan.setText(_translate("Form", ""))
        self.btnActualizar.setText(_translate("Form", "Actualizar"))
        self.lblRango.setText(_translate("Form", ""))
        self.lblVentasTitulo.setText(_translate("Form", "Ventas"))
        self.lblVentasValor.setText(_translate("Form", "0"))
        self.lblUnidadesTitulo.setText(_translate("Form", "Unidades"))
        self.lblUnidadesValor.setText(_translate("Form", "0"))
        self.lblTotalTitulo.setText(_translate("Form", "Facturado"))
        self.lblTotalValor.setText(_translate("Form", "$ 0,00"))
        self.lblTicketTitulo.setText(_translate("Form", "Ticket promedio"))
        self.lblTicketValor.setText(_translate("Form", "$ 0,00"))
        self.btnVentas.setText(_translate("Form", "Ventas"))
        self.btnRanking.setText(_translate("Form", "Más vendidos"))
        self.btnDetalle.setText(_translate("Form", "Detalles"))