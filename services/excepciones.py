class ErrorNegocio(Exception):
    pass


class ErrorValidacion(ErrorNegocio):
    pass


class ProductoNoEncontradoError(ErrorNegocio):
    def __init__(self, codigo: str) -> None:
        super().__init__(f"No se encontró el producto con código {codigo}")
        self.codigo = codigo


class SinStockError(ErrorNegocio):
    def __init__(self, nombre: str) -> None:
        super().__init__(f"El producto {nombre} no tiene stock disponible.")
        self.nombre = nombre


class LimiteStockError(ErrorNegocio):
    def __init__(self) -> None:
        super().__init__("No hay más stock disponible para este producto.")
