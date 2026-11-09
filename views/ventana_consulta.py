from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QWidget

from models.producto import Producto
from models.usuario import Usuario
from services.fotos import ruta_foto
from services.gestor_stock import GestorStock
from ui.estilos import AMBAR_TEXTO, ROJO_TEXTO, VERDE_TEXTO
from ui.manual.consulta_ui import Ui_ConsultaForm
from utils.formato import formatear_cantidad, formatear_dinero
from views.formulario_producto import FormularioProducto
from views.ventana_base import VentanaBase


class VentanaConsulta(QWidget, VentanaBase):
    def __init__(self, gestor_stock: GestorStock,
                 permiso: str = Usuario.PERMISO_ADMIN) -> None:
        super().__init__()
        self._gestor_stock = gestor_stock
        self._admin = Usuario.es_admin(permiso)
        self._coincidencias: list[Producto] = []
        self.ui = Ui_ConsultaForm()
        self.ui.setupUi(self)
        self.ui.btnBuscar.clicked.connect(self.buscar)
        self.ui.txtBuscar.returnPressed.connect(self.buscar)
        self.ui.lstCoincidencias.itemClicked.connect(self._elegir_de_lista)
        self.ui.btnAlta.clicked.connect(self.dar_de_alta)
        self.ui.btnLimpiar.clicked.connect(self.limpiar)
        self.ui.txtBuscar.setFocus()

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
            self.ui.lblStock.setStyleSheet(f"color: {ROJO_TEXTO};")
        elif producto.esta_en_stock_critico():
            self.ui.lblStock.setText(
                f"Stock bajo: {formatear_cantidad(producto.stock_actual)}"
                f" (mínimo {formatear_cantidad(producto.stock_minimo)})")
            self.ui.lblStock.setStyleSheet(f"color: {AMBAR_TEXTO};")
        else:
            self.ui.lblStock.setText(f"Stock: {formatear_cantidad(producto.stock_actual)}")
            self.ui.lblStock.setStyleSheet(f"color: {VERDE_TEXTO};")

    def _mostrar_imagen(self, producto: Producto) -> None:
        ruta = ruta_foto(producto.codigo)
        if ruta:
            retrato = QPixmap(ruta).scaled(
                320, 320, Qt.AspectRatioMode.KeepAspectRatio,
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