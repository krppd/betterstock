from PyQt6 import QtCore, QtWidgets

from ui.estilos import TAMANO_BODY, TAMANO_DISPLAY, TAMANO_SUBTITLE, VERDE_TEXTO, fuente
from ui.widgets.etiqueta_rodante import EtiquetaRodante

class Ui_VentasForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(821, 570)
        
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        self.lblCodigo = QtWidgets.QLabel(parent=Form)
        font = fuente(TAMANO_BODY)
        self.lblCodigo.setFont(font)
        self.lblCodigo.setObjectName("lblCodigo")
        self.horizontalLayout.addWidget(self.lblCodigo)
        
        self.txtCodigoBarras = QtWidgets.QLineEdit(parent=Form)
        self.txtCodigoBarras.setFont(font)
        self.txtCodigoBarras.setObjectName("txtCodigoBarras")
        self.txtCodigoBarras.setToolTip(
            "Escaneá el código o escribí 3*1001 para agregar 3 unidades")
        self.horizontalLayout.addWidget(self.txtCodigoBarras)
        
        self.btnAgregar = QtWidgets.QPushButton(parent=Form)
        self.btnAgregar.setFont(font)
        self.btnAgregar.setObjectName("btnAgregar")
        self.horizontalLayout.addWidget(self.btnAgregar)
        
        self.btnQuitar = QtWidgets.QPushButton(parent=Form)
        self.btnQuitar.setFont(font)
        self.btnQuitar.setObjectName("btnQuitar")
        self.horizontalLayout.addWidget(self.btnQuitar)
        
        self.btnComodin = QtWidgets.QPushButton("Comodín", parent=Form)
        self.btnComodin.setFont(font)
        self.btnComodin.setObjectName("btnComodin")
        self.btnComodin.setToolTip("Vender algo que no está en el catálogo (Alt+O)")
        self.horizontalLayout.addWidget(self.btnComodin)
        
        self.verticalLayout.addLayout(self.horizontalLayout)
        
        self.tblVentas = QtWidgets.QTableWidget(parent=Form)
        self.tblVentas.setColumnCount(5)
        self.tblVentas.setObjectName("tblVentas")
        self.tblVentas.setRowCount(0)
        
        headers = ["Código", "Nombre", "Precio Venta", "Cantidad", "Subtotal"]
        for i, header in enumerate(headers):
            item = QtWidgets.QTableWidgetItem()
            item.setText(header)
            self.tblVentas.setHorizontalHeaderItem(i, item)
            
        self.tblVentas.horizontalHeader().setDefaultSectionSize(150)
        self.tblVentas.horizontalHeader().setStretchLastSection(True)
        self.tblVentas.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblVentas.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tblVentas.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.verticalLayout.addWidget(self.tblVentas)
        
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        
        self.lblTotalTxt = QtWidgets.QLabel(parent=Form)
        font_total_txt = fuente(TAMANO_SUBTITLE, negrita=True)
        self.lblTotalTxt.setFont(font_total_txt)
        self.lblTotalTxt.setObjectName("lblTotalTxt")
        self.horizontalLayout_2.addWidget(self.lblTotalTxt)
        
        self.lblTotal = EtiquetaRodante(parent=Form)
        font_total = fuente(TAMANO_DISPLAY, negrita=True, tabular=True)
        self.lblTotal.setFont(font_total)
        self.lblTotal.setStyleSheet(f"color: {VERDE_TEXTO};")
        self.lblTotal.setObjectName("lblTotal")
        self.horizontalLayout_2.addWidget(self.lblTotal)
        
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        
        self.lyBarraAcciones = QtWidgets.QHBoxLayout()
        self.lyBarraAcciones.setObjectName("lyBarraAcciones")
        self.lyBarraAcciones.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.addLayout(self.lyBarraAcciones)
        
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Punto de Venta"))
        self.lblCodigo.setText(_translate("Form", "Código de Barras:"))
        self.btnAgregar.setText(_translate("Form", "&Agregar"))
        self.btnQuitar.setText(_translate("Form", "&Quitar"))
        self.lblTotalTxt.setText(_translate("Form", "TOTAL:"))
        self.lblTotal.setText(_translate("Form", "$ 0,00"))
