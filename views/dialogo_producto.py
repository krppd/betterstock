"""Diálogo con el detalle de un producto."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    PrimaryPushButton,
    PushButton,
    TransparentPushButton,
)

from models.producto import Producto
from services.fotos import ruta_foto
from ui.estilos import TAMANO_BODY, fuente
from ui.fluent import color
from ui.widgets.etiqueta_texto import EtiquetaTexto
from utils.formato import formatear_cantidad, formatear_dinero


class ColorTema:
    """Color de un token de ``ui.fluent`` que se resuelve al consultarlo.

    Sirve para los atributos de clase que antes eran colores fijos: así el
    diálogo respeta el tema claro/oscuro sin perder la API pública.
    """

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre

    def __get__(self, _instancia, _tipo=None) -> str:
        return color(self.nombre)


class DialogoProducto(QDialog):
    """Muestra los datos de un producto, de solo lectura, y permite editarlo o eliminarlo.

    Editar y eliminar los resuelve quien abre el diálogo, a través de ``al_editar`` y
    ``al_eliminar``: cada una devuelve ``True`` si la acción se concretó, y en ese caso
    el diálogo se cierra.
    """

    COLOR_CRITICO = ColorTema("error")
    COLOR_PLACEHOLDER = ColorTema("gris_apagado")
    LADO_FOTO = 180
    MARGEN_FOTO = 6
    PORCENTAJE_ALTO = 0.75

    def __init__(
        self,
        producto: Producto,
        al_editar: Callable[[], bool],
        al_eliminar: Callable[[], bool],
        parent: QWidget | None = None,
        solo_lectura: bool = False,
    ) -> None:
        """Crea el diálogo para ``producto``."""
        super().__init__(parent)
        self._al_editar = al_editar
        self._al_eliminar = al_eliminar
        self._solo_lectura = solo_lectura
        self.setWindowTitle("Detalle del producto")
        self.setObjectName("dlgDetalleProducto")
        self._aplicar_tema()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self._desplazable = QScrollArea(self)
        self._desplazable.setWidgetResizable(True)
        self._desplazable.setFrameShape(QFrame.Shape.NoFrame)
        self._desplazable.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        contenido = QWidget(self._desplazable)
        cuerpo = QHBoxLayout(contenido)
        cuerpo.setContentsMargins(0, 0, 0, 0)
        cuerpo.setSpacing(20)
        cuerpo.addWidget(self._armar_foto(producto), 0, Qt.AlignmentFlag.AlignTop)
        cuerpo.addLayout(self._armar_datos(producto), 1)
        self._desplazable.setWidget(contenido)
        layout.addWidget(self._desplazable)
        layout.addWidget(self._armar_aviso(producto))
        layout.addStretch(1)
        layout.addLayout(self._armar_botones())

        self.setMinimumSize(520, 300)
        self.resize(560, 320)

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo y los textos siguen al tema claro/oscuro."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo')}; }}"
            f"QLabel {{ color: {color('texto')}; }}"
        )

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._ajustar_alto()

    def _ajustar_alto(self) -> None:
        contenido = self._desplazable.widget()
        if contenido is None:
            return
        maximo = int(self._alto_disponible() * self.PORCENTAJE_ALTO)
        alto = contenido.layout().minimumSize().height()
        self._desplazable.setMinimumHeight(min(alto, maximo))
        self._desplazable.setMaximumHeight(maximo)
        necesario = self.layout().minimumSize().height()
        if necesario > self.height():
            self.resize(self.width(), necesario)

    def _alto_disponible(self) -> int:
        pantalla = self.screen()
        if pantalla is None:
            return 800
        return pantalla.availableGeometry().height()

    def _armar_foto(self, producto: Producto) -> QFrame:
        """Arma el cuadro con la foto del producto, o "Sin imagen" si no hay una que se pueda leer."""
        marco = QFrame(self)
        marco.setObjectName("frameFoto")
        marco.setFixedSize(self.LADO_FOTO, self.LADO_FOTO)
        marco.setStyleSheet(
            f"QFrame#frameFoto {{ background-color: {color('fondo_tarjeta')}; "
            f"border: 1px solid {color('borde')}; border-radius: 6px; }}"
        )
        self.lblFoto = BodyLabel(marco)
        self.lblFoto.setObjectName("lblFoto")
        self.lblFoto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contenido = QVBoxLayout(marco)
        contenido.setContentsMargins(*(self.MARGEN_FOTO,) * 4)
        contenido.addWidget(self.lblFoto)

        ruta = ruta_foto(producto.codigo)
        retrato = QPixmap(ruta) if ruta else QPixmap()
        if retrato.isNull():
            self.lblFoto.setText("Sin imagen")
            self.lblFoto.setStyleSheet(f"color: {self.COLOR_PLACEHOLDER};")
        else:
            lado = self.LADO_FOTO - 2 * (self.MARGEN_FOTO + 1)
            self.lblFoto.setPixmap(retrato.scaled(
                lado, lado, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        return marco

    def _armar_datos(self, producto: Producto) -> QFormLayout:
        formulario = QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.setVerticalSpacing(10)
        formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        formulario.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        formulario.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        formulario.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.lblCodigo = self._agregar_dato(formulario, "Código:", producto.codigo)
        self.lblNombre = self._agregar_dato(formulario, "Nombre:", producto.nombre)
        self.lblNombre.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.lblCategoria = self._agregar_dato(formulario, "Categoría:", producto.categoria)
        self.lblStockActual = self._agregar_dato(
            formulario, "Stock actual:", formatear_cantidad(producto.stock_actual))
        self.lblStockMinimo = self._agregar_dato(
            formulario, "Stock mínimo:", formatear_cantidad(producto.stock_minimo))
        self.lblPrecio = self._agregar_dato(formulario, "Precio:", formatear_dinero(producto.precio_venta))
        return formulario

    def _armar_aviso(self, producto: Producto) -> BodyLabel:
        self.lblAviso = BodyLabel("El stock está en el mínimo o por debajo.", self)
        self.lblAviso.setObjectName("lblAviso")
        self.lblAviso.setStyleSheet(f"color: {self.COLOR_CRITICO};")
        self.lblAviso.setVisible(producto.esta_en_stock_critico())
        if producto.esta_en_stock_critico():
            self.lblStockActual.setStyleSheet(f"color: {self.COLOR_CRITICO};")
        return self.lblAviso

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnEditar = PrimaryPushButton("Editar", self)
        self.btnEliminar = PushButton("Eliminar", self)
        self.btnCerrar = TransparentPushButton("Cerrar", self)
        self.btnEditar.setAutoDefault(False)
        self.btnEliminar.setAutoDefault(False)
        self.btnCerrar.setDefault(True)
        botones.addWidget(self.btnEditar)
        botones.addWidget(self.btnEliminar)
        botones.addStretch(1)
        botones.addWidget(self.btnCerrar)

        if self._solo_lectura:
            self.btnEditar.hide()
            self.btnEliminar.hide()

        self.btnEditar.clicked.connect(self.editar)
        self.btnEliminar.clicked.connect(self.eliminar)
        self.btnCerrar.clicked.connect(self.reject)
        return botones

    def _agregar_dato(self, formulario: QFormLayout, etiqueta: str, valor: str) -> EtiquetaTexto:
        """Agrega una fila ``etiqueta: valor`` y devuelve la etiqueta del valor."""
        titulo = BodyLabel(etiqueta, self)
        titulo.setFont(fuente(TAMANO_BODY, negrita=True))
        dato = EtiquetaTexto(valor, self)
        formulario.addRow(titulo, dato)
        return dato

    def editar(self) -> None:
        """Abre la edición del producto y, si se guardó, cierra el diálogo."""
        if self._al_editar():
            self.accept()

    def eliminar(self) -> None:
        """Pide eliminar el producto y, si se eliminó, cierra el diálogo."""
        if self._al_eliminar():
            self.accept()
