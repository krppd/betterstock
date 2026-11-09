from PyQt6 import QtCore, QtWidgets

from ui.estilos import ROJO_TEXTO, TAMANO_BODY, TAMANO_MICRO, VERDE, fuente

TITULO_INICIAL = "Configuración inicial"
TITULO_EDICION = "Datos del comercio"
TEXTO_INICIAL = (
    "Bienvenido a BetterStock.\nCompletá los datos de tu comercio; "
    "después no vuelve a pedirselos."
)
TEXTO_EDICION = "Datos del comercio.\nModificá los datos cuando los necesites."
BUTTON_INICIAL = "Guardar y continuar"
BUTTON_EDICION = "Guardar cambios"


class Ui_ConfiguracionForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowTitle(TITULO_INICIAL)
        Form.setFixedSize(480, 360)

        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout.setSpacing(12)

        self.lblTitulo = QtWidgets.QLabel(parent=Form)
        font_titulo = fuente(TAMANO_BODY, negrita=True)
        self.lblTitulo.setFont(font_titulo)
        self.lblTitulo.setObjectName("lblTitulo")
        self.lblTitulo.setWordWrap(True)
        self.verticalLayout.addWidget(self.lblTitulo)

        self.lblNombre = QtWidgets.QLabel(parent=Form)
        self.lblNombre.setObjectName("lblNombre")
        self.verticalLayout.addWidget(self.lblNombre)

        self.txtNombre = QtWidgets.QLineEdit(parent=Form)
        self.txtNombre.setObjectName("txtNombre")
        self.txtNombre.setPlaceholderText("Ej: verdulería de barrio")
        self.txtNombre.setMinimumHeight(28)
        self.verticalLayout.addWidget(self.txtNombre)

        self.lblDireccion = QtWidgets.QLabel(parent=Form)
        self.lblDireccion.setObjectName("lblDireccion")
        self.verticalLayout.addWidget(self.lblDireccion)

        self.txtDireccion = QtWidgets.QLineEdit(parent=Form)
        self.txtDireccion.setObjectName("txtDireccion")
        self.txtDireccion.setPlaceholderText("Ej: artube 1232")
        self.txtDireccion.setMinimumHeight(28)
        self.verticalLayout.addWidget(self.txtDireccion)

        self.lblCuit = QtWidgets.QLabel(parent=Form)
        self.lblCuit.setObjectName("lblCuit")
        self.verticalLayout.addWidget(self.lblCuit)

        self.txtCuit = QtWidgets.QLineEdit(parent=Form)
        self.txtCuit.setObjectName("txtCuit")
        self.txtCuit.setPlaceholderText("Ej: 30-12345678-9")
        self.txtCuit.setMinimumHeight(28)
        self.verticalLayout.addWidget(self.txtCuit)

        self.lblTelefono = QtWidgets.QLabel(parent=Form)
        self.lblTelefono.setObjectName("lblTelefono")
        self.verticalLayout.addWidget(self.lblTelefono)

        self.txtTelefono = QtWidgets.QLineEdit(parent=Form)
        self.txtTelefono.setObjectName("txtTelefono")
        self.txtTelefono.setPlaceholderText("Ej: 1166666666")
        self.txtTelefono.setMinimumHeight(28)
        self.verticalLayout.addWidget(self.txtTelefono)

        self.lblError = QtWidgets.QLabel(parent=Form)
        font_error = fuente(TAMANO_MICRO)
        self.lblError.setFont(font_error)
        self.lblError.setStyleSheet(f"color: {ROJO_TEXTO};")
        self.lblError.setObjectName("lblError")
        self.lblError.setWordWrap(True)
        self.verticalLayout.addWidget(self.lblError)

        spacerItem = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.verticalLayout.addItem(spacerItem)

        self.btnGuardar = QtWidgets.QPushButton(parent=Form)
        font_guardar = fuente(TAMANO_BODY, negrita=True)
        self.btnGuardar.setFont(font_guardar)
        self.btnGuardar.setObjectName("btnGuardar")
        self.btnGuardar.setMinimumHeight(42)
        self.btnGuardar.setStyleSheet(f"background-color: {VERDE}; color: white;")
        self.verticalLayout.addWidget(self.btnGuardar)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", TITULO_INICIAL))
        self.lblTitulo.setText(_translate("Form", TEXTO_INICIAL))
        self.lblNombre.setText(_translate("Form", "Nombre de tu comercio/emprendimiento *"))
        self.lblDireccion.setText(_translate("Form", "Dirección"))
        self.lblCuit.setText(_translate("Form", "CUIT"))
        self.lblTelefono.setText(_translate("Form", "Teléfono"))
        self.lblError.setText(_translate("Form", ""))
        self.btnGuardar.setText(_translate("Form", BUTTON_INICIAL))

    def aplicar_modo(self, edicion: bool) -> None:
        self.lblTitulo.setText(TEXTO_EDICION if edicion else TEXTO_INICIAL)
        self.btnGuardar.setText(BUTTON_EDICION if edicion else BUTTON_INICIAL)
