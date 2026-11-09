from PyQt6.QtCore import QResource

from config import RECURSOS_DIR

QResource.registerResource(str(RECURSOS_DIR / "recursos.rcc"))
