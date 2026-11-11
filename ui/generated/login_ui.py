from PyQt6 import QtCore, QtWidgets
from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    PasswordLineEdit,
    PixmapLabel,
    PrimaryPushButton,
)
import Recursos.Recursos_rc


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 440)
        self.layoutWidget = QtWidgets.QWidget(parent=Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(26, 20, 361, 391))
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout.setContentsMargins(6, 6, 20, 20)
        self.gridLayout.setObjectName("gridLayout")
        self.lblLogo = PixmapLabel(parent=self.layoutWidget)
        self.lblLogo.setMinimumSize(QtCore.QSize(300, 150))
        self.lblLogo.setObjectName("lblLogo")
        self.gridLayout.addWidget(self.lblLogo, 0, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_3 = BodyLabel("Usuario", self.layoutWidget)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.txtUsuario = LineEdit(parent=self.layoutWidget)
        self.txtUsuario.setObjectName("txtUsuario")
        self.txtUsuario.setPlaceholderText("Nombre de usuario")
        self.gridLayout.addWidget(self.txtUsuario, 2, 0, 1, 1)
        self.label_2 = BodyLabel("Contraseña", self.layoutWidget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.txtPassword = PasswordLineEdit(parent=self.layoutWidget)
        self.txtPassword.setObjectName("txtPassword")
        self.txtPassword.setPlaceholderText("Tu contraseña")
        self.gridLayout.addWidget(self.txtPassword, 4, 0, 1, 1)
        self.lblError = BodyLabel("", self.layoutWidget)
        self.lblError.setObjectName("lblError")
        self.lblError.setWordWrap(True)
        self.gridLayout.addWidget(self.lblError, 5, 0, 1, 1)
        self.btnIngresar = PrimaryPushButton("Ingresar", self.layoutWidget)
        self.btnIngresar.setObjectName("btnIngresar")
        self.gridLayout.addWidget(self.btnIngresar, 6, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Iniciar Sesión"))
        self.btnIngresar.setText(_translate("Dialog", "Ingresar"))
        self.label_2.setText(_translate("Dialog", "Contraseña"))
        self.label_3.setText(_translate("Dialog", "Usuario"))

# --- INICIO CODIGO MANUAL ---
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec())
# --- FIN CODIGO MANUAL ---
