"""Diálogo para pedir una cantidad en la unidad del producto elegido."""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, PrimaryPushButton, PushButton

from ui.fluent import color
from ui.manual.campo_cantidad import CampoCantidad
from views.ventana_base import VentanaBase


class CampoCantidadFluent(CampoCantidad):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)


class DialogoCantidad(QDialog, VentanaBase):
    """Ingreso de cantidad siguiendo la unidad del producto elegida."""

    MAXIMO_CANTIDAD = 999_999.999

    def __init__(self, titulo: str, pregunta: str, unidad: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setObjectName("dlgCantidad")
        self._aplicar_tema()
        texto = f"{pregunta} ({unidad}):" if unidad else f"{pregunta}:"
        etiqueta = BodyLabel(texto, self)
        etiqueta.setObjectName("lblPregunta")
        etiqueta.setFont(self._fuente())

        self.campo = CampoCantidadFluent(self)
        self.campo.setObjectName("campoCantidad")
        self.campo.setMaximum(self.MAXIMO_CANTIDAD)
        self.campo.setValue(1)
        self.campo.setFixedHeight(self._alto_campo())
        self.campo.setPlaceholderText("0")

        fila = QHBoxLayout()
        fila.setSpacing(10)
        fila.addWidget(etiqueta)
        fila.addWidget(self.campo, stretch=1)

        self.botones = self._armar_botones()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addLayout(fila)
        layout.addLayout(self.botones)
        self.campo.returnPressed.connect(self.validar)

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema claro/oscuro."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}"
        )

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnAceptar = PrimaryPushButton("Aceptar", self)
        self.btnCancelar.setAutoDefault(False)
        self.btnAceptar.setDefault(True)
        botones.addStretch(1)
        botones.addWidget(self.btnCancelar)
        botones.addWidget(self.btnAceptar)

        self.btnCancelar.clicked.connect(self.reject)
        self.btnAceptar.clicked.connect(self.validar)
        return botones

    def _fuente(self):
        from ui.estilos import TAMANO_BODY, fuente
        return fuente(TAMANO_BODY, tabular=True)

    def _alto_campo(self) -> int:
        """Alto del campo de texto, el mismo que usan los campos de Fluent."""
        return 33

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
