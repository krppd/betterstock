from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    qconfig,
)

from ui.fluent import CLARO, OSCURO, color
from utils.formato import diferencia as diferencia_montos
from utils.formato import formatear_dinero


def _tinta(nombre: str) -> tuple[QColor, QColor]:
    """Devuelve el par (claro, oscuro) de un token Fluent para labels adaptativos."""
    return QColor(CLARO[nombre]), QColor(OSCURO[nombre])


class DialogoCerrarCaja(QDialog):
    """Confirmación del cierre del día, con el detalle de lo declarado y esperado."""

    def __init__(self, declarado: float, esperado: float | None = None,
                 ciego: bool = False, devoluciones_total: float = 0.0,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Confirmar cierre de caja")
        self.setObjectName("dlgCerrarCaja")
        self.setMinimumWidth(400)
        self._datos: str = ""
        self._devoluciones_total = devoluciones_total
        self._aplicar_tema()
        qconfig.themeChanged.connect(self._aplicar_tema)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 18, 20, 18)

        formulario = QFormLayout()
        formulario.setSpacing(10)
        formulario.setLabelAlignment(formulario.labelAlignment())
        formulario.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        if not ciego and esperado is not None:
            lbl_esp = StrongBodyLabel(formatear_dinero(esperado), self)
            lbl_esp.setTextColor(*_tinta("texto"))
            formulario.addRow(BodyLabel("Esperado:", self), lbl_esp)

        lbl_dec = StrongBodyLabel(formatear_dinero(declarado), self)
        lbl_dec.setTextColor(*_tinta("texto"))
        formulario.addRow(BodyLabel("Declarado:", self), lbl_dec)

        if devoluciones_total > 0:
            lbl_dev = StrongBodyLabel(formatear_dinero(devoluciones_total), self)
            lbl_dev.setObjectName("lblDevoluciones")
            lbl_dev.setTextColor(*_tinta("texto"))
            formulario.addRow(BodyLabel("Devoluciones del día:", self), lbl_dev)

        if not ciego and esperado is not None:
            dif = float(diferencia_montos(declarado, esperado))
            if abs(dif) < 0.01:
                txt_dif = "Cuadra"
                token_dif = "exito"
            elif dif > 0:
                txt_dif = f"Sobrante: {formatear_dinero(dif)}"
                token_dif = "exito"
            else:
                txt_dif = f"Faltante: {formatear_dinero(-dif)}"
                token_dif = "error"
            lbl_dif = StrongBodyLabel(txt_dif, self)
            lbl_dif.setTextColor(*_tinta(token_dif))
            formulario.addRow(BodyLabel("Diferencia:", self), lbl_dif)

        self.txtNotas = LineEdit(self)
        self.txtNotas.setObjectName("txtNotasCierre")
        self.txtNotas.setPlaceholderText("Observaciones (opcional)")
        formulario.addRow(BodyLabel("Observaciones:", self), self.txtNotas)

        layout.addLayout(formulario)

        botones = QHBoxLayout()
        botones.setSpacing(10)

        self.btnCancelar = PushButton("Cancelar", self)
        self.btnCancelar.setObjectName("btnCancelarCierre")
        self.btnCancelar.clicked.connect(self.reject)
        botones.addWidget(self.btnCancelar)

        self.btnConfirmar = PrimaryPushButton("Confirmar cierre", self)
        self.btnConfirmar.setObjectName("btnConfirmarCierre")
        self.btnConfirmar.clicked.connect(self._confirmar)
        botones.addWidget(self.btnConfirmar)

        layout.addLayout(botones)

    @property
    def notas(self) -> str:
        return self._datos

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema: los labels Fluent son claros en oscuro."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}")

    def _confirmar(self) -> None:
        self._datos = self.txtNotas.text().strip()
        self.accept()

    def exec(self) -> int:
        padre = self.parent()
        if padre is not None:
            metodo = getattr(padre, "confirmar", None)
            if metodo is not None and getattr(metodo, "__qualname__", "") != "VentanaBase.confirmar":
                if metodo("Cerrar caja", "¿Confirmar cierre?"):
                    self._datos = self.txtNotas.text().strip()
                    return QDialog.DialogCode.Accepted
                return QDialog.DialogCode.Rejected
        return super().exec()
