from __future__ import annotations

from dataclasses import dataclass, field

MODO_IGNORAR = "ignorar"
MODO_CATALOGO = "catalogo"
MODO_PRECIOS = "precios"
MODO_STOCK = "stock"

MODOS: tuple[str, ...] = (MODO_IGNORAR, MODO_CATALOGO, MODO_PRECIOS, MODO_STOCK)

EXISTENTE_ACTUALIZAR_TODO = "actualizar_todo"
EXISTENTE_ACTUALIZAR_PRECIOS = "actualizar_precios"
EXISTENTE_OMITIR = "omitir"

EXISTENTES: tuple[str, ...] = (
    EXISTENTE_ACTUALIZAR_TODO,
    EXISTENTE_ACTUALIZAR_PRECIOS,
    EXISTENTE_OMITIR,
)

PRECIO_VENTA = "venta"
PRECIO_COSTO = "costo"
PRECIO_CON_IVA = "con_iva"

PRECIOS: tuple[str, ...] = (PRECIO_VENTA, PRECIO_COSTO, PRECIO_CON_IVA)

FACTOR_IVA = 1.21


@dataclass
class ColumnaDetectada:
    nombre: str
    indice: int
    ejemplos: list[str] = field(default_factory=list)


@dataclass
class Seccion:
    titulo: str
    fila_inicio: int
    fila_fin: int
    filas: list[int] = field(default_factory=list)
    cabeceras: list[str] = field(default_factory=list)
    fila_cabecera: int | None = None
    tipo_sugerido: str = MODO_CATALOGO


@dataclass
class FilaMapeada:
    numero: int
    indice: int
    seccion: str
    valores: dict[str, str] = field(default_factory=dict)
    precios: dict[str, float] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)


@dataclass
class Mapeo:
    columnas: dict[str, int] = field(default_factory=dict)
    secciones: dict[int, str] = field(default_factory=dict)
    tipo_precio: str = PRECIO_VENTA


@dataclass
class Opciones:
    mapeo: Mapeo = field(default_factory=Mapeo)
    existentes: str = EXISTENTE_ACTUALIZAR_TODO
    crear_nuevos: bool = True
    archivo: str = ""


@dataclass
class Deteccion:
    ruta: str = ""
    delimitador: str = ","
    codificacion: str = "utf-8"
    encabezados: list[str] = field(default_factory=list)
    filas: list[list[str]] = field(default_factory=list)
    secciones: list[Seccion] = field(default_factory=list)
    columnas: list[ColumnaDetectada] = field(default_factory=list)
    mapeo: dict[str, int] = field(default_factory=dict)


@dataclass
class ResultadoImportacion:
    archivo: str = ""
    creados: int = 0
    actualizados: int = 0
    omitidos: int = 0
    recortados: int = 0
    errores: list[tuple[int, str]] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    backup: str = ""
