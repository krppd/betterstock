from __future__ import annotations

from datetime import date

from models.movimiento import MOTIVO_DEVOLUCION_PREFIJO, Movimiento, MovimientoAjuste
from models.categoria import Categoria
from models.producto import Producto
from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from services.excepciones import ErrorValidacion
from utils.formato import redondear_cantidad


class GestorStock:
    TODOS_LOS_TIPOS = "Todos"

    def __init__(
        self,
        productos: ProductoRepositorio,
        movimientos: MovimientoRepositorio,
        categorias: CategoriaRepositorio,
    ) -> None:
        """Crea el gestor a partir de los repositorios de productos, de movimientos y de categorías."""
        self._productos = productos
        self._movimientos = movimientos
        self._categorias = categorias

    def inicializar(self) -> None:
        self._productos.inicializar()
        self._movimientos.inicializar()
        self._categorias.inicializar()

    @property
    def repositorio_productos(self) -> ProductoRepositorio:
        return self._productos

    def listar_productos(self) -> list[Producto]:
        return self._productos.listar()

    def buscar_producto(self, codigo: str) -> Producto | None:
        return self._productos.buscar(codigo)

    def buscar_productos(self, texto: str) -> list[Producto]:
        """Devuelve los productos cuyo código o nombre contienen ``texto`` (todos, si está vacío)."""
        return self._productos.buscar_por_texto(texto)

    def productos_por_codigo(self) -> dict[str, Producto]:
        return {p.codigo: p for p in self._productos.listar()}

    def guardar_producto(self, producto: Producto) -> None:
        if not producto.codigo.strip() or not producto.nombre.strip():
            raise ErrorValidacion("El código y el nombre son obligatorios.")
        producto.validar()
        self._productos.guardar(producto)

    def eliminar_producto(self, codigo: str) -> None:
        self._productos.eliminar(codigo)

    def productos_criticos(self) -> list[Producto]:
        return [p for p in self._productos.listar() if p.esta_en_stock_critico()]

    def stock_valorizado(self) -> float:
        return sum(p.valor_stock() for p in self._productos.listar())


    def listar_categorias(self) -> list[str]:
        """Devuelve los nombres de las categorías, en el orden en que se cargaron."""
        return [c.nombre for c in self._categorias.listar()]

    def agregar_categoria(self, nombre: str) -> str:
        """Da de alta una categoría y devuelve su nombre, ya sin espacios a los costados.

        Lanza ``ErrorValidacion`` si el nombre está vacío o si ya existe una categoría
        con ese nombre (sin distinguir mayúsculas de minúsculas).
        """
        nombre = nombre.strip()
        if not nombre:
            raise ErrorValidacion("El nombre de la categoría es obligatorio.")
        if self._categorias.existe(nombre):
            raise ErrorValidacion(f"Ya existe una categoría llamada '{nombre}'.")
        self._categorias.agregar(Categoria(nombre))
        return nombre

    def tipos_de_movimiento(self) -> list[str]:
        return Movimiento.tipos_disponibles()

    def registrar_movimiento(
        self, tipo: str, codigo_producto: str, cantidad: float, fecha: date, motivo: str = ""
    ) -> Movimiento:
        cantidad = redondear_cantidad(cantidad)
        if cantidad <= 0:
            raise ErrorValidacion("La cantidad debe ser mayor a 0.")
        try:
            movimiento = Movimiento.crear(tipo, fecha, codigo_producto, cantidad, motivo)
        except ValueError as error:
            raise ErrorValidacion(str(error)) from error

        producto = self._productos.buscar(codigo_producto)
        if producto is not None:
            try:
                producto.stock_actual = movimiento.aplicar_a(producto.stock_actual)
            except ValueError as error:
                raise ErrorValidacion(str(error)) from error

        self._movimientos.agregar(movimiento)

        if producto is not None:
            self._productos.guardar(producto)
        return movimiento

    def registrar_ajuste(
        self, codigo_producto: str, cantidad: float, fecha: date, motivo: str = ""
    ) -> Movimiento:
        cantidad = redondear_cantidad(cantidad)
        if cantidad < 0:
            raise ErrorValidacion("La cantidad no puede ser negativa.")
        try:
            movimiento = Movimiento.crear(
                MovimientoAjuste.TIPO, fecha, codigo_producto, cantidad, motivo)
        except ValueError as error:
            raise ErrorValidacion(str(error)) from error

        producto = self._productos.buscar(codigo_producto)
        if producto is not None:
            try:
                producto.stock_actual = movimiento.aplicar_a(producto.stock_actual)
            except ValueError as error:
                raise ErrorValidacion(str(error)) from error

        self._movimientos.agregar(movimiento)

        if producto is not None:
            self._productos.guardar(producto)
        return movimiento

    def listar_movimientos_recientes(self, motivo: str = "") -> list[Movimiento]:
        """Devuelve los movimientos del más nuevo al más viejo.

        ``motivo`` filtra por coincidencia exacta o por prefijo si es MOTIVO_DEVOLUCION_PREFIJO.
        """
        movimientos = list(reversed(self._movimientos.listar()))
        if motivo:
            if motivo == MOTIVO_DEVOLUCION_PREFIJO:
                movimientos = [
                    m for m in movimientos if m.motivo.startswith(MOTIVO_DEVOLUCION_PREFIJO)
                ]
            else:
                movimientos = [m for m in movimientos if m.motivo == motivo]
        return movimientos

    def motivos_de_movimientos(self) -> list[str]:
        """Motivos registrados, sin repetir y ordenados alfabéticamente."""
        return sorted({
            m.motivo
            for m in self._movimientos.listar()
            if m.motivo and not m.motivo.startswith(MOTIVO_DEVOLUCION_PREFIJO)
        })

    def hay_devoluciones_en_movimientos(self) -> bool:
        return any(
            m.motivo.startswith(MOTIVO_DEVOLUCION_PREFIJO)
            for m in self._movimientos.listar()
        )

    def filtrar_movimientos(
        self, desde: date, hasta: date, tipo: str = TODOS_LOS_TIPOS,
        motivo: str = "",
    ) -> list[Movimiento]:
        return [
            m for m in self.listar_movimientos_recientes(motivo)
            if desde <= m.fecha <= hasta and (tipo == self.TODOS_LOS_TIPOS or m.tipo == tipo)
        ]
