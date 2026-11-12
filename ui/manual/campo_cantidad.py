from __future__ import annotations

from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QRegularExpressionValidator
from qfluentwidgets import LineEdit

from utils.formato import DECIMALES_CANTIDAD, formatear_cantidad, redondear_cantidad

MAXIMO_CANTIDAD = 999_999.999
PATRON_CANTIDAD = QRegularExpression(rf"^\d{{0,9}}([.,]\d{{0,{DECIMALES_CANTIDAD}}})?$")


class CampoCantidad(LineEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._maximo = MAXIMO_CANTIDAD
        self.setValidator(QRegularExpressionValidator(PATRON_CANTIDAD, self))
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def maximum(self) -> float:
        return self._maximo

    def setMaximum(self, valor: float) -> None:
        self._maximo = float(valor)

    def setValue(self, valor: float) -> None:
        if not valor:
            self.setText("")
            return
        self.setText(formatear_cantidad(valor))

    def value(self) -> float:
        texto = self.text().strip()
        if not texto:
            return 0.0
        return redondear_cantidad(texto.replace(",", "."))

    def es_valido(self) -> bool:
        texto = self.text().strip()
        if not texto:
            return True
        try:
            float(texto.replace(",", "."))
        except ValueError:
            return False
        return True
