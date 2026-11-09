from PyQt6 import QtCore, QtWidgets

from ui.estilos import TAMANO_BODY, fuente


class Ui_FotosForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowTitle("Buscar Foto")
        Form.setMinimumSize(640, 600)

        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(16, 16, 16, 16)
        self.verticalLayout.setSpacing(10)

        self.hlyBuscar = QtWidgets.QHBoxLayout()
        self.hlyBuscar.setObjectName("hlyBuscar")

        self.txtBuscar = QtWidgets.QLineEdit(parent=Form)
        self.txtBuscar.setObjectName("txtBuscar")
        self.txtBuscar.setMinimumHeight(34)
        self.txtBuscar.setClearButtonEnabled(True)
        self.hlyBuscar.addWidget(self.txtBuscar, 1)

        self.btnBuscar = QtWidgets.QPushButton(parent=Form)
        self.btnBuscar.setObjectName("btnBuscar")
        self.btnBuscar.setMinimumHeight(34)
        self.btnBuscar.setMinimumWidth(110)
        self.hlyBuscar.addWidget(self.btnBuscar)

        self.verticalLayout.addLayout(self.hlyBuscar)

        self.lblEstado = QtWidgets.QLabel(parent=Form)
        font_estado = fuente(TAMANO_BODY)
        self.lblEstado.setFont(font_estado)
        self.lblEstado.setObjectName("lblEstado")
        self.lblEstado.setWordWrap(True)
        self.verticalLayout.addWidget(self.lblEstado)

        self.hlyMedio = QtWidgets.QHBoxLayout()
        self.hlyMedio.setObjectName("hlyMedio")
        self.hlyMedio.setSpacing(12)

        self.grdFotos = QtWidgets.QGridLayout()
        self.grdFotos.setObjectName("grdFotos")
        self.grdFotos.setSpacing(8)

        self.btnFotos: list[QtWidgets.QPushButton] = []
        for indice in range(6):
            boton = QtWidgets.QPushButton(parent=Form)
            boton.setObjectName(f"btnFoto{indice}")
            boton.setFixedSize(110, 110)
            boton.setIconSize(QtCore.QSize(100, 100))
            boton.setEnabled(False)
            self.grdFotos.addWidget(boton, indice // 2, indice % 2)
            self.btnFotos.append(boton)

        self.hlyMedio.addLayout(self.grdFotos)

        self.vlyVista = QtWidgets.QVBoxLayout()
        self.vlyVista.setObjectName("vlyVista")
        self.vlyVista.setSpacing(6)

        self.lblVista = QtWidgets.QLabel(parent=Form)
        self.lblVista.setObjectName("lblVista")
        self.lblVista.setMinimumSize(250, 250)
        self.lblVista.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblVista.setStyleSheet("border: 1px solid #CCC; background-color: #F8F8F8;")
        self.vlyVista.addWidget(self.lblVista)

        self.lblTitulo = QtWidgets.QLabel(parent=Form)
        self.lblTitulo.setObjectName("lblTitulo")
        self.lblTitulo.setWordWrap(True)
        self.vlyVista.addWidget(self.lblTitulo)

        spacer_vista = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.vlyVista.addItem(spacer_vista)

        self.hlyMedio.addLayout(self.vlyVista, 1)

        self.verticalLayout.addLayout(self.hlyMedio, 1)

        self.hlyUrl = QtWidgets.QHBoxLayout()
        self.hlyUrl.setObjectName("hlyUrl")

        self.txtUrl = QtWidgets.QLineEdit(parent=Form)
        self.txtUrl.setObjectName("txtUrl")
        self.txtUrl.setMinimumHeight(32)
        self.txtUrl.setClearButtonEnabled(True)
        self.hlyUrl.addWidget(self.txtUrl, 1)

        self.btnUrl = QtWidgets.QPushButton(parent=Form)
        self.btnUrl.setObjectName("btnUrl")
        self.btnUrl.setMinimumHeight(32)
        self.hlyUrl.addWidget(self.btnUrl)

        self.verticalLayout.addLayout(self.hlyUrl)

        self.hlyBotones = QtWidgets.QHBoxLayout()
        self.hlyBotones.setObjectName("hlyBotones")

        spacer_btn = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.hlyBotones.addItem(spacer_btn)

        self.btnGuardar = QtWidgets.QPushButton(parent=Form)
        font_guardar = fuente(TAMANO_BODY, negrita=True)
        self.btnGuardar.setFont(font_guardar)
        self.btnGuardar.setObjectName("btnGuardar")
        self.btnGuardar.setMinimumHeight(38)
        self.btnGuardar.setMinimumWidth(140)
        self.btnGuardar.setEnabled(False)
        self.hlyBotones.addWidget(self.btnGuardar)

        self.btnCancelar = QtWidgets.QPushButton(parent=Form)
        self.btnCancelar.setObjectName("btnCancelar")
        self.btnCancelar.setMinimumHeight(38)
        self.hlyBotones.addWidget(self.btnCancelar)

        self.verticalLayout.addLayout(self.hlyBotones)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Buscar Foto"))
        self.txtBuscar.setPlaceholderText(_translate("Form", "Nombre o código del producto"))
        self.btnBuscar.setText(_translate("Form", "Buscar"))
        self.lblEstado.setText(_translate("Form", ""))
        self.lblVista.setText(_translate("Form", "Sin vista previa"))
        self.lblTitulo.setText(_translate("Form", ""))
        self.txtUrl.setPlaceholderText(_translate("Form", "…o pegá la URL de una imagen"))
        self.btnUrl.setText(_translate("Form", "Usar URL"))
        self.btnGuardar.setText(_translate("Form", "Guardar foto"))
        self.btnCancelar.setText(_translate("Form", "Cancelar"))
