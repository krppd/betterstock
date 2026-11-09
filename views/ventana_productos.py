from __future__ import annotations

from datetime import date

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QWidget

from models.movimiento import MovimientoEntrada
from models.producto import Producto
from models.usuario import Usuario
from repositories.importacion_repositorio import ImportacionRepositorio
from services.excepciones import ErrorNegocio
from services.gestor_stock import GestorStock
from services.importador.servicio import ServicioImportacion
from services.plan_motor import CONTACTO, excedido, limite, reposicion_permitida
from ui.estilos import ROJO_TEXTO
from ui.generated.productos_ui import Ui_Form as Ui_ProductosForm
from ui.widgets.notificacion import Notificacion
from utils.formato import formatear_cantidad, formatear_dinero
from views.dialogo_categoria import DialogoCategoria
from views.dialogo_cantidad import pedir_cantidad
from views.dialogo_producto import DialogoProducto
from views.formulario_producto import FormularioProducto
from views.importador_productos import AvisoPlanGratis, ImportadorProductos
from views.ventana_base import VentanaBase
from views.ventana_recuento import VentanaRecuento


class VentanaProductos(QWidget, VentanaBase):
    """Muestra el listado de productos (en rojo los críticos) y permite buscarlos, crearlos, editarlos y eliminarlos."""

    COLOR_CRITICO = ROJO_TEXTO
    DEMORA_BUSQUEDA_MS = 250

    def __init__(self, gestor_stock: GestorStock,
                 permiso: str = Usuario.PERMISO_ADMIN) -> None:
        super().__init__()
        self._gestor_stock = gestor_stock
        self._admin = Usuario.es_admin(permiso)
        self.formulario: FormularioProducto | None = None
        self._productos_mostrados: list[Producto] = []
        self._limite_avisado = False
        self._servicio_importacion: ServicioImportacion | None = None
        self.ui = Ui_ProductosForm()
        self.ui.setupUi(self)
        self._acomodar_widgets()
        self.ui.tblProductos.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.tblProductos.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self._conectar_botones()
        self._aplicar_permisos()
        self._preparar_busqueda()
        self.cargar_datos()

    def _aplicar_permisos(self) -> None:
        if self._admin:
            return
        for boton in (
            self.ui.btnNuevo,
            self.ui.btnEditar,
            self.ui.btnEliminar,
            self.btnAgregarCategoria,
            self.btnReponer,
            self.btnRecuento,
            self.btnImportarLista,
        ):
            boton.hide()

    def _puede_editar(self) -> bool:
        if self._admin:
            return True
        self.mostrar_advertencia(
            "Acceso restringido",
            "Solo un administrador puede modificar productos y stock.")
        return False

    def al_mostrar(self) -> None:
        self.cargar_datos()

    def _conectar_botones(self) -> None:
        self.ui.btnNuevo.clicked.connect(self.abrir_formulario)
        self.ui.btnEditar.clicked.connect(self.editar_producto)
        self.ui.btnEliminar.clicked.connect(self.eliminar_producto)
        self.btnAgregarCategoria.clicked.connect(self.agregar_categoria)
        self.btnReponer.clicked.connect(self.reponer_stock)
        self.btnRecuento.clicked.connect(self.abrir_recuento)
        self.btnImportarLista.clicked.connect(self.importar_lista)

    def _preparar_busqueda(self) -> None:
        self._temporizador_busqueda = QTimer(self)
        self._temporizador_busqueda.setSingleShot(True)
        self._temporizador_busqueda.setInterval(self.DEMORA_BUSQUEDA_MS)
        self._temporizador_busqueda.timeout.connect(self.cargar_datos)
        self.ui.txtBuscar.textChanged.connect(lambda _texto: self._temporizador_busqueda.start())
        self.ui.txtBuscar.returnPressed.connect(self.abrir_detalle_buscado)
        self.ui.tblProductos.cellDoubleClicked.connect(self._abrir_detalle_de_fila)

    def _acomodar_widgets(self) -> None:
        """Mete el contenido en un layout, para que acompañe el redimensionado.

        En el ``.ui`` quedó con posición y tamaño fijos.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 9)
        layout.addWidget(self.ui.layoutWidget)
        self.btnAgregarCategoria = QPushButton("Agregar categoría", self.ui.layoutWidget)
        self.ui.horizontalLayout_2.addWidget(self.btnAgregarCategoria)
        self.btnReponer = QPushButton("Reponer stock", self.ui.layoutWidget)
        self.ui.horizontalLayout_2.addWidget(self.btnReponer)
        self.btnRecuento = QPushButton("Recuento", self.ui.layoutWidget)
        self.ui.horizontalLayout_2.addWidget(self.btnRecuento)
        self.btnImportarLista = QPushButton("Importar lista", self.ui.layoutWidget)
        self.ui.horizontalLayout_2.addWidget(self.btnImportarLista)
        self.estirar_columnas(self.ui.tblProductos)
        self.ui.tblProductos.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ui.tblProductos.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMinimumSize(720, 360)

    def cargar_datos(self) -> None:
        """Vuelve a llenar la tabla con los productos que coinciden con el buscador (todos, si está vacío)."""
        self._temporizador_busqueda.stop()
        productos = self._gestor_stock.buscar_productos(self.ui.txtBuscar.text())
        self._productos_mostrados = productos
        filas = [
            [p.codigo, p.nombre, p.categoria, formatear_cantidad(p.stock_actual),
             formatear_cantidad(p.stock_minimo), formatear_dinero(p.precio_venta)]
            for p in productos
        ]
        colores = [self.COLOR_CRITICO if p.esta_en_stock_critico() else None for p in productos]
        self.llenar_tabla(self.ui.tblProductos, filas, colores)

    def abrir_formulario(self) -> None:
        if not self._puede_editar():
            return
        self._mostrar_formulario(FormularioProducto(
            self._gestor_stock, al_antes_de_guardar=self._al_antes_de_guardar))

    def agregar_categoria(self) -> None:
        """Abre el alta de una categoría, que después aparece en el formulario de producto."""
        if not self._puede_editar():
            return
        DialogoCategoria(self._gestor_stock, self).exec()

    def abrir_recuento(self) -> None:
        if not self._puede_editar():
            return
        dialogo = VentanaRecuento(self._gestor_stock, self)
        dialogo.exec()
        dialogo.deleteLater()
        self.cargar_datos()

    def importar_lista(self) -> None:
        """Abre el asistente para importar una lista de productos desde un archivo CSV."""
        if not self._puede_editar():
            return
        servicio = self._obtener_servicio_importacion()
        if servicio.limite_alcanzado():
            AvisoPlanGratis(self).exec()
            return
        asistente = ImportadorProductos(servicio, self)
        asistente.exec()
        resultado = asistente.resultado()
        asistente.deleteLater()
        self.cargar_datos()
        if resultado is not None and resultado.recortados:
            Notificacion(self).mostrar(
                "Importación limitada",
                f"El plan admite hasta {limite('productos')} productos: "
                f"{resultado.recortados} filas nuevas quedaron fuera.")

    def _obtener_servicio_importacion(self) -> ServicioImportacion:
        if self._servicio_importacion is None:
            repositorio = self._gestor_stock.repositorio_productos
            self._servicio_importacion = ServicioImportacion(
                repositorio,
                ImportacionRepositorio(repositorio.ruta_archivo),
            )
        return self._servicio_importacion

    def reponer_stock(self) -> None:
        if not self._puede_editar():
            return
        codigo = self._codigo_seleccionado("Seleccione un producto para reponer.")
        if codigo is None:
            return
        producto = self._gestor_stock.buscar_producto(codigo)
        unidad = producto.unidad_medida if producto is not None else ""
        cantidad, aceptado = pedir_cantidad(
            "Reponer stock", "Cantidad que ingresa:", unidad, parent=self)
        if not aceptado:
            return
        tope = limite("productos")
        nota_tope = None
        if tope is not None and producto is not None:
            cupo = tope - (producto.stock_actual or 0.0)
            if not reposicion_permitida(producto.stock_actual or 0.0, cantidad):
                if cupo <= 0:
                    texto_unidad = unidad or "unidades"
                    Notificacion(self).mostrar(
                        "Tope del plan",
                        f"{producto.nombre} ya alcanzó el tope de "
                        f"{formatear_cantidad(tope)} {texto_unidad} del plan.")
                    return
                nota_tope = (f"El plan admite hasta {formatear_cantidad(tope)} "
                             "unidades por producto.")
                cantidad = cupo
        try:
            self._gestor_stock.registrar_movimiento(
                MovimientoEntrada.TIPO, codigo, cantidad, date.today(), "Reposición")
        except ErrorNegocio as error:
            self.mostrar_advertencia("Error", str(error))
            return
        self.cargar_datos()
        nombre = producto.nombre if producto is not None else codigo
        texto_unidad = unidad or "unidades"
        aviso = (f"Se repuso {formatear_cantidad(cantidad)} {texto_unidad} de {nombre}.")
        if nota_tope:
            aviso += f" {nota_tope}"
        Notificacion(self).mostrar("Stock repuesto", aviso)

    def editar_producto(self) -> None:
        if not self._puede_editar():
            return
        codigo = self._codigo_seleccionado("Seleccione un producto para editar.")
        if codigo is None:
            return
        producto = self._gestor_stock.buscar_producto(codigo)
        if producto is not None:
            self._editar(producto)

    def eliminar_producto(self) -> None:
        if not self._puede_editar():
            return
        codigo = self._codigo_seleccionado("Seleccione un producto para eliminar.")
        if codigo is None:
            return
        fila = self.ui.tblProductos.selectedItems()[0].row()
        nombre = self.ui.tblProductos.item(fila, 1).text()
        self._eliminar(codigo, nombre)

    def abrir_detalle_buscado(self) -> None:
        """Abre el detalle del producto buscado, al presionar Enter en el buscador.

        Si el texto es exactamente un código, abre ese producto; si no, el de la
        primera fila de la tabla filtrada. Si no hay coincidencias, avisa.
        """
        texto = self.ui.txtBuscar.text().strip()
        if not texto:
            return
        self.cargar_datos()
        if not self._productos_mostrados:
            self.mostrar_informacion("Productos", "No se encontró ningún producto")
            return
        exacto = next((p for p in self._productos_mostrados if p.codigo.casefold() == texto.casefold()), None)
        self._abrir_detalle(exacto or self._productos_mostrados[0])

    def _abrir_detalle_de_fila(self, fila: int, _columna: int) -> None:
        if 0 <= fila < len(self._productos_mostrados):
            self._abrir_detalle(self._productos_mostrados[fila])

    def _abrir_detalle(self, producto: Producto) -> None:
        """Muestra el detalle de ``producto``; editar y eliminar usan la misma lógica que los botones."""
        DialogoProducto(
            producto,
            al_editar=lambda: self._editar(producto),
            al_eliminar=lambda: self._eliminar(producto.codigo, producto.nombre),
            parent=self,
            solo_lectura=not self._admin,
        ).exec()

    def _editar(self, producto: Producto) -> bool:
        """Abre el formulario de edición de ``producto``. Devuelve ``True`` si se guardó."""
        if not self._puede_editar():
            return False
        return self._mostrar_formulario(FormularioProducto(self._gestor_stock, producto))

    def _al_antes_de_guardar(self, producto: Producto) -> None:
        self._avisar_limite_productos(producto)

    def _avisar_limite_productos(self, producto: Producto) -> None:
        if self._limite_avisado:
            return
        try:
            if self._gestor_stock.repositorio_productos.buscar(producto.codigo) is not None:
                return
            cantidad = len(self._gestor_stock.listar_productos())
        except Exception:
            return
        if not excedido("productos", cantidad + 1):
            return
        maximo = limite("productos")
        titulo = "Gratis"
        eleccion = self.elegir(
            "Límite del plan",
            f"Llegaste al límite de {maximo} productos del plan {titulo}. "
            "Podés pasar a un plan superior para seguir sumando productos.",
            [
                ("planes", "Ver planes", "aceptar"),
                ("continuar", "Continuar igual", "ayuda"),
            ],
        )
        if eleccion != "continuar":
            self._limite_avisado = True
            QDesktopServices.openUrl(QUrl(f"mailto:{CONTACTO}"))
            raise ErrorNegocio(
                f"El plan {titulo} admite hasta {maximo} productos. "
                "Se canceló el guardado.")

    def _eliminar(self, codigo: str, nombre: str) -> bool:
        """Elimina el producto, previa confirmación. Devuelve ``True`` si se eliminó."""
        if not self._puede_editar():
            return False
        if not self.confirmar("Confirmar", f"¿Está seguro que desea eliminar el producto '{nombre}'?"):
            return False
        self._gestor_stock.eliminar_producto(codigo)
        self.cargar_datos()
        return True

    def _codigo_seleccionado(self, mensaje_si_no_hay: str) -> str | None:
        seleccion = self.ui.tblProductos.selectedItems()
        if not seleccion:
            self.mostrar_advertencia("Error", mensaje_si_no_hay)
            return None
        return self.ui.tblProductos.item(seleccion[0].row(), 0).text()

    def _mostrar_formulario(self, formulario: FormularioProducto) -> bool:
        self.formulario = formulario
        if formulario.exec() == QDialog.DialogCode.Accepted:
            self.cargar_datos()
            Notificacion(self).mostrar("Producto guardado", "Los cambios se guardaron correctamente.")
            return True
        return False
