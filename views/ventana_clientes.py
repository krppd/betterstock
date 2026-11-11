from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    CardWidget,
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    StrongBodyLabel,
    SubtitleLabel,
    TableWidget,
    qconfig,
)

from models import medio_pago
from services.gestor_fiado import GestorFiado
from ui.fluent import color
from utils.formato import formatear_dinero
from views.dialogo_pago import DialogoPago
from views.formulario_cliente import FormularioCliente
from views.ventana_base import VentanaBase


class _EtiquetaDeuda(StrongBodyLabel):
    """Etiqueta Fluent que conserva la API ``mostrar`` usada por la vista."""

    def mostrar(self, texto: str, direccion: str | None = None) -> None:
        self.setText(texto)


class _UiClientes:
    """Namespace con los widgets Fluent de la vista (``self.ui.*``)."""


class VentanaClientes(QWidget, VentanaBase):
    """Cuentas de clientes: saldos, movimientos y pagos."""

    def __init__(self, fiado: GestorFiado, usuario_actual: str = "") -> None:
        super().__init__()
        self._fiado = fiado
        self._usuario_actual = usuario_actual
        self._codigos: list[str] = []
        self._clientes_cache: list = []
        self.ui = _UiClientes()
        self._iniciar_interfaz()
        self.ui.txtBuscar.textChanged.connect(lambda _texto: self.cargar())
        self.ui.btnNuevo.clicked.connect(self.nuevo_cliente)
        self.ui.btnEditar.clicked.connect(self.editar_cliente)
        self.ui.btnPago.clicked.connect(self.registrar_pago)
        self.ui.tblClientes.itemSelectionChanged.connect(self._cuenta_del_seleccionado)
        self.cargar()
        if hasattr(qconfig, "themeChanged"):
            qconfig.themeChanged.connect(self._repintar_colores)

    def _iniciar_interfaz(self) -> None:
        self.setWindowTitle("Cuentas de clientes")
        self.setMinimumSize(640, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)

        barra = QHBoxLayout()
        barra.setSpacing(8)
        self.ui.txtBuscar = SearchLineEdit(self)
        self.ui.txtBuscar.setObjectName("txtBuscar")
        self.ui.txtBuscar.setPlaceholderText("Nombre o código...")
        self.ui.txtBuscar.setClearButtonEnabled(True)
        self.ui.txtBuscar.setMinimumWidth(220)
        self.ui.lblDeudaTotal = _EtiquetaDeuda(self)
        self.ui.lblDeudaTotal.setObjectName("lblDeudaTotal")
        barra.addWidget(self.ui.txtBuscar, 1)
        barra.addWidget(self.ui.lblDeudaTotal)
        layout.addLayout(barra)

        tarjeta = CardWidget(self)
        lay_tarjeta = QVBoxLayout(tarjeta)
        lay_tarjeta.setContentsMargins(16, 12, 16, 12)
        lay_tarjeta.setSpacing(8)

        self.ui.tblClientes = TableWidget(tarjeta)
        self.ui.tblClientes.setObjectName("tblClientes")
        self.ui.tblClientes.setColumnCount(5)
        self.ui.tblClientes.setHorizontalHeaderLabels(
            ["Código", "Nombre", "Teléfono", "Debe", "Tope"])
        self.ui.tblClientes.setBorderVisible(True)
        self.ui.tblClientes.setBorderRadius(8)
        lay_tarjeta.addWidget(self.ui.tblClientes, 1)

        self.ui.btnNuevo = PushButton(FIF.ADD, "Nuevo cliente", tarjeta)
        self.ui.btnNuevo.setObjectName("btnNuevo")
        self.ui.btnEditar = PushButton(FIF.EDIT, "Editar", tarjeta)
        self.ui.btnEditar.setObjectName("btnEditar")
        self.ui.btnPago = PrimaryPushButton(
            FIF.ACCEPT_MEDIUM, "Registrar pago", tarjeta)
        self.ui.btnPago.setObjectName("btnPago")

        botones = QHBoxLayout()
        botones.setSpacing(8)
        for boton in (
            self.ui.btnNuevo,
            self.ui.btnEditar,
            self.ui.btnPago,
        ):
            botones.addWidget(boton)
        botones.addStretch(1)
        lay_tarjeta.addLayout(botones)
        layout.addWidget(tarjeta, 3)

        tarjeta_cuenta = CardWidget(self)
        lay_cuenta = QVBoxLayout(tarjeta_cuenta)
        lay_cuenta.setContentsMargins(16, 12, 16, 12)
        lay_cuenta.setSpacing(8)

        self.ui.lblCuenta = SubtitleLabel("Cuenta", tarjeta_cuenta)
        self.ui.lblCuenta.setObjectName("lblCuenta")
        lay_cuenta.addWidget(self.ui.lblCuenta)

        self.ui.tblCuenta = TableWidget(tarjeta_cuenta)
        self.ui.tblCuenta.setObjectName("tblCuenta")
        self.ui.tblCuenta.setColumnCount(6)
        self.ui.tblCuenta.setHorizontalHeaderLabels(
            ["Fecha", "Tipo", "Importe", "Pagó con", "Detalle", "Usuario"])
        self.ui.tblCuenta.setBorderVisible(True)
        self.ui.tblCuenta.setBorderRadius(8)
        lay_cuenta.addWidget(self.ui.tblCuenta, 2)
        layout.addWidget(tarjeta_cuenta, 2)

        self.estirar_columnas(self.ui.tblClientes)
        self.estirar_columnas(self.ui.tblCuenta)

    def al_mostrar(self) -> None:
        self.cargar()

    def _repintar_colores(self) -> None:
        """Repinta la tabla con los colores del tema, sin volver a consultar la base."""
        colores = []
        for cliente in self._clientes_cache:
            if not cliente.activo:
                colores.append(color("gris_medio"))
            elif cliente.limite > 0 and self._fiado.saldo(cliente.identificador) >= cliente.limite:
                colores.append(color("error"))
            else:
                colores.append(None)
        filas = [
            [self.ui.tblClientes.item(fila, columna).text() if self.ui.tblClientes.item(fila, columna) is not None else ""
             for columna in range(self.ui.tblClientes.columnCount())]
            for fila in range(self.ui.tblClientes.rowCount())
        ]
        self.llenar_tabla(self.ui.tblClientes, filas, colores)

    def cargar(self) -> None:
        clientes = self._fiado.buscar_clientes(self.ui.txtBuscar.text())
        self._clientes_cache = clientes
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
                colores.append(color("gris_medio"))
            elif cliente.limite > 0 and deuda >= cliente.limite:
                colores.append(color("error"))
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
