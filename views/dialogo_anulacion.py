from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.codigo_anulacion import LARGO_CODIGO
from ui.estilos import ROJO_TEXTO, TAMANO_BODY, TAMANO_MICRO, fuente
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
        self.setMinimumWidth(440)

        self.lblCabecera = QLabel(self)
        self.lblCabecera.setObjectName("lblCabecera")
        self.lblCabecera.setWordWrap(True)
        font_cabecera = fuente(TAMANO_BODY, negrita=True)
        self.lblCabecera.setFont(font_cabecera)
        self.lblCabecera.setText(titulo or "Anular la venta con el código del supervisor.")

        self.lblCodigo = QLabel("Código del supervisor:", self)
        self.lblCodigo.setObjectName("lblCodigo")
        self.txtCodigo = QLineEdit(self)
        self.txtCodigo.setObjectName("txtCodigo")
        self.txtCodigo.setPlaceholderText("Código de 10 dígitos")
        self.txtCodigo.setMaxLength(LARGO_CODIGO)
        self.txtCodigo.setMinimumHeight(30)

        self.lblAyuda = QLabel(self)
        self.lblAyuda.setObjectName("lblAyuda")
        self.lblAyuda.setWordWrap(True)
        font_ayuda = fuente(TAMANO_MICRO)
        self.lblAyuda.setFont(font_ayuda)
        self.lblAyuda.setText(AYUDA_CODIGO)

        self.lblMotivo = QLabel("Motivo de la anulación:", self)
        self.lblMotivo.setObjectName("lblMotivo")
        self.txtMotivo = QTextEdit(self)
        self.txtMotivo.setObjectName("txtMotivo")
        self.txtMotivo.setPlaceholderText("Por ejemplo: se cobró mal, el cliente devolvió la mercadería.")
        self.txtMotivo.setFixedHeight(ALTO_MOTIVO)

        self.lblRecordatorio = QLabel(self)
        self.lblRecordatorio.setObjectName("lblRecordatorio")
        self.lblRecordatorio.setWordWrap(True)
        self.lblRecordatorio.setFont(font_ayuda)
        self.lblRecordatorio.setStyleSheet(f"color: {ROJO_TEXTO};")
        self.lblRecordatorio.setText(RECORDATORIO_PLAZO)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.btnAceptar = self.botones.button(QDialogButtonBox.StandardButton.Ok)
        self.btnAceptar.setText("Anular")
        self.btnAceptar.setObjectName("btnAceptar")
        self.btnAceptar.setDefault(True)
        self.btnCancelar = self.botones.button(QDialogButtonBox.StandardButton.Cancel)
        self.btnCancelar.setText("Cancelar")
        self.btnCancelar.setAutoDefault(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.addWidget(self.lblCabecera)
        layout.addWidget(self.lblCodigo)
        layout.addWidget(self.txtCodigo)
        layout.addWidget(self.lblAyuda)
        layout.addWidget(self.lblMotivo)
        layout.addWidget(self.txtMotivo)
        layout.addWidget(self.lblRecordatorio)
        layout.addWidget(self.botones)

        self.txtCodigo.textChanged.connect(self.actualizar)
        self.txtCodigo.returnPressed.connect(self.aceptar)
        self.botones.accepted.connect(self.aceptar)
        self.botones.rejected.connect(self.reject)
        self.actualizar()
        self.txtCodigo.setFocus()

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
