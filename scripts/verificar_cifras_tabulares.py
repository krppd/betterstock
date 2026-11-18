from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QApplication, QTableWidget

from repositories.categoria_repositorio import CategoriaRepositorio
from repositories.movimiento_repositorio import MovimientoRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from services.gestor_stock import GestorStock
from ui.estilos import ROLES, TAG_TABULAR, TAMANO_DISPLAY, aplicar_tema, fuente
from ui.widgets.etiqueta_rodante import EtiquetaRodante
from views.ventana_base import VentanaBase

DIGITOS = "0123456789"


def _anchos(fuente_texto: QFont) -> list[int]:
    metricas = QFontMetrics(fuente_texto)
    return [metricas.horizontalAdvance(digito) for digito in DIGITOS]


def main() -> int:
    aplicacion = QApplication(sys.argv[:1])
    aplicar_tema(aplicacion)
    problemas: list[str] = []

    print("anchos por digito (proporcional vs tabular)")
    for nombre, (punto, _, _) in ROLES.items():
        normal = fuente(punto)
        tabular = fuente(punto, tabular=True)
        if not tabular.isFeatureSet(QFont.Tag(TAG_TABULAR)):
            problemas.append(f"la fuente {nombre} no tiene la feature {TAG_TABULAR}")
        anchos_normal = _anchos(normal)
        anchos_tabular = _anchos(tabular)
        print(f"  {nombre} ({punto}pt) proporcional={anchos_normal} tabular={anchos_tabular}")
        if len(set(anchos_tabular)) != 1:
            problemas.append(f"la fuente tabular de {nombre} no tiene digitos de ancho fijo")
        if len(set(anchos_normal)) == 1:
            problemas.append(f"la fuente proporcional de {nombre} ya era de ancho fijo")

    print("cifras con ancho fijo")
    tabular = fuente(13, tabular=True)
    metricas = QFontMetrics(tabular)
    print(f"  '1111' mide {metricas.horizontalAdvance('1111')}px")
    print(f"  '8888' mide {metricas.horizontalAdvance('8888')}px")
    if metricas.horizontalAdvance("1111") != metricas.horizontalAdvance("8888"):
        problemas.append("los digitos no tienen el mismo ancho")

    with tempfile.TemporaryDirectory() as temporal:
        base = Path(temporal) / "cifras.db"
        stock = GestorStock(
            ProductoRepositorio(base),
            MovimientoRepositorio(base),
            CategoriaRepositorio(base),
        )
        stock.inicializar()
        tabla = QTableWidget(1, 2)
        VentanaBase.llenar_tabla(tabla, [["1001", "$ 1.450,00"]])
        fuente_celda = tabla.item(0, 1).font()
        fuente_codigo = tabla.item(0, 0).font()
        if not fuente_celda.isFeatureSet(QFont.Tag(TAG_TABULAR)):
            problemas.append("la celda con importe no tiene cifras tabulares")
        if not fuente_codigo.isFeatureSet(QFont.Tag(TAG_TABULAR)):
            problemas.append("la celda con codigo no tiene cifras tabulares")
        print(f"  celda con importe: {fuente_celda.pointSize()}pt tabular="
              f"{fuente_celda.isFeatureSet(QFont.Tag(TAG_TABULAR))}")
        print(f"  celda con codigo: {fuente_codigo.pointSize()}pt tabular="
              f"{fuente_codigo.isFeatureSet(QFont.Tag(TAG_TABULAR))}")

        etiqueta = EtiquetaRodante()
        etiqueta.setFont(fuente(TAMANO_DISPLAY, negrita=True, tabular=True))
        etiqueta.setText("$ 1.450,00")
        etiqueta.show()
        aplicacion.processEvents()
        metricas_widget = QFontMetrics(etiqueta.font())
        if not etiqueta.font().isFeatureSet(QFont.Tag(TAG_TABULAR)):
            problemas.append("la EtiquetaRodante no tiene cifras tabulares")
        if metricas_widget.horizontalAdvance("1") != metricas_widget.horizontalAdvance("8"):
            problemas.append("la EtiquetaRodante mide con una fuente sin digitos de ancho fijo")
        print(f"  EtiquetaRodante: {etiqueta.font().pointSize()}pt tabular="
              f"{etiqueta.font().isFeatureSet(QFont.Tag(TAG_TABULAR))} "
              f"'1'={metricas_widget.horizontalAdvance('1')}px "
              f"'8'={metricas_widget.horizontalAdvance('8')}px")

    if problemas:
        print("PROBLEMAS:")
        for problema in problemas:
            print(f"  - {problema}")
        return 1
    print("OK: las cifras tabulares funcionan")
    return 0


if __name__ == "__main__":
    # El teardown de Qt se cuelga con un segment fault: se sale sin limpiar.
    codigo = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(codigo)
