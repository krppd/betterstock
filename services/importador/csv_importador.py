from __future__ import annotations

import csv
import io
from pathlib import Path

from services.importador.deteccion import (
    coincidir_columnas,
    detectar_codificacion,
    detectar_delimitador,
    normalizar,
    parsear_precio,
)
from services.importador.modelo import (
    ColumnaDetectada,
    Deteccion,
    FilaMapeada,
    Mapeo,
    MODO_IGNORAR,
    MODO_PRECIOS,
    MODO_STOCK,
    PRECIO_CON_IVA,
    PRECIO_COSTO,
    FACTOR_IVA,
)
from services.importador.secciones import detectar_secciones, recortar_vacias

MUESTRA_EJEMPLOS = 3

_ETIQUETAS: dict[str, str] = {
    "precio_venta": "el precio de venta",
    "precio_costo": "el precio de costo",
}


class ImportadorCSV:

    def detectar(self, ruta: str | Path) -> Deteccion:
        ruta = Path(ruta)
        codificacion = detectar_codificacion(ruta)
        texto = self._leer(ruta, codificacion)
        delimitador = detectar_delimitador(texto)
        filas = self._filas(texto, delimitador)
        secciones = detectar_secciones(filas)
        encabezados = self._encabezados(filas, secciones)
        columnas = self._columnas(filas, encabezados)
        return Deteccion(
            ruta=str(ruta),
            delimitador=delimitador,
            codificacion=codificacion,
            encabezados=encabezados,
            filas=filas,
            secciones=secciones,
            columnas=columnas,
            mapeo=coincidir_columnas(encabezados),
        )

    def parsear(
        self,
        ruta: str | Path,
        mapeo: Mapeo,
        secciones: list | None = None,
        deteccion: Deteccion | None = None,
    ) -> list[FilaMapeada]:
        if deteccion is None:
            deteccion = self.detectar(ruta)
        bloques = list(secciones) if secciones is not None else deteccion.secciones
        filas = deteccion.filas
        resultado: list[FilaMapeada] = []
        for indice, seccion in enumerate(bloques):
            modo = mapeo.secciones.get(indice, seccion.tipo_sugerido)
            if modo in (MODO_IGNORAR, MODO_STOCK):
                continue
            if modo == MODO_PRECIOS:
                resultado.extend(self._filas_de_precios(filas, seccion, mapeo, deteccion))
            else:
                resultado.extend(self._filas_de_catalogo(filas, seccion, mapeo, deteccion))
        return resultado

    def _filas_de_catalogo(
        self,
        filas: list[list[str]],
        seccion,
        mapeo: Mapeo,
        deteccion: Deteccion,
    ) -> list[FilaMapeada]:
        columnas = self._columnas_de_seccion(seccion, mapeo, deteccion)
        resultado: list[FilaMapeada] = []
        for indice in seccion.filas:
            fila = filas[indice]
            valores: dict[str, str] = {}
            for campo, columna in columnas.items():
                valores[campo] = fila[columna].strip() if columna < len(fila) else ""
            mapeada = FilaMapeada(
                numero=indice + 1,
                indice=indice,
                seccion=seccion.titulo,
                valores=valores,
            )
            if "nombre" not in columnas:
                mapeada.errores.append("No se indicó la columna del nombre del producto.")
            self._interpretar_precios(mapeada, mapeo, columnas)
            resultado.append(mapeada)
        return resultado

    def _filas_de_precios(
        self,
        filas: list[list[str]],
        seccion,
        mapeo: Mapeo,
        deteccion: Deteccion,
    ) -> list[FilaMapeada]:
        propias = coincidir_columnas(seccion.cabeceras) if seccion.cabeceras else {}
        columna_codigo = propias.get("codigo", mapeo.columnas.get("codigo"))
        if columna_codigo is None:
            return []
        destino, columna_precio = self._destino_de_precio(propias, mapeo)
        if columna_precio is None:
            return []
        resultado: list[FilaMapeada] = []
        for indice in seccion.filas:
            fila = filas[indice]
            codigo = fila[columna_codigo].strip() if columna_codigo < len(fila) else ""
            if not codigo:
                continue
            texto = fila[columna_precio].strip() if columna_precio < len(fila) else ""
            if not texto:
                continue
            mapeada = FilaMapeada(
                numero=indice + 1,
                indice=indice,
                seccion=seccion.titulo,
                valores={"codigo": codigo, destino: texto},
            )
            self._interpretar_precios(mapeada, mapeo, {destino: columna_precio})
            resultado.append(mapeada)
        return resultado

    def _destino_de_precio(
        self,
        propias: dict[str, int],
        mapeo: Mapeo,
    ) -> tuple[str, int | None]:
        destino = "precio_venta"
        columna: int | None = None
        if "precio_venta" in propias:
            columna = propias["precio_venta"]
        elif "precio_costo" in propias:
            destino, columna = "precio_costo", propias["precio_costo"]
        elif "precio_venta" in mapeo.columnas:
            columna = mapeo.columnas["precio_venta"]
        elif "precio_costo" in mapeo.columnas:
            destino, columna = "precio_costo", mapeo.columnas["precio_costo"]
        else:
            return destino, None
        if mapeo.tipo_precio == PRECIO_COSTO:
            destino = "precio_costo"
        return destino, columna

    def _interpretar_precios(
        self,
        mapeada: FilaMapeada,
        mapeo: Mapeo,
        columnas: dict[str, int],
    ) -> None:
        valores = mapeada.valores
        if (
            mapeo.tipo_precio == PRECIO_COSTO
            and "precio_venta" in valores
            and "precio_costo" not in columnas
        ):
            valores["precio_costo"] = valores.pop("precio_venta")
        for campo in ("precio_venta", "precio_costo"):
            if campo not in valores:
                continue
            texto = valores[campo]
            if not texto:
                valores.pop(campo)
                continue
            valor = parsear_precio(texto)
            if valor is None:
                mapeada.errores.append(
                    f"{_ETIQUETAS[campo].capitalize()} no es un monto válido: '{texto}'.")
                valores.pop(campo)
                continue
            if valor < 0:
                mapeada.avisos.append(
                    f"{_ETIQUETAS[campo].capitalize()} era negativo; se importó como 0.")
                valor = 0.0
            if mapeo.tipo_precio == PRECIO_CON_IVA:
                valor = valor / FACTOR_IVA
            mapeada.precios[campo] = valor

    def _columnas_de_seccion(
        self,
        seccion,
        mapeo: Mapeo,
        deteccion: Deteccion,
    ) -> dict[str, int]:
        if not seccion.cabeceras:
            return dict(mapeo.columnas)
        if seccion.cabeceras == deteccion.encabezados:
            return dict(mapeo.columnas)
        propias = coincidir_columnas(seccion.cabeceras)
        nombres = [normalizar(cabecera) for cabecera in seccion.cabeceras]
        resultado = dict(propias)
        for campo, indice in mapeo.columnas.items():
            if indice >= len(deteccion.encabezados):
                continue
            nombre = normalizar(deteccion.encabezados[indice])
            if nombre in nombres:
                resultado[campo] = nombres.index(nombre)
        return resultado

    def _leer(self, ruta: Path, codificacion: str) -> str:
        try:
            return ruta.read_text(encoding=codificacion, errors="replace")
        except OSError:
            return ""

    def _filas(self, texto: str, delimitador: str) -> list[list[str]]:
        limpio = str(texto or "").replace("\x00", "")
        try:
            lector = csv.reader(io.StringIO(limpio), delimiter=delimitador)
            return [[str(celda or "").strip() for celda in fila] for fila in lector]
        except csv.Error:
            return []

    def _encabezados(self, filas: list[list[str]], secciones: list) -> list[str]:
        for seccion in secciones:
            if seccion.cabeceras:
                return list(seccion.cabeceras)
        if filas:
            return recortar_vacias(filas[0])
        return []

    def _columnas(self, filas: list[list[str]], encabezados: list[str]) -> list[ColumnaDetectada]:
        columnas: list[ColumnaDetectada] = []
        for indice, nombre in enumerate(encabezados):
            ejemplos: list[str] = []
            for fila in filas:
                if indice >= len(fila):
                    continue
                valor = fila[indice]
                if valor and len(ejemplos) < MUESTRA_EJEMPLOS:
                    ejemplos.append(valor)
            columnas.append(ColumnaDetectada(
                nombre=nombre or f"Columna {indice + 1}",
                indice=indice,
                ejemplos=ejemplos,
            ))
        return columnas
