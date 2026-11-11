from __future__ import annotations

import math
from collections.abc import Callable

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QHBoxLayout
from qfluentwidgets import TransparentPushButton

from models.producto import Producto
from models.venta import validar_texto_sin_separadores
from services.excepciones import ErrorNegocio
from services.fotos import ruta_foto
from services.gestor_stock import GestorStock
from services.plan_motor import limite
from ui.fluent import color
from ui.generated.formulario_Producto_ui import Ui_Dialog as Ui_FormularioProducto
from utils.formato import formatear_cantidad, formatear_dinero
from views.dialogo_categoria import DialogoCategoria
from views.ventana_base import VentanaBase
from views.ventana_fotos import VentanaFotos

ALICUOTAS_IVA = (0.0, 10.5, 21.0, 27.0)


class FormularioProducto(QDialog, VentanaBase):
    def __init__(self, gestor_stock: GestorStock, producto: Producto | None = None,
                 codigo_inicial: str = "",
                 al_antes_de_guardar: Callable[[Producto], None] | None = None) -> None:
        super().__init__()
        self._gestor_stock = gestor_stock
        self._al_antes_de_guardar = al_antes_de_guardar
        self.ui = Ui_FormularioProducto()
        self._categoria_original = producto.categoria if producto is not None else ""
        self.ui.setupUi(self)
        self.setObjectName("dlgFormularioProducto")
        self._aplicar_tema()

        self.lblVencimiento = getattr(self.ui, "lblVencimiento", None)
        self.dateVencimiento = getattr(self.ui, "dateVencimiento", None)
        if self.lblVencimiento is not None:
            self.lblVencimiento.hide()
        if self.dateVencimiento is not None:
            self.dateVencimiento.hide()

        for widget in (
            getattr(self.ui, "lblPromoCantidad", None),
            getattr(self.ui, "spnPromoCantidad", None),
            getattr(self.ui, "lblPromoPrecio", None),
            getattr(self.ui, "spnPromoPrecio", None),
        ):
            if widget is not None:
                widget.hide()

        self._agregar_boton_categoria()
        self._cargar_categorias(self._categoria_original)
        self._avisar_maximos()
        self.ui.btnGuardar.clicked.connect(self.guardar_producto)
        self.ui.btnCancelar.clicked.connect(self.reject)
        self.ui.btnFoto.clicked.connect(self.buscar_foto)
        self._ventana_fotos = None
        self._stock_original = 0.0

        if producto is not None:
            self._mostrar_producto(producto)
        elif codigo_inicial.strip():
            self.ui.txtCodigo.setText(codigo_inicial.strip())
        self._refrescar_foto()

    def _aplicar_tema(self) -> None:
        """El fondo del formulario sigue al tema claro/oscuro."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}"
        )

    def _avisar_maximos(self) -> None:
        precio = f"Máximo: {formatear_dinero(Producto.PRECIO_MAXIMO)}."
        unidades = f"Máximo: {formatear_cantidad(Producto.STOCK_MAXIMO)} unidades."
        self.ui.spnPrecioCosto.setToolTip(precio)
        self.ui.spnPrecioVenta.setToolTip(precio)
        self.ui.spnPrecioOferta.setToolTip(precio)
        self.ui.spnStock.setToolTip(unidades)
        self.ui.spnStockMinimo.setToolTip(unidades)

    def _agregar_boton_categoria(self) -> None:
        """Pone un botón "+" al lado del combo de categoría, para crear una sin salir del formulario."""
        self.btnNuevaCategoria = TransparentPushButton("+", self)
        self.btnNuevaCategoria.setObjectName("btnNuevaCategoria")
        self.btnNuevaCategoria.setToolTip("Agregar categoría")
        self.btnNuevaCategoria.setMaximumWidth(40)
        self.btnNuevaCategoria.setAutoDefault(False)
        self.btnNuevaCategoria.clicked.connect(self.nueva_categoria)

        fila = QHBoxLayout()
        self.ui.gridLayout.removeWidget(self.ui.cmbCategoria)
        fila.addWidget(self.ui.cmbCategoria, 1)
        fila.addWidget(self.btnNuevaCategoria)
        self.ui.gridLayout.addLayout(fila, 2, 1, 1, 1)
        self.setTabOrder(self.ui.cmbCategoria, self.btnNuevaCategoria)

    def _cargar_categorias(self, seleccionada: str = "") -> None:
        """Recarga el combo con las categorías guardadas y deja elegida ``seleccionada``.

        La primera opción queda en blanco, porque la categoría es opcional.
        """
        categorias = self._gestor_stock.listar_categorias()
        if self._categoria_original and self._categoria_original not in categorias:
            categorias.append(self._categoria_original)
        combo = self.ui.cmbCategoria
        combo.clear()
        combo.addItem("")
        combo.addItems(categorias)
        combo.setCurrentIndex(max(combo.findText(seleccionada), 0))

    def nueva_categoria(self) -> None:
        """Abre el alta de categoría y, si se guardó, la deja elegida en el combo."""
        dialogo = DialogoCategoria(self._gestor_stock, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._cargar_categorias(dialogo.nombre)

    def _mostrar_producto(self, producto: Producto) -> None:
        self.ui.txtCodigo.setText(producto.codigo)
        self.ui.txtCodigo.setEnabled(False)
        self.ui.txtNombre.setText(producto.nombre)
        self.ui.txtUnidad.setText(producto.unidad_medida)
        self._ampliar_spinbox(self.ui.spnPrecioCosto, producto.precio_costo)
        self.ui.spnPrecioCosto.setValue(producto.precio_costo)
        self._ampliar_spinbox(self.ui.spnPrecioVenta, producto.precio_venta)
        self.ui.spnPrecioVenta.setValue(producto.precio_venta)
        self._ampliar_spinbox(self.ui.spnPrecioOferta, producto.precio_oferta)
        self.ui.spnPrecioOferta.setValue(producto.precio_oferta)
        try:
            self.ui.cmbIva.setCurrentIndex(ALICUOTAS_IVA.index(producto.alicuota_iva))
        except ValueError:
            self.ui.cmbIva.setCurrentIndex(ALICUOTAS_IVA.index(Producto.ALICUOTA_POR_DEFECTO))
        self.ui.spnStock.setValue(producto.stock_actual)
        self._stock_original = producto.stock_actual
        self.ui.spnStockMinimo.setValue(producto.stock_minimo)
        self._refrescar_foto()

    @staticmethod
    def _ampliar_spinbox(spinbox, valor: float) -> None:
        if not math.isfinite(valor):
            return
        if valor > spinbox.maximum():
            spinbox.setMaximum(math.ceil(valor))

    def _codigo_formulario(self) -> str:
        return self.ui.txtCodigo.text().strip()

    def _cantidades_validas(self) -> bool:
        for campo, etiqueta in (
            (self.ui.spnStock, "El stock actual"),
            (self.ui.spnStockMinimo, "El stock mínimo"),
        ):
            if campo.es_valido():
                continue
            self.mostrar_advertencia(
                "Error",
                f"{etiqueta} debe ser un número, por ejemplo 2,5.")
            campo.setFocus()
            return False
        return True

    def _refrescar_foto(self) -> None:
        ruta = ruta_foto(self._codigo_formulario())
        if ruta:
            retrato = QPixmap(ruta).scaled(
                120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self.ui.lblFotoMini.setPixmap(retrato)
            self.ui.lblFotoMini.setText("")
        else:
            self.ui.lblFotoMini.setPixmap(QPixmap())
            self.ui.lblFotoMini.setText("Sin foto")

    def buscar_foto(self) -> None:
        codigo = self._codigo_formulario()
        if not codigo:
            self.mostrar_advertencia("Foto", "Primero poné el código del producto.")
            return
        dialogo = VentanaFotos(codigo, self.ui.txtNombre.text().strip(), parent=self)
        self._ventana_fotos = dialogo
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._refrescar_foto()

    def guardar_producto(self) -> None:
        codigo = self.ui.txtCodigo.text().strip()
        nombre = self.ui.txtNombre.text().strip()
        try:
            validar_texto_sin_separadores(codigo, "El código del producto")
            validar_texto_sin_separadores(nombre, "El nombre del producto")
        except ValueError as error:
            self.mostrar_advertencia("Error", str(error))
            return
        if not self._cantidades_validas():
            return
        vencimiento = None
        try:
            producto = Producto(
                codigo=codigo,
                nombre=nombre,
                categoria=self.ui.cmbCategoria.currentText(),
                unidad_medida=self.ui.txtUnidad.text().strip(),
                precio_costo=self.ui.spnPrecioCosto.value(),
                precio_venta=self.ui.spnPrecioVenta.value(),
                precio_oferta=self.ui.spnPrecioOferta.value(),
                stock_actual=self.ui.spnStock.value(),
                stock_minimo=self.ui.spnStockMinimo.value(),
                alicuota_iva=ALICUOTAS_IVA[self.ui.cmbIva.currentIndex()],
            )
            tope = limite("productos")
            if (tope is not None and producto.stock_actual > tope
                    and producto.stock_actual > self._stock_original):
                raise ErrorNegocio(
                    f"El plan admite hasta {formatear_cantidad(tope)} unidades por producto.")
            if self._al_antes_de_guardar is not None:
                try:
                    self._al_antes_de_guardar(producto)
                except ErrorNegocio:
                    raise
                except Exception:
                    pass
            self._gestor_stock.guardar_producto(producto)
        except (ErrorNegocio, ValueError) as error:
            self.mostrar_advertencia("Error", str(error))
            return

        self.accept()
