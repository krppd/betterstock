from __future__ import annotations

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from models.usuario import Usuario
from services.caja import ServicioCaja
from services.turnos import ErrorTurno, ServicioTurnos
from ui.estilos import GRIS_TEXTO, TAMANO_SMALL, fuente
from utils.formato import diferencia as diferencia_montos
from utils.formato import formatear_dinero
from views.dialogo_turno import DialogoAbrirTurno, DialogoCerrarTurno
from views.ventana_base import VentanaBase


class SeccionTurnos(QGroupBox, VentanaBase):
    def __init__(self, servicio: ServicioTurnos, usuario: str, permiso: str,
                 parent: QWidget | None = None,
                 caja: ServicioCaja | None = None) -> None:
        super().__init__("", parent)
        self._servicio = servicio
        self._caja = caja if caja is not None else getattr(servicio, "caja", None)
        self._usuario = usuario
        self._permiso = permiso
        self._admin = Usuario.es_admin(permiso)
        self.setObjectName("grpTurnos")
        self.setStyleSheet("QGroupBox#grpTurnos { border: none; margin: 0; padding: 0; background: transparent; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        fila_superior = QHBoxLayout()
        fila_superior.setContentsMargins(0, 0, 0, 0)
        fila_superior.setSpacing(8)

        self.lblEstado = QLabel("", self)
        self.lblEstado.setWordWrap(True)
        self.lblEstado.setFont(fuente(TAMANO_SMALL))
        fila_superior.addWidget(self.lblEstado, 1)

        self.btnAbrir = QPushButton("Abrir turno", self)
        self.btnAbrir.setObjectName("btnAbrirTurno")
        self.btnAbrir.setMinimumHeight(28)
        self.btnAbrir.clicked.connect(self.abrir)
        fila_superior.addWidget(self.btnAbrir)

        self.btnCerrar = QPushButton("Cerrar turno", self)
        self.btnCerrar.setObjectName("btnCerrarTurno")
        self.btnCerrar.setMinimumHeight(28)
        self.btnCerrar.clicked.connect(self.cerrar)
        fila_superior.addWidget(self.btnCerrar)

        layout.addLayout(fila_superior)

        self.tabla = QTableWidget(0, 7, self)
        self.tabla.setObjectName("tblTurnos")
        self.tabla.setHorizontalHeaderLabels([
            "Turno", "Apertura", "Cierre", "Fondo", "Esperado",
            "Declarado", "Diferencia",
        ])
        self.tabla.setVisible(False)

        self.actualizar()

    @property
    def caja(self) -> ServicioCaja | None:
        return self._caja

    @caja.setter
    def caja(self, valor: ServicioCaja | None) -> None:
        self._caja = valor

    def actualizar(self, dia_cerrado: bool = False) -> None:
        if self._caja is None:
            self._caja = getattr(self._servicio, "caja", None)
        turno = self._servicio.abierto()
        if dia_cerrado:
            self.lblEstado.setText("Día cerrado: operaciones de turno deshabilitadas.")
            self.lblEstado.setStyleSheet(f"color: {GRIS_TEXTO};")
            self.btnAbrir.setEnabled(False)
            self.btnCerrar.setEnabled(False)
            self.btnCerrar.setToolTip("")
        elif turno is None:
            self.lblEstado.setText(
                "Sin turno abierto. Abrí un turno para rendir el efectivo al terminar.")
            self.lblEstado.setStyleSheet(f"color: {GRIS_TEXTO};")
            self.btnAbrir.setEnabled(True)
            self.btnCerrar.setEnabled(False)
            self.btnCerrar.setToolTip("")
        else:
            arqueo = self._servicio.arqueo(turno)
            self.lblEstado.setText(
                f"Turno #{turno.id_turno} Abierto · Fondo {formatear_dinero(turno.fondo_inicial)} · "
                f"Esperado {formatear_dinero(arqueo.efectivo_esperado)}"
            )
            self.lblEstado.setStyleSheet("")
            self.btnAbrir.setEnabled(False)
            puede_cerrar = self._puede_cerrar(turno)
            self.btnCerrar.setEnabled(puede_cerrar)
            self.btnCerrar.setToolTip(
                "" if puede_cerrar
                else "Solo quien abrió el turno o un administrador puede cerrarlo.")

        self._cargar_historial()

    def _puede_cerrar(self, turno) -> bool:
        return (self._admin or not turno.usuario_apertura
                or turno.usuario_apertura.casefold() == self._usuario.casefold())

    def _cargar_historial(self) -> None:
        filas: list[list[str]] = []
        abierto = self._servicio.abierto()
        arqueo_abierto = (self._servicio.arqueo(abierto)
                          if abierto is not None else None)
        for turno in self._servicio.historial():
            cierre = (f"{turno.cierre_texto} · {turno.usuario_cierre}"
                      if turno.cerrado else "Abierto")
            if turno.abierto and arqueo_abierto is not None:
                esperado = formatear_dinero(arqueo_abierto.efectivo_esperado)
                declarado = "—"
                diferencia = "—"
            else:
                esperado = formatear_dinero(turno.efectivo_esperado)
                declarado = formatear_dinero(turno.declarado)
                diferencia = formatear_dinero(turno.diferencia)
            filas.append([
                f"#{turno.id_turno}",
                f"{turno.apertura_texto} · {turno.usuario_apertura}",
                cierre,
                formatear_dinero(turno.fondo_inicial),
                esperado,
                declarado,
                diferencia,
            ])
        self.llenar_tabla(self.tabla, filas)

    def abrir(self) -> None:
        dialogo = DialogoAbrirTurno(self._servicio.sugerir_fondo(), self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        fondo, notas = dialogo.datos
        try:
            self._servicio.abrir(fondo, self._usuario, notas)
        except ErrorTurno as error:
            self.mostrar_advertencia("Turno de caja", str(error))
            self.actualizar()
            return
        self.actualizar()
        padre = self.parent()
        if padre is not None and hasattr(padre, "recalcular"):
            padre.recalcular()

    def cerrar(self) -> None:
        turno = self._servicio.abierto()
        if turno is None:
            self.mostrar_advertencia(
                "Turno de caja", "No hay un turno abierto para cerrar.")
            self.actualizar()
            return
        if not self._puede_cerrar(turno):
            self.mostrar_advertencia(
                "Turno de caja",
                "Solo quien abrió el turno o un administrador puede cerrarlo.")
            return
        try:
            arqueo = self._servicio.arqueo(turno)
        except ErrorTurno as error:
            self.mostrar_advertencia("Turno de caja", str(error))
            return
        dialogo = DialogoCerrarTurno(
            arqueo.efectivo_esperado, turno.fondo_inicial,
            arqueo.efectivo_ventas, self,
            egresos=arqueo.egresos, ingresos=arqueo.ingresos,
            cobros_fiado=arqueo.cobros_fiado,
            devoluciones_total=arqueo.devoluciones_total)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        declarado, notas = dialogo.datos
        diferencia = float(diferencia_montos(
            declarado, arqueo.efectivo_esperado))
        if abs(diferencia) >= 0.01 and not self.confirmar(
                "Cerrar con diferencia",
                f"Esperado: {formatear_dinero(arqueo.efectivo_esperado)}\n"
                f"Declarado: {formatear_dinero(declarado)}\n"
                f"Diferencia: {formatear_dinero(diferencia)}\n\n"
                "¿Cerrar el turno igual?"):
            return
        try:
            self._servicio.cerrar(
                declarado, self._usuario, self._permiso, notas)
        except ErrorTurno as error:
            self.mostrar_advertencia("Turno de caja", str(error))
            self.actualizar()
            return
        self.actualizar()
        padre = self.parent()
        if padre is not None and hasattr(padre, "recalcular"):
            padre.recalcular()
