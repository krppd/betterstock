
from __future__ import annotations

from collections.abc import Callable
from html import escape

from PyQt6 import QtCore, QtGui
from PyQt6.QtPrintSupport import QPrinter

from models.comercio import Comercio
from models.venta import Venta
from services.ticket import _lineas_ticket


class ErrorImpresion(Exception):
    pass


def _impresora() -> QPrinter:
    impresora = QPrinter(QPrinter.PrinterMode.HighResolution)
    if not impresora.isValid():
        raise ErrorImpresion("No hay ninguna impresora configurada en el sistema.")
    return impresora


def _imprimir(html: str, pagina: Callable[[QPrinter], None] | None = None) -> None:
    impresora = _impresora()
    if pagina is not None:
        pagina(impresora)
    documento = QtGui.QTextDocument()
    documento.setHtml(html)
    documento.print(impresora)


def imprimir_ticket(venta: Venta, comercio: Comercio | None = None,
                    monto_recibido: float = 0.0, vuelto: float = 0.0,
                    identificador: str = "", medio_pago: str = "") -> None:
    from PyQt6 import QtGui
    impresora = _impresora()
    impresora.setPageSize(QtGui.QPageSize(QtCore.QSizeF(90, 200), QtGui.QPageSize.Unit.Millimeter))
    impresora.setPageMargins(QtCore.QMarginsF(5, 5, 5, 5), QtGui.QPageLayout.Unit.Millimeter)
    lineas = _lineas_ticket(venta, comercio, monto_recibido, vuelto, identificador, medio_pago)
    cuerpo = "".join(_html_linea(texto, estilo) for texto, estilo in lineas)
    html = ('<div style="font-family: monospace; font-size: 8pt; width: 100%;">'
            + cuerpo + "</div>")
    documento = QtGui.QTextDocument()
    documento.setHtml(html)
    documento.print(impresora)


def imprimir_codigo_anulacion(codigo: str, etiqueta: str = "") -> None:
    _imprimir(_html_codigo(codigo, etiqueta))


def _html_codigo(codigo: str, etiqueta: str) -> str:
    titulo = f"<p style='font-size: 14pt;'>{escape(etiqueta)}</p>" if etiqueta else ""
    return (
        "<div style='font-family: monospace; text-align: center;'>"
        + titulo
        + f"<p style='font-size: 44pt; font-weight: bold;'>{escape(codigo)}</p>"
        + "</div>"
    )


def _html_linea(texto: str, estilo: str) -> str:
    from html import escape
    separador = texto.strip()
    texto = escape(texto)
    if separador and set(separador) <= {"=", "-"}:
        if set(separador) == {"="}:
            return "<hr style='border-top: 1px solid black;'>"
        return "<hr style='border-top: 1px dotted black;'>"
    if estilo == "titulo":
        return f"<p style='text-align:center;'><b><span style='font-size:13pt;'>{texto}</span></b></p>"
    if estilo == "subtitulo":
        return f"<p style='text-align:center;'><b>{texto}</b></p>"
    if estilo == "negrita":
        return f"<p style='text-align:left;'><b>{texto}</b></p>"
    if estilo == "centro":
        return f"<p style='text-align:center;'>{texto}</p>"
    if texto.strip() == "TOTAL" or texto.startswith("TOTAL "):
        return f"<p style='text-align:center;'><b><span style='font-size:13pt;'>{texto}</span></b></p>"
    return f"<p style='text-align:left;'>{texto}</p>"
