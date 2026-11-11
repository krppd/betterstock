from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "windows:fontengine=gdi")

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QDialog

from config import DATA_DIR, RECURSOS_DIR
from repositories.caja_movimiento_repositorio import CajaMovimientoRepositorio
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.cierre_repositorio import CierreRepositorio
from repositories.cliente_repositorio import ClienteRepositorio
from repositories.codigo_repositorio import CodigoRepositorio
from repositories.comercio_repositorio import ComercioRepositorio
from repositories.cuenta_repositorio import CuentaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.turno_repositorio import TurnoRepositorio
from repositories.usuario_repositorio import UsuarioRepositorio
from repositories.venta_repositorio import VentaRepositorio
from services.autenticacion import Autenticacion
from services.caja import ServicioCaja
from services.cierre_caja import ServicioCierre
from services.estadisticas_ventas import EstadisticasVentas
from services.turnos import ServicioTurnos
from services.gestor_anulaciones import GestorAnulaciones, registrar_servicio
from services.gestor_comercio import GestorComercio
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from services.preferencias import escala_modo_tactil
from ui.estilos import ESCALA_NORMAL, aplicar_color_fluent, aplicar_tema
from ui.scroll_suave import instalar_scroll_suave
from views.ventana_configuracion import VentanaConfiguracion
from views.ventana_login import VentanaLogin
from views.ventana_primer_usuario import VentanaPrimerUsuario
from views.ventana_principal import VentanaPrincipal


class Aplicacion:

    def __init__(self, argumentos: list[str], carpeta_datos: Path = DATA_DIR) -> None:
        self._qt = QApplication(argumentos)
        self._qt.setWindowIcon(QIcon(str(RECURSOS_DIR / "logo_u.png")))
        aplicar_color_fluent(self._qt)
        aplicar_tema(self._qt, ESCALA_NORMAL)
        instalar_scroll_suave(self._qt)
        self._gestor_stock = GestorStock(
            ProductoRepositorio(carpeta_datos / "betterstock.db"),
            MovimientoRepositorio(carpeta_datos / "betterstock.db"),
            CategoriaRepositorio(carpeta_datos / "betterstock.db"),
        )
        self._autenticacion = Autenticacion(UsuarioRepositorio(carpeta_datos / "betterstock.db"))
        self._gestor_comercio = GestorComercio(ComercioRepositorio(carpeta_datos / "betterstock.db"))
        self._estadisticas = EstadisticasVentas(VentaRepositorio(carpeta_datos / "betterstock.db"))
        self._fiado = GestorFiado(
            ClienteRepositorio(carpeta_datos / "betterstock.db"),
            CuentaRepositorio(carpeta_datos / "betterstock.db"))
        self._cierre = ServicioCierre(
            self._estadisticas, CierreRepositorio(carpeta_datos / "betterstock.db"),
            self._fiado)
        self._turnos = ServicioTurnos(
            TurnoRepositorio(carpeta_datos / "betterstock.db"),
            VentaRepositorio(carpeta_datos / "betterstock.db"),
            CuentaRepositorio(carpeta_datos / "betterstock.db"))
        self._caja_repo = CajaMovimientoRepositorio(carpeta_datos / "betterstock.db")
        self._caja = ServicioCaja(
            self._caja_repo,
            cierres=self._cierre,
            turnos=self._turnos,
            codigos=CodigoRepositorio(carpeta_datos / "betterstock.db"),
        )
        self._cierre.caja = self._caja
        self._turnos.caja = self._caja
        self._gestor_ventas = GestorVentas(
            self._gestor_stock, self._estadisticas, self._fiado, self._cierre)
        self._anulaciones = GestorAnulaciones(
            self._gestor_ventas, CodigoRepositorio(carpeta_datos / "betterstock.db"))
        self._ventana_principal: VentanaPrincipal | None = None
        self._carpeta_datos = carpeta_datos

        self._gestor_stock.inicializar()
        self._autenticacion.inicializar(sembrar_iniciales=False)
        self._gestor_comercio.inicializar()
        self._estadisticas.inicializar()
        self._fiado.inicializar()
        self._cierre.inicializar()
        self._turnos.inicializar()
        self._caja.inicializar()
        self._anulaciones.inicializar()
        registrar_servicio(self._anulaciones)

    def _configurar_comercio(self) -> bool:
        if not self._gestor_comercio.necesita_configuracion():
            return True
        configuracion = VentanaConfiguracion(self._gestor_comercio)
        return configuracion.exec() == QDialog.DialogCode.Accepted

    def ejecutar(self) -> int:
        if not self._configurar_comercio():
            return 0

        sesion = self._iniciar_sesion()
        if sesion is None:
            return 0
        self._abrir_principal(*sesion)
        return self._qt.exec()

    def _iniciar_sesion(self) -> tuple[str, str] | None:
        aplicar_tema(self._qt, ESCALA_NORMAL)
        sesion = self._primer_usuario()
        if sesion is None:
            login = VentanaLogin(self._autenticacion)
            if login.exec() != QDialog.DialogCode.Accepted:
                return None
            usuario = self._autenticacion.usuario_actual
            if usuario is None:
                return "", ""
            sesion = (usuario.nombre, usuario.permiso)
        aplicar_tema(self._qt, escala_modo_tactil())
        return sesion

    def _primer_usuario(self) -> tuple[str, str] | None:
        if self._autenticacion.hay_usuarios():
            return None
        primer = VentanaPrimerUsuario(self._autenticacion)
        if primer.exec() != QDialog.DialogCode.Accepted:
            return None
        usuario = self._autenticacion.usuario_actual
        return (usuario.nombre, usuario.permiso) if usuario is not None else None

    def _abrir_principal(self, usuario: str, permiso: str = "") -> None:
        self._ventana_principal = VentanaPrincipal(
            self._gestor_stock, self._gestor_comercio, self._estadisticas,
            self._cierre, usuario, self._fiado,
            gestor_ventas=self._gestor_ventas, anulaciones=self._anulaciones,
            permiso=permiso, autenticacion=self._autenticacion,
            turnos=self._turnos, caja=self._caja)
        self._ventana_principal.sesion_cerrada.connect(self._cerrar_sesion)
        from PyQt6.QtCore import QTimer
        if escala_modo_tactil() > ESCALA_NORMAL:
            self._ventana_principal.showMaximized()
        else:
            self._ventana_principal.show()

    def _cerrar_sesion(self) -> None:
        ventana = self._ventana_principal
        self._ventana_principal = None
        if ventana is not None:
            ventana.hide()
        self._autenticacion.cerrar_sesion()
        sesion = self._iniciar_sesion()
        if ventana is not None:
            ventana.permitir_cierre()
            ventana.close()
            ventana.deleteLater()
        if sesion is None:
            self._qt.quit()
            return
        self._abrir_principal(*sesion)


if __name__ == "__main__":
    sys.exit(Aplicacion(sys.argv).ejecutar())
