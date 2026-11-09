
from __future__ import annotations

import unicodedata
from datetime import datetime

from models.comercio import Comercio
from models.venta import Venta
from utils.formato import formatear_cantidad

ANCHO_PAPEL = 32
"""Caracteres por línea en 58 mm."""


def _ascii(texto: str) -> str:
    desarmado = unicodedata.normalize("NFKD", texto)
    return "".join(letra for letra in desarmado if not unicodedata.combining(letra))


def _recortar(texto: str, ancho: int | None) -> str:
    if not ancho or len(texto) <= ancho:
        return texto
    if ancho <= 3:
        return texto[:ancho]
    return texto[:ancho - 3] + "..."


def _dos_columnas(izquierda: str, derecha: str) -> str:
    espacio = ANCHO_PAPEL - len(izquierda) - len(derecha)
    return izquierda + " " * max(1, espacio) + derecha


def _lineas_columnas(izquierda: str, derecha: str, extra: str = "",
                     ancho: int | None = None) -> list[str]:
    completa = izquierda + extra
    if not ancho:
        return [_dos_columnas(completa, derecha)]
    if len(completa) + 1 + len(derecha) <= ancho:
        return [_dos_columnas(completa, derecha)]
    if extra and len(izquierda) + 1 + len(derecha) <= ancho:
        return [_dos_columnas(izquierda, derecha), extra.strip()]
    if len(completa) <= ancho:
        return [completa, derecha.rjust(ancho)]
    return [_recortar(completa, ancho), _recortar(derecha, ancho)]


def _iva_por_alicuota(venta: Venta) -> dict[float, float]:
    totales: dict[float, float] = {}
    for item in venta.items:
        if item.iva:
            totales[item.alicuota_iva] = totales.get(item.alicuota_iva, 0.0) + item.iva
    return dict(sorted(totales.items()))


def _lineas_ticket(venta: Venta, comercio: Comercio | None = None,
                   monto_recibido: float = 0.0, vuelto: float = 0.0,
                   identificador: str = "", medio: str = "",
                   ancho: int | None = None) -> list[tuple[str, str]]:
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    lineas: list[tuple[str, str]] = [(_recortar(comercio.nombre if comercio else "BetterStock", ancho), "titulo")]
    if comercio:
        for valor in (comercio.direccion, comercio.cuit, comercio.telefono):
            if valor:
                texto = f"CUIT: {valor}" if valor == comercio.cuit else \
                        (f"Tel: {valor}" if valor == comercio.telefono else valor)
                lineas.append((_recortar(texto, ancho), "centro"))
    lineas += [("=" * ANCHO_PAPEL, "centro"), ("TICKET DE VENTA", "subtitulo"),
               (f"Fecha: {fecha}", "centro")]
    if identificador:
        lineas.append((f"Nro: {identificador}", "centro"))
    lineas.append(("=" * ANCHO_PAPEL, "centro"))

    lineas.append((_dos_columnas("CANTIDAD X PRECIO", "SUBTOTAL"), "izq"))
    lineas.append(("-" * ANCHO_PAPEL, "izq"))
    for item in venta.items:
        etiqueta = item.nombre
        if item.es_comodin:
            etiqueta += " (COMODÍN)"
        elif item.en_oferta:
            etiqueta += " (OFERTA)"
        lineas.append((_recortar(etiqueta, ancho), "negrita"))
        detalle = f"  {formatear_cantidad(item.cantidad)} x ${item.precio_unitario:.2f}"
        descuento = f" (-{item.descuento:g}%)" if item.descuento else ""
        for linea in _lineas_columnas(detalle, f"${item.subtotal:.2f}", descuento, ancho):
            lineas.append((linea, "izq"))

    lineas.append(("-" * ANCHO_PAPEL, "izq"))
    if venta.descuento_global or venta.recargo:
        lineas.extend((linea, "izq") for linea in
                      _lineas_columnas("SUBTOTAL", f"${venta.subtotal:.2f}", ancho=ancho))
    if venta.descuento_global:
        lineas.extend((linea, "izq") for linea in
                      _lineas_columnas(f"DESCUENTO {venta.descuento_global:g}%",
                                       f"-${venta.monto_descuento_global:.2f}", ancho=ancho))
    if venta.recargo:
        lineas.extend((linea, "izq") for linea in
                      _lineas_columnas(f"RECARGO {venta.recargo:g}%",
                                       f"+${venta.monto_recargo:.2f}", ancho=ancho))
    for alicuota, monto in _iva_por_alicuota(venta).items():
        lineas.extend((linea, "izq") for linea in
                      _lineas_columnas(f"IVA {alicuota:g}%", f"${monto:.2f}", ancho=ancho))
    lineas.extend((linea, "negrita") for linea in
                  _lineas_columnas("TOTAL", f"$ {venta.total:.2f}", ancho=ancho))
    if medio:
        lineas.extend((linea, "izq") for linea in
                      _lineas_columnas(f"PAGO: {medio}",
                                       f"$ {venta.total:.2f}", ancho=ancho))
    if vuelto > 0:
        lineas.extend((linea, "izq") for linea in
                      _lineas_columnas("SU PAGO", f"$ {monto_recibido:.2f}", ancho=ancho))
        lineas.extend((linea, "izq") for linea in
                      _lineas_columnas("VUELTO", f"$ {vuelto:.2f}", ancho=ancho))
    lineas += [("=" * ANCHO_PAPEL, "centro"),
               ("¡Gracias por su compra!", "centro"),
               ("Emitido con BetterStock Free", "centro")]
    return lineas
