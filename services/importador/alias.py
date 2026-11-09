from __future__ import annotations

ALIAS: dict[str, list[str]] = {
    "codigo": [
        "codigo", "code", "sku", "cod", "art", "codart",
        "cod de barras", "codigo de barras", "codigo de producto",
        "referencia", "ref",
    ],
    "nombre": [
        "nombre", "descripcion", "articulo", "producto", "detalle",
        "nombre del producto", "descripcion del producto",
    ],
    "categoria": ["categoria", "rubro", "familia", "grupo"],
    "unidad_medida": [
        "unidad", "medida", "um", "unidad de medida", "unidad medida",
    ],
    "precio_costo": [
        "costo", "precio de costo", "precio costo", "compra",
        "costo anterior", "costo previo", "valor de compra",
    ],
    "precio_venta": [
        "precio", "precio de venta", "precio venta", "pv", "pvp",
        "lista", "precio lista", "precio de lista", "valor",
    ],
    "fecha_vencimiento": [
        "vencimiento", "fecha de vencimiento", "fecha vencimiento",
        "vence", "vto", "fecha vto", "caducidad", "fecha de caducidad",
        "fecha caducidad", "expira", "expiracion", "fecha de expiracion",
        "consumir antes de",
    ],
}

CAMPOS: tuple[str, ...] = (
    "codigo", "nombre", "categoria", "unidad_medida", "precio_costo",
    "precio_venta",
)

CAMPOS_OBLIGATORIOS: tuple[str, ...] = ("codigo", "nombre")

CAMPOS_PRECIO: tuple[str, ...] = ("precio_costo", "precio_venta")
