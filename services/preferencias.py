from __future__ import annotations

import json
from pathlib import Path

from config import DATA_DIR

ARCHIVO_PREFERENCIAS: Path = DATA_DIR / "preferencias.json"
CLAVE_MODO_TACTIL = "modo_tactil"
CLAVE_MODO_OSCURO = "modo_oscuro"
CLAVE_MOSTRAR_RELOJ = "mostrar_reloj"
CLAVE_POSICION_MENU = "posicion_menu"
CLAVE_FOTOS_EN_LINEA = "fotos_en_linea"
POSICION_IZQUIERDA = "izquierda"
POSICION_DERECHA = "derecha"
ESCALA_NORMAL = 1.0
ESCALA_TACTIL = 1.5


def _ruta(ruta: Path | None = None) -> Path:
    return Path(ruta) if ruta is not None else ARCHIVO_PREFERENCIAS


def leer(ruta: Path | None = None) -> dict:
    try:
        datos = json.loads(_ruta(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return datos if isinstance(datos, dict) else {}


def guardar(datos: dict, ruta: Path | None = None) -> bool:
    destino = _ruta(ruta)
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    except OSError:
        return False
    return True


def modo_tactil(ruta: Path | None = None) -> bool:
    return bool(leer(ruta).get(CLAVE_MODO_TACTIL, False))


def guardar_modo_tactil(activo: bool, ruta: Path | None = None) -> bool:
    datos = leer(ruta)
    datos[CLAVE_MODO_TACTIL] = bool(activo)
    return guardar(datos, ruta)


def modo_oscuro(ruta: Path | None = None) -> bool:
    return bool(leer(ruta).get(CLAVE_MODO_OSCURO, False))


def guardar_modo_oscuro(activo: bool, ruta: Path | None = None) -> bool:
    datos = leer(ruta)
    datos[CLAVE_MODO_OSCURO] = bool(activo)
    return guardar(datos, ruta)


def mostrar_reloj(ruta: Path | None = None) -> bool:
    return bool(leer(ruta).get(CLAVE_MOSTRAR_RELOJ, True))


def guardar_mostrar_reloj(activo: bool, ruta: Path | None = None) -> bool:
    datos = leer(ruta)
    datos[CLAVE_MOSTRAR_RELOJ] = bool(activo)
    return guardar(datos, ruta)


def fotos_en_linea(ruta: Path | None = None) -> bool:
    return bool(leer(ruta).get(CLAVE_FOTOS_EN_LINEA, False))


def guardar_fotos_en_linea(activo: bool, ruta: Path | None = None) -> bool:
    datos = leer(ruta)
    datos[CLAVE_FOTOS_EN_LINEA] = bool(activo)
    return guardar(datos, ruta)


def escala_modo_tactil(ruta: Path | None = None) -> float:
    return ESCALA_TACTIL if modo_tactil(ruta) else ESCALA_NORMAL


def posicion_menu(ruta: Path | None = None) -> str:
    valor = str(leer(ruta).get(CLAVE_POSICION_MENU, POSICION_IZQUIERDA))
    return POSICION_DERECHA if valor == POSICION_DERECHA else POSICION_IZQUIERDA


def guardar_posicion_menu(posicion: str, ruta: Path | None = None) -> bool:
    datos = leer(ruta)
    datos[CLAVE_POSICION_MENU] = POSICION_DERECHA if posicion == POSICION_DERECHA else POSICION_IZQUIERDA
    return guardar(datos, ruta)


def _recortar(valor, maximo: float) -> float:
    """Lee un número de un JSON que puede haber editado cualquiera: basura a 0."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return 0.0
    if numero != numero:
        return 0.0
    return round(min(max(numero, 0.0), maximo), 2)


def _validar(valor, maximo: float, etiqueta: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{etiqueta} no es un número válido.") from None
    if not 0 <= numero <= maximo:
        raise ValueError(f"{etiqueta} tiene que estar entre 0 y {maximo:g}.")
    return round(numero, 2)
