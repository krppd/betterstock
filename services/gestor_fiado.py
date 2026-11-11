from __future__ import annotations

from datetime import date

from models import medio_pago
from models.cliente import Cliente
from models.movimiento_cuenta import MovimientoCuenta
from repositories.cliente_repositorio import ClienteRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from services.excepciones import ErrorValidacion


class GestorFiado:
    def __init__(self, clientes: ClienteRepositorio, cuenta: CuentaRepositorio) -> None:
        self._clientes = clientes
        self._cuenta = cuenta

    def inicializar(self) -> None:
        self._clientes.inicializar()
        self._cuenta.inicializar()

    def listar_clientes(self, solo_activos: bool = True) -> list[Cliente]:
        clientes = self._clientes.listar()
        if solo_activos:
            clientes = [c for c in clientes if c.activo]
        return sorted(clientes, key=lambda c: c.nombre.casefold())

    def buscar_cliente(self, codigo: str) -> Cliente | None:
        return self._clientes.buscar(codigo)

    def buscar_clientes(self, texto: str) -> list[Cliente]:
        baja = texto.strip().casefold()
        if not baja:
            return self.listar_clientes()
        return [
            c for c in self.listar_clientes()
            if baja in c.nombre.casefold() or baja in c.identificador
        ]

    def guardar_cliente(self, nombre: str, telefono: str = "", limite: float = 0.0,
                        activo: bool = True, codigo: str = "",
                        doc_tipo: int | None = None, doc_nro: str | None = None,
                        cond_iva: int | None = None,
                        email: str | None = None) -> Cliente:
        if self._clientes.existe_nombre(nombre, excluir=codigo):
            raise ErrorValidacion(f"Ya hay un cliente llamado '{nombre.strip()}'.")
        if codigo.strip():
            existente = self._clientes.buscar(codigo)
            if existente is None:
                raise ErrorValidacion("No se encontró el cliente indicado.")
            actualizado = Cliente(
                nombre, telefono=telefono, limite=limite, activo=activo,
                codigo=existente.codigo,
                doc_tipo=existente.doc_tipo if doc_tipo is None else doc_tipo,
                doc_nro=existente.doc_nro if doc_nro is None else doc_nro,
                cond_iva=existente.cond_iva if cond_iva is None else cond_iva,
                email=existente.email if email is None else email)
            self._clientes.actualizar(actualizado)
            return actualizado
        return self._clientes.agregar(Cliente(
            nombre, telefono=telefono, limite=limite, activo=activo,
            doc_tipo=99 if doc_tipo is None else doc_tipo,
            doc_nro="" if doc_nro is None else doc_nro,
            cond_iva=5 if cond_iva is None else cond_iva,
            email="" if email is None else email))

    def desactivar(self, codigo: str) -> None:
        cliente = self._clientes.buscar(codigo)
        if cliente is None:
            raise ErrorValidacion("No se encontró el cliente indicado.")
        try:
            inactivo = Cliente(
                cliente.nombre, telefono=cliente.telefono, limite=cliente.limite,
                activo=False, codigo=cliente.codigo)
        except ValueError as error:
            raise ErrorValidacion(str(error)) from error
        self._clientes.actualizar(inactivo)

    def saldo(self, codigo: str) -> float:
        if self._clientes.buscar(codigo) is None:
            raise ErrorValidacion("No se encontró el cliente indicado.")
        return round(sum(
            m.signo * m.importe for m in self._cuenta.por_cliente(codigo)), 2)

    def deudores(self) -> list[tuple[Cliente, float]]:
        
        raise PermissionError("Funciones de fiado avanzado requieren BetterStock Pro.")

    def total_por_cobrar(self) -> float:
        
        raise PermissionError("Funciones de fiado avanzado requieren BetterStock Pro.")

    def movimientos_de(self, codigo: str) -> list[MovimientoCuenta]:
        return self._cuenta.por_cliente(codigo)

    def pagos_del_dia(self, dia: date) -> list[MovimientoCuenta]:
        return [
            m for m in self._cuenta.movimientos_del_dia(dia)
            if m.tipo == MovimientoCuenta.TIPO_PAGO
        ]

    def validar_cargo(self, codigo: str, importe: float) -> float:
        cliente = self._clientes.buscar(codigo)
        if cliente is None:
            raise ErrorValidacion("No se encontró el cliente indicado.")
        if not cliente.activo:
            raise ErrorValidacion(f"El cliente '{cliente.nombre}' está dado de baja.")
        if importe <= 0:
            raise ErrorValidacion("El importe del fiado debe ser mayor a cero.")
        nuevo_saldo = round(self.saldo(cliente.identificador) + importe, 2)
        if cliente.limite > 0 and nuevo_saldo > cliente.limite:
            raise ErrorValidacion(
                f"Supera el límite de {cliente.nombre}: "
                f"debe {self.saldo(cliente.identificador):.2f} "
                f"con tope {cliente.limite:.2f}.")
        return nuevo_saldo

    def registrar_cargo(self, codigo: str, importe: float, fecha: date,
                        detalle: str = "", usuario: str = "") -> MovimientoCuenta:
        self.validar_cargo(codigo, importe)
        cliente = self._clientes.buscar(codigo)
        assert cliente is not None
        return self._cuenta.agregar(MovimientoCuenta(
            fecha, cliente.identificador, MovimientoCuenta.TIPO_CARGO,
            importe, detalle=detalle, usuario=usuario))

    def registrar_pago(self, codigo: str, importe: float, fecha: date, medio: str,
                       usuario: str = "", detalle: str = "") -> MovimientoCuenta:
        cliente = self._clientes.buscar(codigo)
        if cliente is None:
            raise ErrorValidacion("No se encontró el cliente indicado.")
        if importe <= 0:
            raise ErrorValidacion("El pago debe ser mayor a cero.")
        deuda = self.saldo(cliente.identificador)
        if round(importe, 2) > deuda:
            raise ErrorValidacion(
                f"El pago supera la deuda de {cliente.nombre}: debe {deuda:.2f}.")
        if medio_pago.nombre_de(medio) == medio_pago.MEDIO_DESCONOCIDO:
            raise ErrorValidacion("El medio con que paga no es válido.")
        return self._cuenta.agregar(MovimientoCuenta(
            fecha, cliente.identificador, MovimientoCuenta.TIPO_PAGO,
            importe, detalle=detalle, medio=medio, usuario=usuario))

    def reversar_cargo(self, codigo: str, importe: float, fecha: date,
                       detalle: str = "", usuario: str = "") -> MovimientoCuenta:
        cliente = self._clientes.buscar(codigo)
        if cliente is None:
            raise ErrorValidacion("No se encontró el cliente indicado.")
        if importe <= 0:
            raise ErrorValidacion("El importe a reversar debe ser mayor a cero.")
        return self._cuenta.agregar(MovimientoCuenta(
            fecha, cliente.identificador, MovimientoCuenta.TIPO_PAGO,
            importe, detalle=detalle, usuario=usuario))

