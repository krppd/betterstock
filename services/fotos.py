from __future__ import annotations

import io
import json
import re
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


from config import RECURSOS_DIR

DIR_FOTOS = RECURSOS_DIR / "productos"
MAX_RESULTADOS = 6
MAX_BYTES = 5 * 1024 * 1024
LADO_MAXIMO = 800
TIMEOUT_SEGUNDOS = 15
AGENTE = "Mozilla/5.0 (X11; Linux x86_64) BetterStock/1.0"


class ErrorFoto(Exception):
    pass


@dataclass(frozen=True)
class Candidata:
    titulo: str
    url_miniatura: str
    url_completa: str


class ProveedorFotos(ABC):
    @abstractmethod
    def buscar(self, texto: str) -> list[Candidata]:
        ...


class ProveedorOpenFoodFacts(ProveedorFotos):
    URL_BASE = "https://world.openfoodfacts.org"

    def buscar(self, texto: str) -> list[Candidata]:
        texto = texto.strip()
        if not texto:
            return []
        if texto.isdigit() and len(texto) >= 8:
            exacta = self._por_codigo(texto)
            if exacta is not None:
                return [exacta]
        return self._por_nombre(texto)[:MAX_RESULTADOS]

    def _por_codigo(self, codigo: str) -> Candidata | None:
        try:
            datos = self._leer_json(f"{self.URL_BASE}/api/v0/product/{codigo}.json")
        except ErrorFoto:
            return None
        producto = datos.get("product") or {}
        imagen = producto.get("image_url") or ""
        if datos.get("status") != 1 or not imagen:
            return None
        return Candidata(
            titulo=producto.get("product_name") or codigo,
            url_miniatura=producto.get("image_small_url") or imagen,
            url_completa=imagen,
        )

    def _por_nombre(self, texto: str) -> list[Candidata]:
        parametros = urllib.parse.urlencode({
            "query": texto,
            "page_size": MAX_RESULTADOS,
            "fields": "code,product_name,image_url,image_small_url",
        })
        try:
            datos = self._leer_json(f"{self.URL_BASE}/api/v2/search?{parametros}")
        except ErrorFoto:
            return []
        candidatas = []
        for producto in datos.get("products") or []:
            imagen = producto.get("image_url") or ""
            if not imagen:
                continue
            candidatas.append(Candidata(
                titulo=producto.get("product_name") or producto.get("code") or texto,
                url_miniatura=producto.get("image_small_url") or imagen,
                url_completa=imagen,
            ))
        return candidatas

    def _leer_json(self, url: str) -> dict:
        try:
            datos = descargar_bytes(url)
        except ErrorFoto as error:
            raise error
        try:
            valor = json.loads(datos.decode("utf-8"))
        except ValueError as error:
            raise ErrorFoto(f"Respuesta inválida del servidor: {error}")
        if not isinstance(valor, dict):
            raise ErrorFoto("Respuesta inválida del servidor.")
        return valor


def descargar_bytes(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() not in ("http", "https", "file"):
        raise ErrorFoto("Esquema de URL no permitido.")
    try:
        pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
        with urllib.request.urlopen(pedido, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            tipo = ""
            encabezados = getattr(respuesta, "headers", None)
            if encabezados is not None:
                tipo = encabezados.get_content_type()
            if tipo and tipo not in ("image/jpeg", "image/png", "image/gif",
                                     "image/webp", "application/octet-stream"):
                raise ErrorFoto(f"La URL no trae una imagen ({tipo}).")
            datos = respuesta.read(MAX_BYTES + 1)
    except ErrorFoto:
        raise
    except Exception as error:
        raise ErrorFoto(f"No se pudo descargar la imagen: {error}")
    if len(datos) > MAX_BYTES:
        raise ErrorFoto("La imagen es muy pesada (más de 5 MB).")
    if not datos:
        raise ErrorFoto("La URL no trajo nada.")
    return datos


def nombre_archivo(codigo: str) -> str:
    seguro = re.sub(r"[^A-Za-z0-9_-]+", "_", codigo).strip("_")
    return (seguro or "producto") + ".png"


EXTENSIONES_FOTO = (".png", ".jpg", ".jpeg")


def ruta_foto(codigo: str, destino: Path | None = None) -> str:
    carpeta = destino if destino is not None else DIR_FOTOS
    for extension in EXTENSIONES_FOTO:
        candidata = carpeta / f"{codigo}{extension}"
        if candidata.is_file():
            return str(candidata)
    return ""


def guardar_bytes(datos: bytes, codigo: str, destino: Path | None = None) -> Path:
    try:
        imagen = Image.open(io.BytesIO(datos))
        imagen.verify()
        imagen = Image.open(io.BytesIO(datos)).convert("RGB")
    except Exception:
        raise ErrorFoto("El archivo no es una imagen válida.")
    imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
    destino = destino if destino is not None else DIR_FOTOS
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / nombre_archivo(codigo)
    imagen.save(ruta, format="PNG")
    return ruta


def descargar_foto(url: str, codigo: str, destino: Path | None = None) -> Path:
    return guardar_bytes(descargar_bytes(url), codigo, destino)
