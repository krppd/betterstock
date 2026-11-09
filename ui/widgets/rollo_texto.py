from __future__ import annotations

from itertools import zip_longest

from PyQt6.QtCore import QEasingCurve
from PyQt6.QtGui import QFontMetrics, QPainter


class RolloTexto:
    TIEMPO_CARACTER_MS = 160

    ESCALON_MS = 20

    def __init__(self, texto: str = "", tiempo_caracter: int = TIEMPO_CARACTER_MS,
                 escalon: int = ESCALON_MS, rodar_todo: bool = False,
                 direccion: str = "down") -> None:
        self._base = texto
        self._objetivo = texto
        self._tiempo_caracter = tiempo_caracter
        self._escalon = escalon
        self._rodar_todo = rodar_todo
        self._direccion = direccion
        self._curva = QEasingCurve(QEasingCurve.Type.OutCubic)

    @property
    def objetivo(self) -> str:
        return self._objetivo

    @property
    def direccion(self) -> str:
        return self._direccion

    @direccion.setter
    def direccion(self, valor: str) -> None:
        self._direccion = valor

    def fijar(self, texto: str) -> None:
        self._base = texto
        self._objetivo = texto

    def mostrar(self, texto: str, direccion: str | None = None) -> bool:
        if direccion is not None:
            self._direccion = direccion
        if texto == self._objetivo:
            return False
        self._base = self._objetivo
        self._objetivo = texto
        return True

    def terminar(self) -> None:
        self._base = self._objetivo

    def pares(self) -> list[tuple[str | None, str | None, bool]]:
        base, objetivo = self._base, self._objetivo
        prefijo = 0
        while (prefijo < len(base) and prefijo < len(objetivo)
               and base[prefijo] == objetivo[prefijo]):
            prefijo += 1
        resto_base, resto_objetivo = base[prefijo:], objetivo[prefijo:]
        sufijo = 0
        while (sufijo < len(resto_base) and sufijo < len(resto_objetivo)
               and resto_base[-1 - sufijo] == resto_objetivo[-1 - sufijo]):
            sufijo += 1
        medio_base = resto_base[:len(resto_base) - sufijo] if sufijo else resto_base
        medio_objetivo = resto_objetivo[:len(resto_objetivo) - sufijo] if sufijo else resto_objetivo
        pares = [(letra, letra, self._rodar_todo) for letra in base[:prefijo]]
        pares += [(viejo, nuevo, self._rodar_todo or viejo != nuevo)
                  for viejo, nuevo in zip_longest(medio_base[::-1], medio_objetivo[::-1])][::-1]
        if sufijo:
            pares += [(letra, letra, self._rodar_todo)
                      for letra in objetivo[len(objetivo) - sufijo:]]
        return pares

    def demoras(self, pares: list[tuple[str | None, str | None, bool]]) -> list[int]:
        demoras, cuenta = [], 0
        for _, _, rueda in pares:
            demoras.append(cuenta * self._escalon)
            if rueda:
                cuenta += 1
        return demoras

    def duracion_total(self) -> int:
        pares = self.pares()
        if not pares:
            return 0
        return self._tiempo_caracter + max(self.demoras(pares))

    @staticmethod
    def ancho_celda(metricas: QFontMetrics, par: tuple[str | None, str | None, bool]) -> int:
        return max([metricas.horizontalAdvance(c) for c in par[:2] if c is not None] or [0])

    def ancho_bloque(self, metricas: QFontMetrics) -> int:
        return sum(self.ancho_celda(metricas, par) for par in self.pares())

    def dibujar(self, pintor: QPainter, metricas: QFontMetrics,
                x: int, base_y: int, altura: int, transcurrido: int | None) -> None:
        pares = self.pares()
        demoras = self.demoras(pares)
        for (viejo, nuevo, rueda), demora in zip(pares, demoras):
            if transcurrido is None or not rueda:
                texto = nuevo if nuevo is not None else viejo
                if texto is not None:
                    pintor.drawText(x, base_y, texto)
            else:
                self._dibujar_par(pintor, x, base_y, altura, viejo, nuevo,
                                  self._progreso(demora, transcurrido))
            x += self.ancho_celda(metricas, (viejo, nuevo, rueda))

    def _dibujar_par(self, pintor: QPainter, x: int, base_y: int, altura: int,
                     viejo: str | None, nuevo: str | None, progreso: float) -> None:
        avance = self._curva.valueForProgress(progreso)
        if self._direccion == "up":
            if viejo is None:
                pintor.drawText(x, round(base_y + altura * (1 - avance)), nuevo)
            elif nuevo is None:
                pintor.drawText(x, round(base_y - altura * avance), viejo)
            else:
                pintor.drawText(x, round(base_y - altura * avance), viejo)
                pintor.drawText(x, round(base_y + altura * (1 - avance)), nuevo)
        else:
            if viejo is None:
                pintor.drawText(x, round(base_y - altura * (1 - avance)), nuevo)
            elif nuevo is None:
                pintor.drawText(x, round(base_y + altura * avance), viejo)
            else:
                pintor.drawText(x, round(base_y + altura * avance), viejo)
                pintor.drawText(x, round(base_y - altura * (1 - avance)), nuevo)

    def _progreso(self, demora: int, transcurrido: int) -> float:
        local = (transcurrido - demora) / self._tiempo_caracter
        return max(0.0, min(1.0, local))
