from PyQt6 import QtCore, QtWidgets

from ui.estilos import TAMANO_BODY, TAMANO_SMALL, fuente
from ui.widgets.boton_rodante import BotonRodante

MAXIMO_EFECTIVO = 1_000_000_000_000.0


class Ui_CierreForm(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowTitle("Caja")
        Form.setMinimumSize(720, 600)

        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(16, 14, 16, 14)
        self.verticalLayout.setSpacing(10)

        self.frmHeader = QtWidgets.QFrame(parent=Form)
        self.frmHeader.setObjectName("frmHeaderCaja")
        hlyHeader = QtWidgets.QHBoxLayout(self.frmHeader)
        hlyHeader.setContentsMargins(12, 8, 12, 8)
        hlyHeader.setSpacing(8)

        self.lblDia = QtWidgets.QLabel(parent=self.frmHeader)
        self.lblDia.setObjectName("lblDia")
        self.lblDia.setFont(fuente(TAMANO_BODY, negrita=True))
        hlyHeader.addWidget(self.lblDia)

        self.dateDia = QtWidgets.QDateEdit(parent=self.frmHeader)
        self.dateDia.setObjectName("dateDia")
        self.dateDia.setCalendarPopup(True)
        self.dateDia.setDisplayFormat("dd/MM/yyyy")
        self.dateDia.setMinimumHeight(30)
        hlyHeader.addWidget(self.dateDia)

        self.btnHoy = QtWidgets.QPushButton(parent=self.frmHeader)
        self.btnHoy.setObjectName("btnHoy")
        self.btnHoy.setMinimumHeight(30)
        hlyHeader.addWidget(self.btnHoy)

        self.btnRefrescar = QtWidgets.QPushButton(parent=self.frmHeader)
        self.btnRefrescar.setObjectName("btnRefrescar")
        self.btnRefrescar.setMinimumHeight(30)
        hlyHeader.addWidget(self.btnRefrescar)

        hlyHeader.addStretch(1)

        self.btnEstado = BotonRodante(parent=self.frmHeader, escalon=0)
        self.btnEstado.setObjectName("btnEstadoCaja")
        self.btnEstado.setCentrado(True)
        self.btnEstado.setMinimumSize(QtCore.QSize(150, 30))
        self.btnEstado.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        hlyHeader.addWidget(self.btnEstado)

        self.verticalLayout.addWidget(self.frmHeader)

        self.lblAviso = QtWidgets.QLabel(parent=Form)
        self.lblAviso.setFont(fuente(TAMANO_SMALL, negrita=True))
        self.lblAviso.setObjectName("lblAviso")
        self.lblAviso.setWordWrap(True)
        self.lblAviso.setVisible(False)
        self.verticalLayout.addWidget(self.lblAviso)

        self.frmArqueo = QtWidgets.QFrame(parent=Form)
        self.frmArqueo.setObjectName("frmArqueoCaja")
        vlyArqueo = QtWidgets.QVBoxLayout(self.frmArqueo)
        vlyArqueo.setContentsMargins(12, 8, 12, 8)
        vlyArqueo.setSpacing(6)

        self.contenedorTurnos = QtWidgets.QHBoxLayout()
        self.contenedorTurnos.setObjectName("contenedorTurnos")
        self.contenedorTurnos.setSpacing(8)
        vlyArqueo.addLayout(self.contenedorTurnos)

        self.hlyArqueoFila = QtWidgets.QHBoxLayout()
        self.hlyArqueoFila.setObjectName("hlyArqueoFila")
        self.hlyArqueoFila.setSpacing(8)
        self.hlyResumen = self.hlyArqueoFila

        self.lblEsperado = QtWidgets.QLabel(parent=self.frmArqueo)
        self.lblEsperado.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        self.lblEsperado.setObjectName("lblEsperado")
        self.lblEsperado.setWordWrap(True)
        self.hlyArqueoFila.addWidget(self.lblEsperado, 1)

        self.btnToggleMedios = QtWidgets.QPushButton(parent=self.frmArqueo)
        self.btnToggleMedios.setObjectName("btnToggleMedios")
        self.btnToggleMedios.setMinimumHeight(24)
        self.hlyArqueoFila.addWidget(self.btnToggleMedios)

        vlyArqueo.addLayout(self.hlyArqueoFila)

        self.tblMedios = QtWidgets.QFrame(parent=self.frmArqueo)
        self.tblMedios.setObjectName("tblMedios")
        self.hlyMedios = QtWidgets.QHBoxLayout(self.tblMedios)
        self.hlyMedios.setContentsMargins(0, 2, 0, 0)
        self.hlyMedios.setSpacing(8)
        vlyArqueo.addWidget(self.tblMedios)

        self.verticalLayout.addWidget(self.frmArqueo)

        self.frmDeclarado = QtWidgets.QFrame(parent=Form)
        self.frmDeclarado.setObjectName("frmDeclaradoCaja")
        vlyDeclarado = QtWidgets.QVBoxLayout(self.frmDeclarado)
        vlyDeclarado.setContentsMargins(12, 8, 12, 8)
        vlyDeclarado.setSpacing(6)

        hlyDeclaradoFila = QtWidgets.QHBoxLayout()
        hlyDeclaradoFila.setSpacing(10)

        self.lblDeclarado = QtWidgets.QLabel(parent=self.frmDeclarado)
        self.lblDeclarado.setObjectName("lblDeclarado")
        self.lblDeclarado.setFont(fuente(TAMANO_BODY, negrita=True))
        hlyDeclaradoFila.addWidget(self.lblDeclarado)

        self.spnEfectivo = QtWidgets.QDoubleSpinBox(parent=self.frmDeclarado)
        self.spnEfectivo.setObjectName("spnEfectivo")
        self.spnEfectivo.setDecimals(2)
        self.spnEfectivo.setMinimum(0.0)
        self.spnEfectivo.setMaximum(MAXIMO_EFECTIVO)
        self.spnEfectivo.setMinimumHeight(30)
        self.spnEfectivo.setMinimumWidth(150)
        hlyDeclaradoFila.addWidget(self.spnEfectivo)

        self.lblDiferencia = QtWidgets.QLabel(parent=self.frmDeclarado)
        self.lblDiferencia.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        self.lblDiferencia.setObjectName("lblDiferencia")
        self.lblDiferencia.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        hlyDeclaradoFila.addWidget(self.lblDiferencia, 1)

        vlyDeclarado.addLayout(hlyDeclaradoFila)

        self.verticalLayout.addWidget(self.frmDeclarado)

        self.hlyAcciones = QtWidgets.QHBoxLayout()
        self.hlyAcciones.setObjectName("hlyAcciones")
        self.hlyAcciones.setSpacing(10)

        font_accion = fuente(TAMANO_BODY, negrita=True)

        self.btnEgreso = QtWidgets.QPushButton(parent=Form)
        self.btnEgreso.setFont(font_accion)
        self.btnEgreso.setObjectName("btnEgresoCaja")
        self.btnEgreso.setMinimumHeight(42)
        self.hlyAcciones.addWidget(self.btnEgreso)

        self.btnIngreso = QtWidgets.QPushButton(parent=Form)
        self.btnIngreso.setFont(font_accion)
        self.btnIngreso.setObjectName("btnIngresoCaja")
        self.btnIngreso.setMinimumHeight(42)
        self.hlyAcciones.addWidget(self.btnIngreso)

        self.btnCerrarCaja = QtWidgets.QPushButton(parent=Form)
        self.btnCerrarCaja.setFont(font_accion)
        self.btnCerrarCaja.setObjectName("btnCerrarCaja")
        self.btnCerrarCaja.setMinimumHeight(42)
        self.hlyAcciones.addWidget(self.btnCerrarCaja)

        self.verticalLayout.addLayout(self.hlyAcciones)

        self.hlyPaneles = QtWidgets.QHBoxLayout()
        self.hlyPaneles.setObjectName("hlyPanelesCaja")
        self.hlyPaneles.setSpacing(10)

        self.frmMovimientos = QtWidgets.QFrame(parent=Form)
        self.frmMovimientos.setObjectName("frmMovimientosCaja")
        vlyMov = QtWidgets.QVBoxLayout(self.frmMovimientos)
        vlyMov.setContentsMargins(12, 8, 12, 8)
        vlyMov.setSpacing(6)

        hlyMovHeader = QtWidgets.QHBoxLayout()
        self.lblMovimientos = QtWidgets.QLabel(parent=self.frmMovimientos)
        self.lblMovimientos.setFont(fuente(TAMANO_BODY, negrita=True))
        self.lblMovimientos.setObjectName("lblMovimientosCaja")
        hlyMovHeader.addWidget(self.lblMovimientos)
        hlyMovHeader.addStretch(1)

        self.btnAnularMovimiento = QtWidgets.QPushButton(parent=self.frmMovimientos)
        self.btnAnularMovimiento.setObjectName("btnAnularMovimientoCierre")
        self.btnAnularMovimiento.setMinimumHeight(28)
        hlyMovHeader.addWidget(self.btnAnularMovimiento)

        vlyMov.addLayout(hlyMovHeader)

        self.scrollMovimientos = QtWidgets.QScrollArea(parent=self.frmMovimientos)
        self.scrollMovimientos.setObjectName("scrollMovimientosCaja")
        self.scrollMovimientos.setMinimumHeight(70)
        self.scrollMovimientos.setMaximumHeight(300)
        self.scrollMovimientos.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.scrollMovimientos.setWidgetResizable(True)
        self.scrollMovimientos.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollMovimientos.setStyleSheet(
            "QScrollArea#scrollMovimientosCaja { border: none; background: transparent; }"
        )

        self.contenedorMovimientos = QtWidgets.QWidget()
        self.contenedorMovimientos.setObjectName("contenedorMovimientosCaja")
        self.vlyTarjetasMovimientos = QtWidgets.QVBoxLayout(self.contenedorMovimientos)
        self.vlyTarjetasMovimientos.setContentsMargins(0, 0, 0, 0)
        self.vlyTarjetasMovimientos.setSpacing(6)
        self.scrollMovimientos.setWidget(self.contenedorMovimientos)

        vlyMov.addWidget(self.scrollMovimientos, 1)

        self.frmMovimientos.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.hlyPaneles.addWidget(self.frmMovimientos, 1)

        self.frmHistorial = QtWidgets.QFrame(parent=Form)
        self.frmHistorial.setObjectName("frmHistorialCaja")
        vlyHist = QtWidgets.QVBoxLayout(self.frmHistorial)
        vlyHist.setContentsMargins(12, 8, 12, 8)
        vlyHist.setSpacing(6)

        self.hlyHistHeader = QtWidgets.QHBoxLayout()
        self.lblHistorial = QtWidgets.QLabel(parent=self.frmHistorial)
        self.lblHistorial.setFont(fuente(TAMANO_BODY, negrita=True))
        self.lblHistorial.setObjectName("lblHistorial")
        self.hlyHistHeader.addWidget(self.lblHistorial)
        self.hlyHistHeader.addStretch(1)
        vlyHist.addLayout(self.hlyHistHeader)

        self.tblHistorial = QtWidgets.QTableWidget(0, 6, parent=self.frmHistorial)
        self.tblHistorial.setObjectName("tblHistorial")
        self.tblHistorial.setVisible(False)

        self.scrollHistorial = QtWidgets.QScrollArea(parent=self.frmHistorial)
        self.scrollHistorial.setObjectName("scrollHistorialCaja")
        self.scrollHistorial.setMinimumHeight(70)
        self.scrollHistorial.setMaximumHeight(300)
        self.scrollHistorial.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.scrollHistorial.setWidgetResizable(True)
        self.scrollHistorial.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scrollHistorial.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollHistorial.setStyleSheet(
            "QScrollArea#scrollHistorialCaja { border: none; background: transparent; } "
            "QScrollBar:vertical { width: 5px; background: transparent; border: none; margin: 0px; } "
            "QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 2px; min-height: 20px; } "
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; } "
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
        )
        self.scrollHistorial.viewport().setStyleSheet("background: transparent; border: none;")

        self.contenedorHistorial = QtWidgets.QWidget()
        self.contenedorHistorial.setObjectName("contenedorHistorialCaja")
        self.contenedorHistorial.setStyleSheet("QWidget#contenedorHistorialCaja { background: transparent; border: none; }")
        self.gridHistorial = QtWidgets.QGridLayout(self.contenedorHistorial)
        self.gridHistorial.setContentsMargins(0, 0, 0, 0)
        self.gridHistorial.setSpacing(8)
        self.scrollHistorial.setWidget(self.contenedorHistorial)

        vlyHist.addWidget(self.scrollHistorial, 1)

        self.frmHistorial.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.hlyPaneles.addWidget(self.frmHistorial, 1)

        self.verticalLayout.addLayout(self.hlyPaneles, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Caja"))
        self.lblDia.setText(_translate("Form", "Día:"))
        self.btnHoy.setText(_translate("Form", "Hoy"))
        self.btnRefrescar.setText(_translate("Form", "Recalcular"))
        self.lblAviso.setText(_translate("Form", ""))
        self.lblEsperado.setText(_translate("Form", ""))
        self.btnToggleMedios.setText(_translate("Form", "Medios de pago ▾"))
        self.lblDeclarado.setText(_translate("Form", "Efectivo contado en el cajón:"))
        self.lblDiferencia.setText(_translate("Form", ""))
        self.btnEgreso.setText(_translate("Form", "Egreso de caja"))
        self.btnIngreso.setText(_translate("Form", "Ingreso de caja"))
        self.btnCerrarCaja.setText(_translate("Form", "Cerrar caja"))
        self.lblMovimientos.setText(_translate("Form", "Movimientos del día"))
        self.btnAnularMovimiento.setText(_translate("Form", "Anular movimiento seleccionado"))
        self.lblHistorial.setText(_translate("Form", "Historial de cierres"))

        headers_h = ["Fecha", "Hora", "Ventas", "Esperado", "Diferencia", "Usuario"]
        for i, header in enumerate(headers_h):
            item = QtWidgets.QTableWidgetItem()
            item.setText(_translate("Form", header))
            self.tblHistorial.setHorizontalHeaderItem(i, item)
