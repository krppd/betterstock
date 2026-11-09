from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ui.manual.campo_cantidad import CampoCantidad
from views.ventana_base import VentanaBase


class DialogoCantidad(QDialog, VentanaBase):
    """Ingreso de cantidad siguiendo la unidad del producto elegida."""

    MAXIMO_CANTIDAD = 999_999.999

    def __init__(self, titulo: str, pregunta: str, unidad: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(titulo)
        texto = f"{pregunta} ({unidad}):" if unidad else f"{pregunta}:"
        etiqueta = QLabel(texto, self)
        etiqueta.setFont(self._fuente())

        self.campo = CampoCantidad(self)
        self.campo.setMaximum(self.MAXIMO_CANTIDAD)
        self.campo.setValue(1)
        self.campo.setFixedHeight(self._alto_campo())
        self.campo.setFont(self._fuente())

        fila = QHBoxLayout()
        fila.setSpacing(10)
        fila.addWidget(etiqueta)
        fila.addWidget(self.campo, stretch=1)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setText("OK")
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setDefault(True)
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setAutoDefault(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(fila)
        layout.addWidget(self.botones)
        self.botones.accepted.connect(self.validar)
        self.botones.rejected.connect(self.reject)
        self.campo.returnPressed.connect(self.validar)

    def _fuente(self):
        from ui.estilos import TAMANO_BODY, fuente
        return fuente(TAMANO_BODY, tabular=True)

    def _alto_campo(self) -> int:
        from ui.estilos import TAMANO_BODY
        return round(TAMANO_BODY * 2.2)

    def cantidad(self) -> float:
        return self.campo.value()

    def validar(self) -> None:
        import math
        valor = self.cantidad()
        if not math.isfinite(valor) or valor <= 0:
            self.mostrar_advertencia("Reposición", "La cantidad debe ser mayor a cero.")
            self.campo.setFocus()
            return
        self.accept()


def pedir_cantidad(titulo: str, pregunta: str, unidad: str = "",
                   parent: QWidget | None = None) -> tuple[float, bool]:
    """Devuelve (cantidad, aceptado) con el punto decimal de la casa."""
    dialogo = DialogoCantidad(titulo, pregunta, unidad, parent=parent)
    aceptado = dialogo.exec() == QDialog.DialogCode.Accepted
    return dialogo.cantidad(), aceptado
