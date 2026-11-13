#!/usr/bin/env python3
"""Corre todas las verificaciones del proyecto: los tests y los scripts de control visual."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VERIFICADORES = (
    "scripts/verificar_texto.py",
    "scripts/verificar_contraste.py",
    "scripts/verificar_cifras_tabulares.py",
)


def _ejecutar(etiqueta: str, comando: list[str]) -> bool:
    print(f"\n=== {etiqueta}", flush=True)
    resultado = subprocess.run(
        comando,
        cwd=RAIZ,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
    )
    return resultado.returncode == 0


def main() -> int:
    fallos = []
    if not _ejecutar("Tests", [sys.executable, "-m", "pytest", "tests/", "-q"]):
        fallos.append("tests")
    for script in VERIFICADORES:
        if not _ejecutar(script, [sys.executable, script]):
            fallos.append(script)
    print()
    if fallos:
        print("FALLARON: " + ", ".join(fallos))
        return 1
    print("TODO OK: tests y verificaciones visuales")
    return 0


if __name__ == "__main__":
    sys.exit(main())
