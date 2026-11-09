from __future__ import annotations

from services.importador.alias import ALIAS, CAMPOS
from services.importador.deteccion import normalizar, parsear_precio
from services.importador.modelo import MODO_CATALOGO, MODO_PRECIOS, MODO_STOCK, Seccion

_ALIAS_TODOS: set[str] = {
    normalizar(alias) for campo in CAMPOS for alias in ALIAS[campo]
}

_ALIAS_NOMBRE: set[str] = {normalizar(alias) for alias in ALIAS["nombre"]}
_ALIAS_PRECIO: set[str] = (
    {normalizar(alias) for alias in ALIAS["precio_venta"]}
    | {normalizar(alias) for alias in ALIAS["precio_costo"]}
)
_ALIAS_STOCK: set[str] = {
    "stock", "stockactual", "stockminimo", "existencia", "existencias",
    "cantidad", "cantstock",
}


def recortar_vacias(celdas: list[str]) -> list[str]:
    lista = [str(celda or "").strip() for celda in celdas]
    while lista and not lista[-1]:
        lista.pop()
    return lista


def es_fila_de_encabezados(fila: list[str]) -> bool:
    valores = [normalizar(celda) for celda in fila]
    conocidos = [valor for valor in valores if valor in _ALIAS_TODOS]
    return len(conocidos) >= 2


def es_fila_separadora(fila: list[str]) -> bool:
    celdas = [str(celda or "").strip() for celda in fila]
    while celdas and not celdas[-1]:
        celdas.pop()
    if not celdas or len(celdas) > 3:
        return False
    if len(celdas) == len(fila):
        return False
    if es_fila_de_encabezados(fila):
        return False
    return not any(parsear_precio(celda) is not None for celda in celdas)


def detectar_secciones(filas: list[list[str]]) -> list[Seccion]:
    if not filas:
        return []
    ancho = max(len(fila) for fila in filas)
    completas = [list(fila) + [""] * (ancho - len(fila)) for fila in filas]
    secciones: list[Seccion] = []
    titulo = ""
    fila_inicio = 0
    bloque: list[int] = []

    for indice, fila in enumerate(completas):
        if not any(str(celda or "").strip() for celda in fila):
            continue
        if es_fila_separadora(fila):
            secciones.append(_armar_seccion(titulo, fila_inicio, bloque, completas))
            titulo = _titulo_de(fila)
            fila_inicio = indice
            bloque = []
            continue
        bloque.append(indice)

    secciones.append(_armar_seccion(titulo, fila_inicio, bloque, completas))
    return [seccion for seccion in secciones if seccion.filas or seccion.cabeceras]


def _titulo_de(fila: list[str]) -> str:
    for celda in fila:
        texto = str(celda or "").strip()
        if texto:
            return texto
    return ""


def _armar_seccion(
    titulo: str,
    fila_inicio: int,
    bloque: list[int],
    filas: list[list[str]],
) -> Seccion:
    fila_cabecera: int | None = None
    cabeceras: list[str] = []
    datos = list(bloque)
    if datos and es_fila_de_encabezados(filas[datos[0]]):
        fila_cabecera = datos[0]
        cabeceras = recortar_vacias(filas[datos[0]])
        datos = datos[1:]
    if datos:
        fin = datos[-1]
    elif fila_cabecera is not None:
        fin = fila_cabecera
    else:
        fin = fila_inicio
    return Seccion(
        titulo=titulo,
        fila_inicio=fila_inicio,
        fila_fin=fin,
        filas=datos,
        cabeceras=cabeceras,
        fila_cabecera=fila_cabecera,
        tipo_sugerido=_tipo_sugerido(cabeceras),
    )


def _tipo_sugerido(cabeceras: list[str]) -> str:
    valores = {normalizar(cabecera) for cabecera in cabeceras}
    if valores & _ALIAS_NOMBRE:
        return MODO_CATALOGO
    if valores & _ALIAS_PRECIO:
        return MODO_PRECIOS
    if valores & _ALIAS_STOCK:
        return MODO_STOCK
    return MODO_CATALOGO
