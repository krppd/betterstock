from __future__ import annotations

import csv
import math
import unicodedata
from pathlib import Path

from services.importador.alias import ALIAS, CAMPOS

DELIMITADORES: tuple[str, ...] = (",", ";", "\t", "|")
LINEAS_MUESTRA: int = 30


def normalizar(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", str(texto or ""))
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c)).casefold()
    return "".join(c for c in sin_acentos if c.isalnum())


def detectar_delimitador(muestra: str) -> str:
    lineas = [
        linea for linea in str(muestra or "").splitlines()
        if linea.strip()
    ][:LINEAS_MUESTRA]
    if not lineas:
        return ","
    mejor = DELIMITADORES[0]
    mejor_puntaje = (0, 0, 0.0)
    for delimitador in DELIMITADORES:
        try:
            filas = list(csv.reader(lineas, delimiter=delimitador))
        except csv.Error:
            continue
        conteos = [len(fila) for fila in filas if len(fila) > 1]
        if not conteos:
            continue
        moda = max(set(conteos), key=conteos.count)
        puntaje = (len(conteos), moda, conteos.count(moda) / len(conteos))
        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor = delimitador
    return mejor


def detectar_codificacion(ruta: str | Path) -> str:
    datos = Path(ruta).read_bytes()
    if datos.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        datos.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    if any(0x80 <= byte <= 0x9F for byte in datos):
        return "cp1252"
    return "latin-1"


def coincidir_columnas(cabeceras: list[str]) -> dict[str, int]:
    normalizados = [normalizar(cabecera) for cabecera in cabeceras]
    alias_por_campo = {
        campo: {normalizar(alias) for alias in ALIAS[campo]} for campo in CAMPOS
    }
    usados: set[int] = set()
    resultado: dict[str, int] = {}

    for campo in CAMPOS:
        for indice, valor in enumerate(normalizados):
            if indice in usados or not valor:
                continue
            if valor in alias_por_campo[campo]:
                resultado[campo] = indice
                usados.add(indice)
                break

    candidatos: list[tuple[int, int, int, str]] = []
    for campo in CAMPOS:
        for indice, valor in enumerate(normalizados):
            if indice in usados or not valor:
                continue
            for alias in alias_por_campo[campo]:
                if len(alias) < 3 or len(valor) < 3:
                    continue
                if alias in valor or valor in alias:
                    candidatos.append((len(alias), CAMPOS.index(campo), indice, campo))
                    break

    candidatos.sort(key=lambda candidato: (-candidato[0], candidato[1], candidato[2]))
    for _, _, indice, campo in candidatos:
        if campo in resultado or indice in usados:
            continue
        resultado[campo] = indice
        usados.add(indice)

    return resultado


def parsear_precio(texto: str) -> float | None:
    limpio = str(texto or "").strip()
    if not limpio:
        return None
    limpio = (
        limpio.replace("$", "")
        .replace("€", "")
        .replace(" ", "")
        .replace(" ", "")
        .replace("\t", "")
    )
    if limpio.endswith("%"):
        limpio = limpio[:-1]
    negativo = limpio.startswith("-")
    if negativo or limpio.startswith("+"):
        limpio = limpio[1:]
    if "," in limpio and "." in limpio:
        if limpio.rfind(",") > limpio.rfind("."):
            limpio = limpio.replace(".", "").replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
    elif "," in limpio:
        limpio = _separador_unico(limpio, ",")
    elif "." in limpio:
        limpio = _separador_unico(limpio, ".")
    try:
        valor = float(limpio)
    except ValueError:
        return None
    if not math.isfinite(valor):
        return None
    return -valor if negativo else valor


def _separador_unico(texto: str, separador: str) -> str:
    if texto.count(separador) > 1:
        return texto.replace(separador, "")
    entero, _, decimales = texto.partition(separador)
    if len(decimales) == 3 and entero:
        return entero + decimales
    return entero + "." + decimales
