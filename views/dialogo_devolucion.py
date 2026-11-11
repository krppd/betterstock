"""Diálogo de devolución parcial de una venta."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    DoubleSpinBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
    TableWidget,
)

from models.codigo_anulacion import LARGO_CODIGO
from models.venta_registrada import VentaRegistrada
from services.devoluciones import cantidades_devueltas
from ui.estilos import TAMANO_BODY, fuente
from ui.fluent import color
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
        self.spinboxes: dict[str, DoubleSpinBox] = {}
        self.subtotal_items: dict[str, QTableWidgetItem] = {}
        self._devueltos_previos = cantidades_devueltas(
            venta.identificador, base=self._base
        )

        self.setWindowTitle("Devolución parcial")
        self.setObjectName("dlgDevolucion")
        self.setMinimumWidth(700)
        self.setMinimumHeight(460)
        self._aplicar_tema()

        self.lblCabecera = SubtitleLabel(
            f"Devolución parcial - Venta #{venta.identificador} ({venta.fecha_texto})",
            self,
        )
        self.lblCabecera.setObjectName("lblCabecera")
        self.lblCabecera.setFont(fuente(TAMANO_BODY, negrita=True))

        self.tblItems = TableWidget(self)
        self.tblItems.setObjectName("tblItems")
        self.tblItems.setColumnCount(6)
        self.tblItems.setHorizontalHeaderLabels(
            ["Código", "Producto", "Vendida", "Devuelta", "A devolver", "Subtotal"]
        )
        encabezado = self.tblItems.horizontalHeader()
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for columna, ancho in ((0, 80), (2, 80), (3, 85), (4, 140), (5, 95)):
            encabezado.setSectionResizeMode(columna, QHeaderView.ResizeMode.Interactive)
            self.tblItems.setColumnWidth(columna, ancho)

        self.lblTotal = BodyLabel("Total a devolver: $0,00", self)
        self.lblTotal.setObjectName("lblTotal")
        self.lblTotal.setFont(fuente(TAMANO_BODY, negrita=True, tabular=True))
        self.lblTotal.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.lblCodigo = BodyLabel("Código del supervisor:", self)
        self.lblCodigo.setObjectName("lblCodigo")
        self.txtCodigo = LineEdit(self)
        self.txtCodigo.setObjectName("txtCodigo")
        self.txtCodigo.setPlaceholderText("Código de 10 dígitos")
        self.txtCodigo.setMaxLength(LARGO_CODIGO)

        self.lblMotivo = BodyLabel("Motivo de la devolución:", self)
        self.lblMotivo.setObjectName("lblMotivo")
        self.txtMotivo = LineEdit(self)
        self.txtMotivo.setObjectName("txtMotivo")
        self.txtMotivo.setPlaceholderText("Por ejemplo: producto defectuoso, cambio de talle")

        self.botones = self._armar_botones()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        layout.addWidget(self.lblCabecera)
        layout.addWidget(self.tblItems, 1)
        layout.addWidget(self.lblTotal)
        layout.addWidget(self.lblCodigo)
        layout.addWidget(self.txtCodigo)
        layout.addWidget(self.lblMotivo)
        layout.addWidget(self.txtMotivo)
        layout.addLayout(self.botones)

        self._cargar_items()
        self._actualizar_totales()

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema claro/oscuro."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}"
        )

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnAceptar = PrimaryPushButton("Devolver", self)
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

            spinbox = DoubleSpinBox(self.tblItems)
            spinbox.setObjectName(f"spnDevolver_{codigo}")
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
        for renglon in self._venta.detalle:
            if renglon.codigo == codigo:
                return (
                    round(renglon.subtotal / renglon.cantidad, 2)
                    if renglon.cantidad
                    else renglon.precio_unitario
                )
        return 0.0

    def _actualizar_totales(self, *_args: object) -> None:
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
