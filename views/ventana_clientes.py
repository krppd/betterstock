from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QWidget

from models import medio_pago
from services.gestor_fiado import GestorFiado
from ui.manual.clientes_ui import Ui_ClientesForm
from utils.formato import formatear_dinero
from views.dialogo_pago import DialogoPago
from views.formulario_cliente import FormularioCliente
from views.ventana_base import VentanaBase


class VentanaClientes(QWidget, VentanaBase):
    def __init__(self, fiado: GestorFiado, usuario_actual: str = "") -> None:
        super().__init__()
        self._fiado = fiado
        self._usuario_actual = usuario_actual
        self._codigos: list[str] = []
        self.ui = Ui_ClientesForm()
        self.ui.setupUi(self)
        self.estirar_columnas(self.ui.tblClientes)
        self.estirar_columnas(self.ui.tblCuenta)
        self.setMinimumSize(640, 480)
        self.ui.txtBuscar.textChanged.connect(self.cargar)
        self.ui.btnNuevo.clicked.connect(self.nuevo_cliente)
        self.ui.btnEditar.clicked.connect(self.editar_cliente)
        self.ui.btnPago.clicked.connect(self.registrar_pago)
        self.ui.tblClientes.itemSelectionChanged.connect(self._cuenta_del_seleccionado)
        self.cargar()

    def al_mostrar(self) -> None:
        self.cargar()

    def cargar(self) -> None:
        clientes = self._fiado.buscar_clientes(self.ui.txtBuscar.text())
        self._codigos = [c.identificador for c in clientes]
        filas = []
        colores = []
        for cliente in clientes:
            deuda = self._fiado.saldo(cliente.identificador)
            tope = formatear_dinero(cliente.limite) if cliente.limite > 0 else "sin tope"
            filas.append([
                cliente.identificador, cliente.nombre, cliente.telefono,
                formatear_dinero(deuda), tope])
            if not cliente.activo:
                colores.append("gray")
            elif cliente.limite > 0 and deuda >= cliente.limite:
                colores.append("red")
            else:
                colores.append(None)
        self.llenar_tabla(self.ui.tblClientes, filas, colores)
        self.ui.lblDeudaTotal.mostrar("Por cobrar: disponible en BetterStock Pro")
        self.ui.lblDeudaTotal.setToolTip(
            "El total consolidado por cobrar está disponible en BetterStock Pro.")
        self._cuenta_del_seleccionado()

    def _codigo_seleccionado(self, mensaje: str) -> str | None:
        seleccion = self.ui.tblClientes.selectedItems()
        if not seleccion:
            self.mostrar_advertencia("Clientes", mensaje)
            return None
        fila = seleccion[0].row()
        if fila < 0 or fila >= len(self._codigos):
            return None
        return self._codigos[fila]

    def _cuenta_del_seleccionado(self) -> None:
        seleccion = self.ui.tblClientes.selectedItems()
        if not seleccion or seleccion[0].row() >= len(self._codigos):
            self.ui.lblCuenta.setText("Cuenta")
            self.llenar_tabla(self.ui.tblCuenta, [])
            return
        codigo = self._codigos[seleccion[0].row()]
        cliente = self._fiado.buscar_cliente(codigo)
        nombre = cliente.nombre if cliente is not None else codigo
        self.ui.lblCuenta.setText(f"Cuenta de {nombre}")
        filas = [
            [m.fecha_texto, m.tipo, formatear_dinero(m.importe),
             medio_pago.nombre_de(m.medio) if m.medio else "—",
             m.detalle, m.usuario]
            for m in reversed(self._fiado.movimientos_de(codigo))
        ]
        self.llenar_tabla(self.ui.tblCuenta, filas)

    def nuevo_cliente(self) -> None:
        if FormularioCliente(self._fiado, parent=self).exec() == QDialog.DialogCode.Accepted:
            self.cargar()

    def editar_cliente(self) -> None:
        codigo = self._codigo_seleccionado("Elegí un cliente para editar.")
        if codigo is None:
            return
        cliente = self._fiado.buscar_cliente(codigo)
        if cliente is None:
            return
        if FormularioCliente(self._fiado, cliente, parent=self).exec() == QDialog.DialogCode.Accepted:
            self.cargar()

    def registrar_pago(self) -> None:
        codigo = self._codigo_seleccionado("Elegí un cliente para registrarle el pago.")
        if codigo is None:
            return
        if self._fiado.saldo(codigo) <= 0:
            self.mostrar_advertencia("Pago", "Ese cliente no tiene deuda.")
            return
        if DialogoPago(self._fiado, codigo, self._usuario_actual, parent=self).exec() == QDialog.DialogCode.Accepted:
            self.cargar()

