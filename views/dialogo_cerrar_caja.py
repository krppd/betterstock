from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.estilos import ROJO_TEXTO, VERDE_TEXTO, TAMANO_BODY, fuente
from utils.formato import diferencia as diferencia_montos
from utils.formato import formatear_dinero


class DialogoCerrarCaja(QDialog):
    def __init__(self, declarado: float, esperado: float | None = None,
                 ciego: bool = False, devoluciones_total: float = 0.0,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Confirmar cierre de caja")
        self.setMinimumWidth(380)
        self._datos: str = ""
        self._devoluciones_total = devoluciones_total

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 16, 18, 16)

        formulario = QFormLayout()
        formulario.setSpacing(10)

        if not ciego and esperado is not None:
            lbl_esp = QLabel(formatear_dinero(esperado), self)
            lbl_esp.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
            formulario.addRow("Esperado:", lbl_esp)

        lbl_dec = QLabel(formatear_dinero(declarado), self)
        lbl_dec.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        formulario.addRow("Declarado:", lbl_dec)

        if devoluciones_total > 0:
            lbl_dev = QLabel(formatear_dinero(devoluciones_total), self)
            lbl_dev.setObjectName("lblDevoluciones")
            lbl_dev.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
            formulario.addRow("Devoluciones del día:", lbl_dev)

        if not ciego and esperado is not None:
            dif = float(diferencia_montos(declarado, esperado))
            if abs(dif) < 0.01:
                txt_dif = "Cuadra"
                color_dif = VERDE_TEXTO
            elif dif > 0:
                txt_dif = f"Sobrante: {formatear_dinero(dif)}"
                color_dif = VERDE_TEXTO
            else:
                txt_dif = f"Faltante: {formatear_dinero(-dif)}"
                color_dif = ROJO_TEXTO
            lbl_dif = QLabel(txt_dif, self)
            lbl_dif.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
            lbl_dif.setStyleSheet(f"color: {color_dif};")
            formulario.addRow("Diferencia:", lbl_dif)

        self.txtNotas = QLineEdit(self)
        self.txtNotas.setObjectName("txtNotasCierre")
        self.txtNotas.setPlaceholderText("Observaciones (opcional)")
        self.txtNotas.setMinimumHeight(32)
        formulario.addRow("Observaciones:", self.txtNotas)

        layout.addLayout(formulario)

        botones = QHBoxLayout()
        botones.setSpacing(10)

        self.btnCancelar = QPushButton("Cancelar", self)
        self.btnCancelar.setMinimumHeight(36)
        self.btnCancelar.clicked.connect(self.reject)
        botones.addWidget(self.btnCancelar)

        self.btnConfirmar = QPushButton("Confirmar cierre", self)
        self.btnConfirmar.setObjectName("btnConfirmarCierre")
        self.btnConfirmar.setFont(fuente(TAMANO_BODY, negrita=True))
        self.btnConfirmar.setMinimumHeight(36)
        self.btnConfirmar.setStyleSheet(
            "background-color: #1E8149; color: #FFFFFF; border-radius: 6px; font-weight: bold;"
        )
        self.btnConfirmar.clicked.connect(self._confirmar)
        botones.addWidget(self.btnConfirmar)

        layout.addLayout(botones)

    @property
    def notas(self) -> str:
        return self._datos

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
