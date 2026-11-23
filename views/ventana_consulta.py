from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    FluentIcon as FIF,
    ListWidget,
    PrimaryPushButton,
    SearchLineEdit,
    SubtitleLabel,
    TransparentPushButton,
    qconfig,
)

from models.producto import Producto
from models.usuario import Usuario
from services.fotos import ruta_foto
from services.gestor_stock import GestorStock
from ui.estilos import TAMANO_HERO, TAMANO_TITLE, fuente
from ui.fluent import CLARO, OSCURO, color
from utils.formato import formatear_cantidad, formatear_dinero
from views.formulario_producto import FormularioProducto
from views.ventana_base import VentanaBase

LADO_FOTO = 400


def _tintar(etiqueta, token: str) -> None:
    """Aplica a una etiqueta Fluent el color de un token de ui.fluent (claro y oscuro)."""
    etiqueta.setTextColor(
        QColor(CLARO.get(token, "#000000")),
        QColor(OSCURO.get(token, "#FFFFFF")),
    )


class _UiConsulta:
    """Interfaz Fluent de la consulta de precios.

    Conserva los nombres de widget heredados (``txtBuscar``, ``btnAlta``…) para
    no romper el código ni los tests que los consultan.
    """

    def __init__(self, ventana: QWidget) -> None:
        self.lblBuscar = BodyLabel("Código o nombre:", ventana)
        self.lblBuscar.setObjectName("lblBuscar")

        self.txtBuscar = SearchLineEdit(ventana)
        self.txtBuscar.setObjectName("txtBuscar")
        self.txtBuscar.setPlaceholderText("Escaneá o escribí y apretá Enter")
        self.txtBuscar.setClearButtonEnabled(True)

        self.btnBuscar = PrimaryPushButton(FIF.SEARCH, "Buscar", ventana)
        self.btnBuscar.setObjectName("btnBuscar")

        self.lblEstado = BodyLabel("", ventana)
        self.lblEstado.setObjectName("lblEstado")
        self.lblEstado.setWordWrap(True)

        self.lstCoincidencias = ListWidget(ventana)
        self.lstCoincidencias.setObjectName("lstCoincidencias")
        self.lstCoincidencias.setMaximumHeight(160)
        self.lstCoincidencias.setVisible(False)

        self.lblNombre = SubtitleLabel("", ventana)
        self.lblNombre.setObjectName("lblNombre")
        self.lblNombre.setWordWrap(True)
        self.lblNombre.setFont(fuente(TAMANO_TITLE, negrita=True))

        self.lblCodigo = BodyLabel("", ventana)
        self.lblCodigo.setObjectName("lblCodigo")
        self.lblCodigo.setWordWrap(True)

        self.lblPrecio = SubtitleLabel("", ventana)
        self.lblPrecio.setObjectName("lblPrecio")
        self.lblPrecio.setFont(fuente(TAMANO_HERO, negrita=True, tabular=True))

        self.lblOferta = BodyLabel("", ventana)
        self.lblOferta.setObjectName("lblOferta")
        self.lblOferta.setWordWrap(True)
        self.lblOferta.setVisible(False)

        self.lblStock = BodyLabel("", ventana)
        self.lblStock.setObjectName("lblStock")

        self.lblImagen = QLabel(ventana)
        self.lblImagen.setObjectName("lblImagen")
        self.lblImagen.setMinimumSize(LADO_FOTO, LADO_FOTO)
        self.lblImagen.setMaximumSize(LADO_FOTO, LADO_FOTO)
        self.lblImagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblImagen.setScaledContents(False)

        self.btnAlta = PrimaryPushButton(FIF.ADD, "Dar de alta con este código", ventana)
        self.btnAlta.setObjectName("btnAlta")
        self.btnAlta.setVisible(False)

        self.btnLimpiar = TransparentPushButton(FIF.SYNC, "Limpiar", ventana)
        self.btnLimpiar.setObjectName("btnLimpiar")

        self.tarjeta = CardWidget(ventana)
        self.tarjeta.setObjectName("tarjeta")
        self.tarjeta.setBorderRadius(8)

        self.verticalLayout = QVBoxLayout(ventana)
        self.verticalLayout.setContentsMargins(20, 16, 20, 16)
        self.verticalLayout.setSpacing(12)

        self.hlyBuscar = QHBoxLayout()
        self.hlyBuscar.setSpacing(8)
        self.hlyBuscar.addWidget(self.lblBuscar)
        self.hlyBuscar.addWidget(self.txtBuscar, 1)
        self.hlyBuscar.addWidget(self.btnBuscar)

        self.vlyDatos = QVBoxLayout()
        self.vlyDatos.setSpacing(6)
        self.vlyDatos.addWidget(self.lblNombre)
        self.vlyDatos.addWidget(self.lblCodigo)
        self.vlyDatos.addWidget(self.lblPrecio)
        self.vlyDatos.addWidget(self.lblOferta)
        self.vlyDatos.addWidget(self.lblStock)
        self.vlyDatos.addStretch(1)

        self.vlyImagen = QVBoxLayout()
        self.vlyImagen.setSpacing(6)
        self.vlyImagen.addWidget(self.lblImagen)
        self.vlyImagen.addStretch(1)

        self.hlyDetalle = QHBoxLayout()
        self.hlyDetalle.setSpacing(16)
        self.hlyDetalle.addLayout(self.vlyDatos, 3)
        self.hlyDetalle.addLayout(self.vlyImagen, 1)

        self.lyTarjeta = QVBoxLayout(self.tarjeta)
        self.lyTarjeta.setContentsMargins(16, 16, 16, 16)
        self.lyTarjeta.addLayout(self.hlyDetalle)

        self.hlyBotones = QHBoxLayout()
        self.hlyBotones.setSpacing(8)
        self.hlyBotones.addWidget(self.btnAlta)
        self.hlyBotones.addStretch(1)
        self.hlyBotones.addWidget(self.btnLimpiar)

        self.verticalLayout.addLayout(self.hlyBuscar)
        self.verticalLayout.addWidget(self.lblEstado)
        self.verticalLayout.addWidget(self.lstCoincidencias)
        self.verticalLayout.addWidget(self.tarjeta, 1)
        self.verticalLayout.addLayout(self.hlyBotones)

        self._aplicar_temas()

    def _aplicar_temas(self) -> None:
        """Pinta las pastillas y los bordes con los colores del tema activo."""
        _tintar(self.lblPrecio, "exito")
        _tintar(self.lblOferta, "alerta")
        self.lblImagen.setStyleSheet(
            f"border: 1px solid {color('borde')};"
            f" background-color: {color('fondo_suave')};"
            " border-radius: 8px;")


class VentanaConsulta(QWidget, VentanaBase):
    """Consulta de precios por código o nombre de producto."""

    def __init__(self, gestor_stock: GestorStock,
                 permiso: str = Usuario.PERMISO_ADMIN) -> None:
        super().__init__()
        self._gestor_stock = gestor_stock
        self._admin = Usuario.es_admin(permiso)
        self._coincidencias: list[Producto] = []
        self.ui = _UiConsulta(self)
        self.setWindowTitle("Consultar Precio")
        self.setMinimumSize(700, 560)
        self.ui.btnBuscar.clicked.connect(self.buscar)
        self.ui.txtBuscar.returnPressed.connect(self.buscar)
        self.ui.lstCoincidencias.itemClicked.connect(self._elegir_de_lista)
        self.ui.btnAlta.clicked.connect(self.dar_de_alta)
        self.ui.btnLimpiar.clicked.connect(self.limpiar)
        self.ui.txtBuscar.setFocus()
        if hasattr(qconfig, "themeChanged"):
            qconfig.themeChanged.connect(self.ui._aplicar_temas)

    def al_mostrar(self) -> None:
        self.ui.txtBuscar.setFocus()
        self.ui.txtBuscar.selectAll()

    def buscar(self) -> None:
        texto = self.ui.txtBuscar.text().strip()
        self._reiniciar_resultados()
        if not texto:
            self._limpiar_tarjeta()
            self.ui.lblEstado.setText("Escribí un código o parte del nombre.")
            return

        exacto = self._gestor_stock.buscar_producto(texto)
        if exacto is not None:
            self.mostrar(exacto)
            return

        self._coincidencias = self._buscar_por_nombre(texto)
        if len(self._coincidencias) == 1:
            self.mostrar(self._coincidencias[0])
        elif self._coincidencias:
            self._listar_coincidencias()
        else:
            self._avisar_sin_resultados(texto)
        self.ui.txtBuscar.selectAll()

    def _reiniciar_resultados(self) -> None:
        self._coincidencias = []
        self.ui.lstCoincidencias.clear()
        self.ui.lstCoincidencias.setVisible(False)
        self.ui.btnAlta.setVisible(False)

    def _buscar_por_nombre(self, texto: str) -> list[Producto]:
        return self._gestor_stock.buscar_productos(texto)

    def _listar_coincidencias(self) -> None:
        self._limpiar_tarjeta()
        self.ui.lblEstado.setText(
            f"{len(self._coincidencias)} productos: elegí uno de la lista.")
        for producto in self._coincidencias:
            self.ui.lstCoincidencias.addItem(
                f"{producto.codigo} — {producto.nombre} ({formatear_dinero(producto.precio_vigente())})")
        self.ui.lstCoincidencias.setVisible(True)

    def _avisar_sin_resultados(self, texto: str) -> None:
        self._limpiar_tarjeta()
        self.ui.lblEstado.setText(f"Sin resultados para '{texto}'.")
        self.ui.btnAlta.setVisible(self._admin)

    def mostrar(self, producto: Producto) -> None:
        self.ui.lblEstado.setText("")
        self.ui.lstCoincidencias.setVisible(False)
        self.ui.btnAlta.setVisible(False)
        self._mostrar_datos(producto)
        self._mostrar_oferta(producto)
        self._aplicar_color_stock(producto)
        self._mostrar_imagen(producto)
        self.ui.txtBuscar.selectAll()

    def _mostrar_datos(self, producto: Producto) -> None:
        self.ui.lblNombre.setText(producto.nombre)
        categoria = f" · {producto.categoria}" if producto.categoria else ""
        unidad = f" ({producto.unidad_medida})" if producto.unidad_medida else ""
        self.ui.lblCodigo.setText(f"Código {producto.codigo}{categoria}{unidad}")
        self.ui.lblPrecio.setText(formatear_dinero(producto.precio_vigente()))

    def _mostrar_oferta(self, producto: Producto) -> None:
        if producto.en_oferta():
            self.ui.lblOferta.setText(
                f"OFERTA · antes {formatear_dinero(producto.precio_venta)}")
            self.ui.lblOferta.setVisible(True)
        else:
            self.ui.lblOferta.setVisible(False)

    def _aplicar_color_stock(self, producto: Producto) -> None:
        if not producto.tiene_stock():
            self.ui.lblStock.setText("SIN STOCK")
            _tintar(self.ui.lblStock, "error")
        elif producto.esta_en_stock_critico():
            self.ui.lblStock.setText(
                f"Stock bajo: {formatear_cantidad(producto.stock_actual)}"
                f" (mínimo {formatear_cantidad(producto.stock_minimo)})")
            _tintar(self.ui.lblStock, "alerta")
        else:
            self.ui.lblStock.setText(f"Stock: {formatear_cantidad(producto.stock_actual)}")
            _tintar(self.ui.lblStock, "exito")

    def _mostrar_imagen(self, producto: Producto) -> None:
        ruta = ruta_foto(producto.codigo)
        if ruta:
            retrato = QPixmap(ruta).scaled(
                LADO_FOTO, LADO_FOTO, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self.ui.lblImagen.setPixmap(retrato)
            self.ui.lblImagen.setText("")
        else:
            self.ui.lblImagen.setPixmap(QPixmap())
            self.ui.lblImagen.setText("Sin imagen")

    def dar_de_alta(self) -> None:
        if not self._admin:
            self.mostrar_advertencia(
                "Acceso restringido",
                "Solo un administrador puede dar de alta productos.")
            return
        codigo = self.ui.txtBuscar.text().strip()
        if not codigo:
            return
        formulario = FormularioProducto(self._gestor_stock, codigo_inicial=codigo)
        if formulario.exec() == QDialog.DialogCode.Accepted:
            self.buscar()
        else:
            self.ui.txtBuscar.setFocus()
            self.ui.txtBuscar.selectAll()

    def limpiar(self) -> None:
        self.ui.txtBuscar.clear()
        self._coincidencias = []
        self.ui.lstCoincidencias.clear()
        self.ui.lstCoincidencias.setVisible(False)
        self.ui.btnAlta.setVisible(False)
        self._limpiar_tarjeta()
        self.ui.txtBuscar.setFocus()

    def _elegir_de_lista(self, item) -> None:
        fila = self.ui.lstCoincidencias.row(item)
        if 0 <= fila < len(self._coincidencias):
            self.mostrar(self._coincidencias[fila])

    def _limpiar_tarjeta(self) -> None:
        self.ui.lblNombre.setText("")
        self.ui.lblCodigo.setText("")
        self.ui.lblPrecio.setText("")
        self.ui.lblOferta.setVisible(False)
        self.ui.lblStock.setText("")
        self.ui.lblImagen.setPixmap(QPixmap())
        self.ui.lblImagen.setText("Sin imagen")
