from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    DoubleSpinBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    qconfig,
)

from ui.fluent import CLARO, OSCURO, color
from utils.formato import diferencia as diferencia_montos
from utils.formato import formatear_dinero
from views.ventana_base import VentanaBase

IMPORTE_MAXIMO = 99_999_999.99


def _tinta(nombre: str) -> tuple[QColor, QColor]:
    """Devuelve el par (claro, oscuro) de un token Fluent para labels adaptativos."""
    return QColor(CLARO[nombre]), QColor(OSCURO[nombre])


class _FondoDeTema:
    """Mixin: el fondo del diálogo sigue al tema activo.

    Los labels Fluent usan texto claro en modo oscuro, así que el fondo del
    diálogo tiene que acompañarlo para que el texto se lea.
    """

    def _aplicar_tema(self) -> None:
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}")


class DialogoAbrirTurno(_FondoDeTema, QDialog, VentanaBase):
    """Alta de un turno de caja con el fondo inicial y notas opcionales."""

    def __init__(self, fondo_sugerido: float = 0.0,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._datos: tuple[float, str] = (0.0, "")
        self.setWindowTitle("Abrir caja")
        self.setObjectName("dlgAbrirTurno")
        self._aplicar_tema()
        qconfig.themeChanged.connect(self._aplicar_tema)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addLayout(self._armar_formulario(fondo_sugerido))
        layout.addStretch(1)
        layout.addLayout(self._armar_botones())
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def _armar_formulario(self, fondo_sugerido: float) -> QFormLayout:
        formulario = QFormLayout()
        formulario.setSpacing(10)
        self.spnFondo = DoubleSpinBox(self)
        self.spnFondo.setDecimals(2)
        self.spnFondo.setMinimum(0.0)
        self.spnFondo.setMaximum(IMPORTE_MAXIMO)
        self.spnFondo.setPrefix("$ ")
        self.spnFondo.setValue(max(fondo_sugerido, 0.0))
        formulario.addRow(BodyLabel("Fondo inicial:", self), self.spnFondo)

        self.txtNotas = LineEdit(self)
        self.txtNotas.setPlaceholderText("Opcional")
        formulario.addRow(BodyLabel("Notas:", self), self.txtNotas)
        return formulario

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnAbrir = PrimaryPushButton("Abrir caja", self)
        self.btnCancelar.setAutoDefault(False)
        self.btnAbrir.setDefault(True)
        botones.addWidget(self.btnCancelar)
        botones.addStretch(1)
        botones.addWidget(self.btnAbrir)
        self.btnCancelar.clicked.connect(self.reject)
        self.btnAbrir.clicked.connect(self.guardar)
        return botones

    @property
    def datos(self) -> tuple[float, str]:
        return self._datos

    def guardar(self) -> None:
        self._datos = (self.spnFondo.value(), self.txtNotas.text().strip())
        self.accept()


class DialogoCerrarTurno(_FondoDeTema, QDialog, VentanaBase):
    """Cierre de un turno de caja, con el resumen del efectivo esperado."""

    def __init__(self, efectivo_esperado: float, fondo_inicial: float,
                 efectivo_ventas: float, parent: QWidget | None = None,
                 egresos: float = 0.0, ingresos: float = 0.0,
                 cobros_fiado: float = 0.0,
                 devoluciones_total: float = 0.0) -> None:
        super().__init__(parent)
        self._efectivo_esperado = efectivo_esperado
        self._datos: tuple[float, str] = (0.0, "")
        self.setWindowTitle("Cerrar turno")
        self.setObjectName("dlgCerrarTurno")
        self._aplicar_tema()
        qconfig.themeChanged.connect(self._aplicar_tema)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(self._armar_resumen(
            fondo_inicial, efectivo_ventas, egresos, ingresos, cobros_fiado,
            devoluciones_total))
        layout.addLayout(self._armar_formulario())
        self.lblDiferencia = BodyLabel("", self)
        self.lblDiferencia.setWordWrap(True)
        layout.addWidget(self.lblDiferencia)
        layout.addStretch(1)
        layout.addLayout(self._armar_botones())
        self.spnDeclarado.valueChanged.connect(self.actualizar_diferencia)
        self.actualizar_diferencia()

    def _armar_resumen(self, fondo_inicial: float,
                       efectivo_ventas: float, egresos: float = 0.0,
                       ingresos: float = 0.0, cobros_fiado: float = 0.0,
                       devoluciones_total: float = 0.0) -> BodyLabel:
        lineas = [f"Fondo inicial: {formatear_dinero(fondo_inicial)}"]
        if egresos > 0 or ingresos > 0 or cobros_fiado > 0 or devoluciones_total > 0:
            if efectivo_ventas > 0:
                lineas.append(f"Ventas en efectivo: {formatear_dinero(efectivo_ventas)}")
            if cobros_fiado > 0:
                lineas.append(f"Cobros fiado: {formatear_dinero(cobros_fiado)}")
            if devoluciones_total > 0:
                lineas.append(f"Devoluciones del día: {formatear_dinero(devoluciones_total)}")
            if egresos > 0:
                lineas.append(f"Egresos de caja: -{formatear_dinero(egresos)}")
            if ingresos > 0:
                lineas.append(f"Ingresos de caja: +{formatear_dinero(ingresos)}")
        else:
            lineas.append(f"Ventas y cobros en efectivo: {formatear_dinero(efectivo_ventas)}")
        lineas.append(f"Esperado en el cajón: {formatear_dinero(self._efectivo_esperado)}")
        resumen = BodyLabel("\n".join(lineas), self)
        resumen.setWordWrap(True)
        resumen.setTextColor(*_tinta("texto"))
        return resumen

    def _armar_formulario(self) -> QFormLayout:
        formulario = QFormLayout()
        formulario.setSpacing(10)
        self.spnDeclarado = DoubleSpinBox(self)
        self.spnDeclarado.setDecimals(2)
        self.spnDeclarado.setMinimum(0.0)
        self.spnDeclarado.setMaximum(IMPORTE_MAXIMO)
        self.spnDeclarado.setPrefix("$ ")
        self.spnDeclarado.setValue(max(self._efectivo_esperado, 0.0))
        formulario.addRow(BodyLabel("Efectivo contado:", self), self.spnDeclarado)

        self.txtNotas = LineEdit(self)
        self.txtNotas.setPlaceholderText("Opcional")
        formulario.addRow(BodyLabel("Notas:", self), self.txtNotas)
        return formulario

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnCerrar = PrimaryPushButton("Cerrar turno", self)
        self.btnCancelar.setAutoDefault(False)
        self.btnCerrar.setDefault(True)
        botones.addWidget(self.btnCancelar)
        botones.addStretch(1)
        botones.addWidget(self.btnCerrar)
        self.btnCancelar.clicked.connect(self.reject)
        self.btnCerrar.clicked.connect(self.guardar)
        return botones

    @property
    def datos(self) -> tuple[float, str]:
        return self._datos

    def actualizar_diferencia(self) -> None:
        diferencia = float(diferencia_montos(
            self.spnDeclarado.value(), self._efectivo_esperado))
        if abs(diferencia) < 0.01:
            self.lblDiferencia.setText("Cuadra: no hay diferencia.")
            self.lblDiferencia.setTextColor(*_tinta("exito"))
            return
        if diferencia > 0:
            self.lblDiferencia.setText(
                f"Sobrante: {formatear_dinero(diferencia)}")
            self.lblDiferencia.setTextColor(*_tinta("exito"))
            return
        self.lblDiferencia.setText(
            f"Faltante: {formatear_dinero(-diferencia)}")
        self.lblDiferencia.setTextColor(*_tinta("error"))

    def guardar(self) -> None:
        self._datos = (self.spnDeclarado.value(), self.txtNotas.text().strip())
        self.accept()
