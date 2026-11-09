from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.codigo_anulacion import LARGO_CODIGO
from models.venta_registrada import VentaRegistrada
from services.devoluciones import cantidades_devueltas
from ui.estilos import TAMANO_BODY, TAMANO_MICRO, fuente
from utils.formato import formatear_cantidad, formatear_dinero
from views.ventana_base import VentanaBase

CODIGO_INVALIDO = "El código no es válido."


class DialogoDevolucion(QDialog, VentanaBase):
    def __init__(
        self,
        parent: QWidget | None,
        venta: VentaRegistrada,
        validar_codigo: Callable[[str], bool] | None = None,
        base: str | Path | None = None,
    ) -> None:
        super().__init__(parent)
        self._venta = venta
        self._validar_codigo = validar_codigo
        self._base = base
        self.spinboxes: dict[str, QDoubleSpinBox] = {}
        self.subtotal_items: dict[str, QTableWidgetItem] = {}
        self._devueltos_previos = cantidades_devueltas(
            venta.identificador, base=self._base
        )

        self.setWindowTitle("Devolución parcial")
        self.setMinimumWidth(640)
        self.setMinimumHeight(460)

        self.lblCabecera = QLabel(
            f"Devolución parcial - Venta #{venta.identificador} ({venta.fecha_texto})",
            self,
        )
        self.lblCabecera.setFont(fuente(TAMANO_BODY, negrita=True))

        self.tblItems = QTableWidget(self)
        self.tblItems.setColumnCount(6)
        self.tblItems.setHorizontalHeaderLabels(
            ["Código", "Producto", "Vendida", "Devuelta", "A devolver", "Subtotal"]
        )
        self.tblItems.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )

        self.lblTotal = QLabel("Total a devolver: $0,00", self)
        self.lblTotal.setFont(fuente(TAMANO_BODY, negrita=True))
        self.lblTotal.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.lblCodigo = QLabel("Código del supervisor:", self)
        self.txtCodigo = QLineEdit(self)
        self.txtCodigo.setPlaceholderText("Código de 10 dígitos")
        self.txtCodigo.setMaxLength(LARGO_CODIGO)
        self.txtCodigo.setMinimumHeight(30)

        self.lblMotivo = QLabel("Motivo de la devolución:", self)
        self.txtMotivo = QLineEdit(self)
        self.txtMotivo.setPlaceholderText("Por ejemplo: producto defectuoso, cambio de talle")
        self.txtMotivo.setMinimumHeight(30)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self.btnAceptar = self.botones.button(QDialogButtonBox.StandardButton.Ok)
        self.btnAceptar.setText("Devolver")
        self.btnCancelar = self.botones.button(QDialogButtonBox.StandardButton.Cancel)
        self.btnCancelar.setText("Cancelar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.addWidget(self.lblCabecera)
        layout.addWidget(self.tblItems, 1)
        layout.addWidget(self.lblTotal)
        layout.addWidget(self.lblCodigo)
        layout.addWidget(self.txtCodigo)
        layout.addWidget(self.lblMotivo)
        layout.addWidget(self.txtMotivo)
        layout.addWidget(self.botones)

        self.botones.accepted.connect(self.aceptar)
        self.botones.rejected.connect(self.reject)

        self._cargar_items()
        self._actualizar_totales()

    def _cargar_items(self) -> None:
        renglones = self._venta.detalle
        self.tblItems.setRowCount(len(renglones))

        for fila, renglon in enumerate(renglones):
            codigo = renglon.codigo
            devuelta_previa = self._devueltos_previos.get(codigo, 0.0)
            disponible = max(0.0, renglon.cantidad - devuelta_previa)

            item_codigo = QTableWidgetItem(codigo)
            item_codigo.setFlags(item_codigo.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tblItems.setItem(fila, 0, item_codigo)

            item_nombre = QTableWidgetItem(renglon.nombre)
            item_nombre.setFlags(item_nombre.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tblItems.setItem(fila, 1, item_nombre)

            item_vendida = QTableWidgetItem(formatear_cantidad(renglon.cantidad))
            item_vendida.setFlags(item_vendida.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tblItems.setItem(fila, 2, item_vendida)

            item_devuelta = QTableWidgetItem(formatear_cantidad(devuelta_previa))
            item_devuelta.setFlags(item_devuelta.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tblItems.setItem(fila, 3, item_devuelta)

            spinbox = QDoubleSpinBox(self.tblItems)
            spinbox.setMinimum(0.0)
            spinbox.setMaximum(disponible)
            spinbox.setDecimals(2)
            spinbox.setSingleStep(1.0)
            spinbox.setValue(0.0)
            spinbox.setEnabled(disponible > 0)
            spinbox.valueChanged.connect(self._actualizar_totales)
            self.spinboxes[codigo] = spinbox
            self.tblItems.setCellWidget(fila, 4, spinbox)

            item_subtotal = QTableWidgetItem("$0,00")
            item_subtotal.setFlags(item_subtotal.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.subtotal_items[codigo] = item_subtotal
            self.tblItems.setItem(fila, 5, item_subtotal)

    def _precio_unitario(self, codigo: str) -> float:
        for r in self._venta.detalle:
            if r.codigo == codigo:
                return (
                    round(r.subtotal / r.cantidad, 2)
                    if r.cantidad
                    else r.precio_unitario
                )
        return 0.0

    def _actualizar_totales(self) -> None:
        total = 0.0
        for codigo, spinbox in self.spinboxes.items():
            cant = spinbox.value()
            pu = self._precio_unitario(codigo)
            subtotal = round(cant * pu, 2)
            total += subtotal
            if codigo in self.subtotal_items:
                self.subtotal_items[codigo].setText(formatear_dinero(subtotal))
        self.lblTotal.setText(f"Total a devolver: {formatear_dinero(total)}")

    @property
    def total_devolucion(self) -> float:
        total = 0.0
        for codigo, spinbox in self.spinboxes.items():
            total += round(spinbox.value() * self._precio_unitario(codigo), 2)
        return round(total, 2)

    @property
    def items_a_devolver(self) -> list[dict[str, Any]]:
        items = []
        for codigo, spinbox in self.spinboxes.items():
            cant = spinbox.value()
            if cant > 0:
                pu = self._precio_unitario(codigo)
                items.append(
                    {
                        "codigo_producto": codigo,
                        "cantidad": cant,
                        "precio_unitario": pu,
                        "subtotal": round(cant * pu, 2),
                    }
                )
        return items

    @property
    def codigo(self) -> str:
        return self.txtCodigo.text().strip()

    @property
    def motivo(self) -> str:
        return self.txtMotivo.text().strip()

    def aceptar(self) -> None:
        if not self.items_a_devolver:
            self.mostrar_advertencia(
                "Devolución parcial", "Indicá una cantidad mayor a 0 para devolver."
            )
            return
        if not self.codigo:
            self.mostrar_advertencia(
                "Devolución parcial", "Escaneá o tipeá el código del supervisor."
            )
            self.txtCodigo.setFocus()
            return
        if self._validar_codigo is not None and not self._validar_codigo(self.codigo):
            self.mostrar_advertencia("Devolución parcial", CODIGO_INVALIDO)
            self.txtCodigo.selectAll()
            self.txtCodigo.setFocus()
            return
        if not self.motivo:
            self.mostrar_advertencia(
                "Devolución parcial", "Escribí el motivo de la devolución."
            )
            self.txtMotivo.setFocus()
            return
        self.accept()
