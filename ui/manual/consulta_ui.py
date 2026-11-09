from PyQt6 import QtCore, QtWidgets

from ui.estilos import (
    TAMANO_BODY,
    TAMANO_DISPLAY,
    TAMANO_HERO,
    TAMANO_SMALL,
    TAMANO_TITLE,
    VERDE_TEXTO,
    fuente,
)
from ui.widgets.etiqueta_texto import EtiquetaTexto


class Ui_ConsultaForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowTitle("Consultar Precio")
        Form.setMinimumSize(700, 560)

        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(24, 20, 24, 20)
        self.verticalLayout.setSpacing(12)

        self.hlyBuscar = QtWidgets.QHBoxLayout()
        self.hlyBuscar.setObjectName("hlyBuscar")

        self.lblBuscar = QtWidgets.QLabel(parent=Form)
        font_buscar = fuente(TAMANO_BODY)
        self.lblBuscar.setFont(font_buscar)
        self.lblBuscar.setObjectName("lblBuscar")
        self.hlyBuscar.addWidget(self.lblBuscar)

        self.txtBuscar = QtWidgets.QLineEdit(parent=Form)
        font_campo = fuente(TAMANO_TITLE)
        self.txtBuscar.setFont(font_campo)
        self.txtBuscar.setObjectName("txtBuscar")
        self.txtBuscar.setMinimumHeight(48)
        self.txtBuscar.setClearButtonEnabled(True)
        self.hlyBuscar.addWidget(self.txtBuscar, 1)

        self.btnBuscar = QtWidgets.QPushButton(parent=Form)
        self.btnBuscar.setObjectName("btnBuscar")
        self.btnBuscar.setMinimumHeight(48)
        self.btnBuscar.setMinimumWidth(140)
        self.hlyBuscar.addWidget(self.btnBuscar)

        self.verticalLayout.addLayout(self.hlyBuscar)

        self.lblEstado = QtWidgets.QLabel(parent=Form)
        font_estado = fuente(TAMANO_SMALL)
        self.lblEstado.setFont(font_estado)
        self.lblEstado.setObjectName("lblEstado")
        self.lblEstado.setWordWrap(True)
        self.verticalLayout.addWidget(self.lblEstado)

        self.lstCoincidencias = QtWidgets.QListWidget(parent=Form)
        self.lstCoincidencias.setObjectName("lstCoincidencias")
        self.lstCoincidencias.setMaximumHeight(160)
        self.lstCoincidencias.setVisible(False)
        self.verticalLayout.addWidget(self.lstCoincidencias)

        self.lblNombre = EtiquetaTexto(parent=Form)
        font_nombre = fuente(TAMANO_DISPLAY, negrita=True)
        self.lblNombre.setFont(font_nombre)
        self.lblNombre.setObjectName("lblNombre")
        self.verticalLayout.addWidget(self.lblNombre)

        self.lblCodigo = EtiquetaTexto(parent=Form)
        self.lblCodigo.setObjectName("lblCodigo")
        self.verticalLayout.addWidget(self.lblCodigo)

        self.hlyDetalle = QtWidgets.QHBoxLayout()
        self.hlyDetalle.setObjectName("hlyDetalle")
        self.hlyDetalle.setSpacing(16)

        self.vlyDatos = QtWidgets.QVBoxLayout()
        self.vlyDatos.setObjectName("vlyDatos")
        self.vlyDatos.setSpacing(6)

        self.lblPrecio = QtWidgets.QLabel(parent=Form)
        font_precio = fuente(TAMANO_HERO, negrita=True, tabular=True)
        self.lblPrecio.setFont(font_precio)
        self.lblPrecio.setObjectName("lblPrecio")
        self.lblPrecio.setStyleSheet(f"color: {VERDE_TEXTO};")
        self.vlyDatos.addWidget(self.lblPrecio)

        self.lblOferta = QtWidgets.QLabel(parent=Form)
        font_oferta = fuente(TAMANO_BODY, negrita=True)
        self.lblOferta.setFont(font_oferta)
        self.lblOferta.setObjectName("lblOferta")
        self.lblOferta.setStyleSheet(
            "background-color: #FFF3CD; color: #856404; padding: 6px;")
        self.lblOferta.setVisible(False)
        self.vlyDatos.addWidget(self.lblOferta)

        self.lblStock = QtWidgets.QLabel(parent=Form)
        font_stock = fuente(TAMANO_BODY, tabular=True)
        self.lblStock.setFont(font_stock)
        self.lblStock.setObjectName("lblStock")
        self.vlyDatos.addWidget(self.lblStock)

        spacer_datos = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.vlyDatos.addItem(spacer_datos)

        self.hlyDetalle.addLayout(self.vlyDatos, 3)

        self.vlyImagen = QtWidgets.QVBoxLayout()
        self.vlyImagen.setObjectName("vlyImagen")

        self.lblImagen = QtWidgets.QLabel(parent=Form)
        self.lblImagen.setObjectName("lblImagen")
        self.lblImagen.setMinimumSize(260, 260)
        self.lblImagen.setMaximumSize(340, 340)
        self.lblImagen.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblImagen.setStyleSheet("border: 1px solid #CCC; background-color: #F8F8F8;")
        self.lblImagen.setScaledContents(False)
        self.vlyImagen.addWidget(self.lblImagen)

        self.hlyDetalle.addLayout(self.vlyImagen, 1)

        self.verticalLayout.addLayout(self.hlyDetalle, 1)

        self.hlyBotones = QtWidgets.QHBoxLayout()
        self.hlyBotones.setObjectName("hlyBotones")

        self.btnAlta = QtWidgets.QPushButton(parent=Form)
        self.btnAlta.setObjectName("btnAlta")
        self.btnAlta.setMinimumHeight(44)
        self.btnAlta.setVisible(False)
        self.hlyBotones.addWidget(self.btnAlta)

        spacer_btn = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.hlyBotones.addItem(spacer_btn)

        self.btnLimpiar = QtWidgets.QPushButton(parent=Form)
        self.btnLimpiar.setObjectName("btnLimpiar")
        self.btnLimpiar.setMinimumHeight(44)
        self.hlyBotones.addWidget(self.btnLimpiar)

        self.verticalLayout.addLayout(self.hlyBotones)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Consultar Precio"))
        self.lblBuscar.setText(_translate("Form", "Código o nombre:"))
        self.txtBuscar.setPlaceholderText(
            _translate("Form", "Escaneá o escribí y apretá Enter"))
        self.btnBuscar.setText(_translate("Form", "Buscar"))
        self.lblEstado.setText(_translate("Form", ""))
        self.lblNombre.setText(_translate("Form", ""))
        self.lblCodigo.setText(_translate("Form", ""))
        self.lblPrecio.setText(_translate("Form", ""))
        self.lblOferta.setText(_translate("Form", ""))
        self.lblStock.setText(_translate("Form", ""))
        self.lblImagen.setText(_translate("Form", "Sin imagen"))
        self.btnAlta.setText(_translate("Form", "Dar de alta con este código"))
        self.btnLimpiar.setText(_translate("Form", "Limpiar"))
