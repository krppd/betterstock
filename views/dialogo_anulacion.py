"""Diálogo para anular una venta con el código del supervisor."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
    TextEdit,
)

from models.codigo_anulacion import LARGO_CODIGO
from ui.estilos import TAMANO_MICRO, fuente
from ui.fluent import color
from views.ventana_base import VentanaBase

AYUDA_CODIGO = "Escaneá el código del supervisor o tipealo."
RECORDATORIO_PLAZO = (
    "Solo se anulan ventas de las últimas 24 horas y de días que todavía no "
    "tienen el cierre de caja hecho."
)
CODIGO_INVALIDO = "El código no es válido."
ALTO_MOTIVO = 84


class DialogoAnulacion(QDialog, VentanaBase):
    def __init__(self, parent: QWidget | None = None, titulo: str = "",
                 validar_codigo: Callable[[str], bool] | None = None) -> None:
        super().__init__(parent)
        self._validar_codigo = validar_codigo
        self.setWindowTitle("Anular venta")
        self.setObjectName("dlgAnulacion")
        self.setMinimumWidth(440)
        self._aplicar_tema()

        self.lblCabecera = SubtitleLabel(self)
        self.lblCabecera.setObjectName("lblCabecera")
        self.lblCabecera.setWordWrap(True)
        self.lblCabecera.setText(titulo or "Anular la venta con el código del supervisor.")

        self.lblCodigo = BodyLabel("Código del supervisor:", self)
        self.lblCodigo.setObjectName("lblCodigo")
        self.txtCodigo = LineEdit(self)
        self.txtCodigo.setObjectName("txtCodigo")
        self.txtCodigo.setPlaceholderText("Código de 10 dígitos")
        self.txtCodigo.setMaxLength(LARGO_CODIGO)

        self.lblAyuda = BodyLabel(self)
        self.lblAyuda.setObjectName("lblAyuda")
        self.lblAyuda.setWordWrap(True)
        font_ayuda = fuente(TAMANO_MICRO)
        self.lblAyuda.setFont(font_ayuda)
        self.lblAyuda.setStyleSheet(f"color: {color('texto_suave')};")
        self.lblAyuda.setText(AYUDA_CODIGO)

        self.lblMotivo = BodyLabel("Motivo de la anulación:", self)
        self.lblMotivo.setObjectName("lblMotivo")
        self.txtMotivo = TextEdit(self)
        self.txtMotivo.setObjectName("txtMotivo")
        self.txtMotivo.setPlaceholderText("Por ejemplo: se cobró mal, el cliente devolvió la mercadería.")
        self.txtMotivo.setFixedHeight(ALTO_MOTIVO)

        self.lblRecordatorio = BodyLabel(self)
        self.lblRecordatorio.setObjectName("lblRecordatorio")
        self.lblRecordatorio.setWordWrap(True)
        self.lblRecordatorio.setFont(font_ayuda)
        self.lblRecordatorio.setStyleSheet(f"color: {color('error')};")
        self.lblRecordatorio.setText(RECORDATORIO_PLAZO)

        self.botones = self._armar_botones()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        layout.addWidget(self.lblCabecera)
        layout.addWidget(self.lblCodigo)
        layout.addWidget(self.txtCodigo)
        layout.addWidget(self.lblAyuda)
        layout.addWidget(self.lblMotivo)
        layout.addWidget(self.txtMotivo)
        layout.addWidget(self.lblRecordatorio)
        layout.addLayout(self.botones)

        self.txtCodigo.textChanged.connect(self.actualizar)
        self.txtCodigo.returnPressed.connect(self.aceptar)
        self.actualizar()
        self.txtCodigo.setFocus()

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema claro/oscuro."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}"
        )

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnAceptar = PrimaryPushButton("Anular", self)
        self.btnAceptar.setObjectName("btnAceptar")
        self.btnAceptar.setDefault(True)
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnCancelar.setObjectName("btnCancelar")
        self.btnCancelar.setAutoDefault(False)
        botones.addStretch(1)
        botones.addWidget(self.btnCancelar)
        botones.addWidget(self.btnAceptar)

        self.btnAceptar.clicked.connect(self.aceptar)
        self.btnCancelar.clicked.connect(self.reject)
        return botones

    @property
    def codigo(self) -> str:
        return self.txtCodigo.text().strip()

    @property
    def motivo(self) -> str:
        return self.txtMotivo.toPlainText().strip()

    @property
    def resultado(self) -> tuple[str, str]:
        return self.codigo, self.motivo

    def actualizar(self, *_args: object) -> None:
        self.btnAceptar.setEnabled(bool(self.codigo))

    def aceptar(self) -> None:
        if not self.codigo:
            self.mostrar_advertencia("Anular venta", "Escaneá o tipeá el código del supervisor.")
            self.txtCodigo.setFocus()
            return
        if self._validar_codigo is not None and not self._validar_codigo(self.codigo):
            self.mostrar_advertencia("Anular venta", CODIGO_INVALIDO)
            self.txtCodigo.selectAll()
            self.txtCodigo.setFocus()
            return
        if not self.motivo:
            self.mostrar_advertencia("Anular venta", "Escribí el motivo de la anulación.")
            self.txtMotivo.setFocus()
            return
        self.accept()
