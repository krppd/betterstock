"""Diálogo con el resumen de una venta registrada y las acciones de impresión."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    PrimaryPushButton,
    SubtitleLabel,
    TransparentPushButton,
)

from ui.estilos import (
    TAMANO_BODY,
    TAMANO_DISPLAY,
    TAMANO_MICRO,
    TAMANO_SUBTITLE,
    fuente,
)
from ui.fluent import color
from utils.formato import formatear_dinero
from views.ventana_base import VentanaBase


class DialogoTicket(QDialog, VentanaBase):
    imprimir_pedido = pyqtSignal()

    def __init__(self, total: float, medio: str = "", monto_recibido: float = 0.0,
                 vuelto: float = 0.0, identificador: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._accion = "cerrar"
        self.setWindowTitle("Venta registrada")
        self.setObjectName("dlgTicket")
        self.setMinimumWidth(440)
        self._aplicar_tema()

        self.lblCabecera = SubtitleLabel(self)
        self.lblCabecera.setObjectName("lblCabecera")
        self.lblCabecera.setText("Venta registrada")
        self.lblCabecera.setFont(fuente(TAMANO_SUBTITLE, negrita=True))

        self.lblTotal = SubtitleLabel(self)
        self.lblTotal.setObjectName("lblTotal")
        self.lblTotal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblTotal.setFont(fuente(TAMANO_DISPLAY, negrita=True, tabular=True))
        self.lblTotal.setText(formatear_dinero(total))

        self.lblDetalle = BodyLabel(self)
        self.lblDetalle.setObjectName("lblDetalle")
        self.lblDetalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblDetalle.setFont(fuente(TAMANO_BODY))
        self.lblDetalle.setText(self._texto_detalle(medio, monto_recibido, vuelto))

        self.lblComprobante = BodyLabel(self)
        self.lblComprobante.setObjectName("lblComprobante")
        self.lblComprobante.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblComprobante.setFont(fuente(TAMANO_MICRO))
        self.lblComprobante.setStyleSheet(f"color: {color('texto_suave')};")
        self.lblComprobante.setText(f"Comprobante: {identificador}" if identificador else "")

        self.lblAviso = BodyLabel(self)
        self.lblAviso.setObjectName("lblAviso")
        self.lblAviso.setWordWrap(True)
        self.lblAviso.setFont(fuente(TAMANO_MICRO))
        self.lblAviso.setStyleSheet(f"color: {color('error')};")
        self.lblAviso.setVisible(False)

        self.btnImprimir = PrimaryPushButton("Imprimir ticket", self)
        self.btnImprimir.setObjectName("btnImprimir")
        self.btnImprimir.setMinimumHeight(34)
        self.btnImprimir.setDefault(True)
        self.btnImprimir.setToolTip("Imprime el ticket con la impresora del sistema.")
        self.btnImprimir.clicked.connect(self._pedir_impresion)

        self.btnCerrar = TransparentPushButton("Cerrar", self)
        self.btnCerrar.setObjectName("btnCerrar")
        self.btnCerrar.setMinimumHeight(34)
        self.btnCerrar.clicked.connect(self._cerrar)

        botones = QHBoxLayout()
        botones.setSpacing(8)
        botones.addWidget(self.btnImprimir)
        botones.addStretch(1)
        botones.addWidget(self.btnCerrar)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        layout.addWidget(self.lblCabecera)

        tarjeta = CardWidget(self)
        tarjeta.setObjectName("tarjetaTotal")
        contenido = QVBoxLayout(tarjeta)
        contenido.setContentsMargins(16, 12, 16, 12)
        contenido.setSpacing(4)
        contenido.addWidget(self.lblTotal)
        contenido.addWidget(self.lblDetalle)
        layout.addWidget(tarjeta)

        layout.addWidget(self.lblComprobante)
        layout.addWidget(self.lblAviso)
        layout.addLayout(botones)

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema claro/oscuro."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}"
        )

    @property
    def accion(self) -> str:
        return self._accion

    @staticmethod
    def _texto_detalle(medio: str, monto_recibido: float, vuelto: float) -> str:
        partes = []
        if medio:
            partes.append(medio)
        if monto_recibido:
            partes.append(f"Recibido {formatear_dinero(monto_recibido)}")
        if vuelto > 0:
            partes.append(f"Vuelto {formatear_dinero(vuelto)}")
        return " · ".join(partes)

    def _pedir_impresion(self) -> None:
        self.imprimiendo()
        self.imprimir_pedido.emit()

    def _cerrar(self) -> None:
        self._accion = "cerrar"
        self.reject()

    def imprimiendo(self) -> None:
        self.btnImprimir.setEnabled(False)
        self.btnCerrar.setEnabled(False)
        self.lblAviso.setStyleSheet(f"color: {color('texto_suave')};")
        self.lblAviso.setText("Mandando el ticket a la impresora…")
        self.lblAviso.setVisible(True)

    def mostrar_error(self, mensaje: str) -> None:
        self.btnImprimir.setEnabled(True)
        self.btnCerrar.setEnabled(True)
        self.lblAviso.setStyleSheet(f"color: {color('error')};")
        self.lblAviso.setText(
            f"{mensaje}\n\nLa venta quedó registrada igual. "
            "Podés cerrar.")
        self.lblAviso.setVisible(True)

    def terminar_impresion(self) -> None:
        self._accion = "imprimir"
        self.accept()
