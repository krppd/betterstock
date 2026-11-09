from __future__ import annotations

from models.comercio import Comercio
from repositories.comercio_repositorio import ComercioRepositorio


class GestorComercio:
    def __init__(self, repositorio: ComercioRepositorio) -> None:
        self._repositorio = repositorio
        self._comercio: Comercio | None = None

    @property
    def comercio(self) -> Comercio | None:
        return self._comercio

    def inicializar(self) -> None:
        self._repositorio.inicializar()
        self._comercio = self._repositorio.obtener()

    def necesita_configuracion(self) -> bool:
        return self._comercio is None

    def configurar(
        self, nombre: str, direccion: str = "", cuit: str = "", telefono: str = ""
    ) -> Comercio:
        comercio = Comercio(nombre, direccion, cuit, telefono)
        self._repositorio.guardar(comercio)
        self._comercio = comercio
        return comercio