

from PyQt6 import QtCore, QtGui, QtWidgets
import Recursos.Recursos_rc
from ui.widgets.boton_rodante import BotonRodante


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
        self.lblLogo = QtWidgets.QLabel(parent=self.layoutWidget)
        self.lblLogo.setMinimumSize(QtCore.QSize(300, 150))
        self.lblLogo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblLogo.setObjectName("lblLogo")
        self.gridLayout.addWidget(self.lblLogo, 0, 0, 1, 1)
        self.txtUsuario = QtWidgets.QLineEdit(parent=self.layoutWidget)
        self.txtUsuario.setObjectName("txtUsuario")
        self.gridLayout.addWidget(self.txtUsuario, 2, 0, 1, 1)
        self.btnIngresar = BotonRodante(parent=self.layoutWidget)
        self.btnIngresar.setObjectName("btnIngresar")
        self.gridLayout.addWidget(self.btnIngresar, 6, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.txtPassword = QtWidgets.QLineEdit(parent=self.layoutWidget)
        self.txtPassword.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.txtPassword.setObjectName("txtPassword")
        self.gridLayout.addWidget(self.txtPassword, 4, 0, 1, 1)
        self.lblError = QtWidgets.QLabel(parent=self.layoutWidget)
        self.lblError.setText("")
        self.lblError.setObjectName("lblError")
        self.gridLayout.addWidget(self.lblError, 5, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Iniciar Sesión"))
        self.btnIngresar.setText(_translate("Dialog", "Ingresar"))
        self.label_2.setText(_translate("Dialog", "Contraseña"))
        self.label_3.setText(_translate("Dialog", "<html><head/><body><p><span style=\" font-size:13pt;\">Usuario</span></p></body></html>"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec())
