#!/usr/bin/env python3
"""Regenera ``ui/generated/`` desde los ``.ui`` conservando el código escrito a mano.

Cada ``.ui`` de ``ui/designer/`` se vuelve a compilar con ``pyuic6`` y después se
vuelve a poner lo que ``pyuic6`` no sabe generar. Eso son dos cosas:

1. Los imports de widgets propios (``from ui.widgets... import ...``), que se
   detectan comparando los imports del archivo anterior con los del nuevo.
2. Los bloques de código escritos a mano, que van marcados en el archivo con
   ``# --- INICIO CODIGO MANUAL ---`` y ``# --- FIN CODIGO MANUAL ---``.

Según la indentación del marcador, el bloque va en un lugar u otro:

- ocho espacios: dentro de ``setupUi``, justo después de ``connectSlotsByName``.
- cuatro espacios: a nivel de clase, antes de ``retranslateUi``.
- cero espacios: a nivel de módulo, al final del archivo.

El ``pyuic6`` que se usa es el del entorno activo, así que tiene que ser el del
``requirements.txt`` (6.11.0). Para generarlo con otra versión:

    /ruta/al/venv/bin/python scripts/regenerar_ui.py

La conversión de los widgets de Qt a los de Fluent está escrita a mano en los
archivos de ``ui/generated/`` y los ``.ui`` siguen siendo de Qt plano, así que
``pyuic6`` no la reproduce. Un archivo que use clases de Fluent que el
``pyuic6`` no genera no se toca: el script lo avisa y sigue con el siguiente.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DISEÑO = RAIZ / "ui" / "designer"
GENERADOS = RAIZ / "ui" / "generated"
PYUIC = "pyuic6"

INICIO = "# --- INICIO CODIGO MANUAL ---"
FIN = "# --- FIN CODIGO MANUAL ---"


def _generar(origen: Path, destino: Path) -> str:
    relativo = origen.relative_to(RAIZ)
    subprocess.run([PYUIC, str(relativo), "-o", str(destino)], check=True, cwd=RAIZ)
    return destino.read_text(encoding="utf-8")


def _bloques_manuales(codigo: str) -> list[tuple[int, str]]:
    """Devuelve (indentación, contenido con marcadores) de cada bloque marcado."""
    bloques: list[tuple[int, str]] = []
    lineas = codigo.splitlines()
    indice = 0
    while indice < len(lineas):
        linea = lineas[indice]
        if linea.strip() != INICIO:
            indice += 1
            continue
        indentacion = len(linea) - len(linea.lstrip())
        fin = indice + 1
        while fin < len(lineas) and lineas[fin].strip() != FIN:
            fin += 1
        contenido = "\n".join(lineas[indice : fin + 1])
        bloques.append((indentacion, contenido))
        indice = fin + 1
    return bloques


def _imports(codigo: str) -> list[str]:
    return [
        linea
        for linea in codigo.splitlines()
        if linea.startswith(("import ", "from ")) and "PyQt6" not in linea
    ]


def _clases_fluent(codigo: str) -> list[str]:
    """Clases de qfluentwidgets que importa el archivo."""
    try:
        arbol = ast.parse(codigo)
    except SyntaxError:
        return []
    nombres = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and (nodo.module or "").split(".")[0] == "qfluentwidgets":
            for alias in nodo.names:
                nombres.append(alias.asname or alias.name)
    return nombres


def _usa(codigo: str, nombre: str) -> bool:
    return re.search(rf"\b{re.escape(nombre)}\b", codigo) is not None


def _adaptado_a_fluent(anterior: str, nuevo: str) -> list[str]:
    """Clases de Fluent que el archivo viejo usa y el nuevo no trae.

    Los archivos de `ui/generated/` se adaptaron a mano a Fluent después de
    generarlos: el `.ui` sigue siendo de Qt plano, así que `pyuic6` no
    reproduce esa conversión. Si al regenerar desaparecen esas clases, el
    archivo viejo es el bueno y el nuevo dejaría la ventana sin Fluent.
    """
    return [
        nombre
        for nombre in _clases_fluent(anterior)
        if _usa(anterior, nombre) and not _usa(nuevo, nombre)
    ]


def _preservar(anterior: str, nuevo: str) -> str:
    lineas = nuevo.splitlines()

    imports_previos = _imports(anterior)
    imports_nuevos = set(_imports(nuevo))
    faltantes = [linea for linea in imports_previos if linea not in imports_nuevos]

    imports_propios = [
        linea
        for linea in _imports(nuevo)
        if linea.startswith(("from ui.", "import Recursos"))
    ]
    for linea in imports_propios:
        lineas.remove(linea)
    while lineas and not lineas[-1].strip():
        lineas.pop()

    if faltantes or imports_propios:
        ultimo = max(
            indice
            for indice, linea in enumerate(lineas)
            if linea.startswith(("import ", "from "))
        )
        extras = [linea for linea in imports_previos if linea not in imports_nuevos]
        extras = [linea for linea in extras if linea not in imports_propios] + imports_propios
        lineas = lineas[: ultimo + 1] + extras + lineas[ultimo + 1 :]

    bloques = _bloques_manuales(anterior)
    if not bloques:
        return "\n".join(lineas) + "\n"

    dentro = [texto for indentacion, texto in bloques if indentacion >= 8]
    en_clase = [texto for indentacion, texto in bloques if indentacion == 4]
    en_modulo = [texto for indentacion, texto in bloques if indentacion == 0]

    if dentro:
        ancla = None
        for indice, linea in enumerate(lineas):
            if "QtCore.QMetaObject.connectSlotsByName" in linea:
                ancla = indice
        if ancla is None:
            raise SystemExit("No se encontró connectSlotsByName para insertar el bloque manual.")
        lineas = lineas[: ancla + 1] + dentro + lineas[ancla + 1 :]

    if en_clase:
        ancla = None
        for indice, linea in enumerate(lineas):
            if linea.startswith("    def retranslateUi"):
                ancla = indice
                break
        if ancla is None:
            raise SystemExit("No se encontró retranslateUi para insertar el bloque manual.")
        lineas = lineas[:ancla] + en_clase + [""] + lineas[ancla:]

    if en_modulo:
        while lineas and not lineas[-1].strip():
            lineas.pop()
        lineas += [""] + en_modulo

    return "\n".join(lineas) + "\n"


def main() -> int:
    global PYUIC
    if len(sys.argv) > 1:
        PYUIC = str(Path(sys.argv[1]) / "pyuic6")
    if not GENERADOS.is_dir():
        print(f"No existe {GENERADOS}")
        return 1
    for origen in sorted(DISEÑO.glob("*.ui")):
        destino = GENERADOS / f"{origen.stem}_ui.py"
        if not destino.exists():
            print(f"[nuevo] {origen.name}")
            _generar(origen, destino)
            continue
        anterior = destino.read_text(encoding="utf-8")
        temporal = destino.with_suffix(".tmp")
        nuevo = _generar(origen, temporal)
        temporal.unlink()
        perdidos = _adaptado_a_fluent(anterior, nuevo)
        if perdidos:
            print(f"[sin tocar] {destino.name}: usa {', '.join(perdidos)} de Fluent, "
                  "que pyuic6 no genera; actualizalo a mano")
            continue
        final = _preservar(anterior, nuevo)
        manual_viejo = len(_bloques_manuales(anterior))
        manual_nuevo = len(_bloques_manuales(final))
        if manual_viejo != manual_nuevo:
            print(f"[AVISO] {destino.name}: se perdieron bloques manuales")
            return 1
        if final != anterior:
            destino.write_text(final, encoding="utf-8")
            print(f"[actualizado] {destino.name}")
        else:
            print(f"[sin cambios] {destino.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
