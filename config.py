from __future__ import annotations

import os
from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent
"""Carpeta raíz del proyecto (sólo lectura en instalaciones)."""

RECURSOS_DIR: Path = BASE_DIR / "Recursos"
"""Carpeta de imágenes y del archivo de recursos de Qt (sólo lectura)."""

APP_VERSION: str = "1.0.2"
"""Versión de la app."""

ALERTAS_EN_AVISO_STOCK: int = 5
"""Cuántos productos críticos se listan en el aviso de stock bajo al iniciar."""

DIAS_AVISO_VENCIMIENTO: int = 30
"""Con cuántos días de anticipación se avisa que un producto está por vencer."""


def _directorio_datos() -> Path:
    """Carpeta escribible para datos del usuario.

    Prioridad: BETTERSTOCK_HOME / BETTERSTOCK_DATA_DIR, luego AppData por plataforma.
    """
    override = os.environ.get("BETTERSTOCK_DATA_DIR") or os.environ.get("BETTERSTOCK_HOME")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "BetterStock"
        return Path.home() / "AppData" / "Roaming" / "BetterStock"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "BetterStock"
    return Path.home() / ".local" / "share" / "BetterStock"


DATA_DIR: Path = _directorio_datos()
OUTPUT_DIR: Path = DATA_DIR / "output"

