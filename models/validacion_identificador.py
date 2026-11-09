from __future__ import annotations

import re

RE_CUIT = re.compile(r"^(\d{2})-?(\d{8})-?(\d)$")
PESOS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def _digito_verificador(primeros_diez: str) -> int:
    suma = sum(int(digito) * peso for digito, peso in zip(primeros_diez, PESOS))
    resto = 11 - (suma % 11)
    if resto == 11:
        return 0
    if resto == 10:
        return 9
    return resto


def normalizar_cuit(valor: str) -> str:
    valor = valor.strip()
    encontrado = RE_CUIT.match(valor)
    if not encontrado:
        return valor
    inicio, cuerpo, fin = encontrado.groups()
    return f"{inicio}-{cuerpo}-{fin}"


def es_cuit_valido(valor: str) -> bool:
    encontrado = RE_CUIT.match(valor.strip())
    if not encontrado:
        return False
    primeros_diez = encontrado.group(1) + encontrado.group(2)
    return int(encontrado.group(3)) == _digito_verificador(primeros_diez)


PREFIXOS_PERSONA = {"20", "23", "24", "27", "33", "34"}


def tipo_de_identificador(valor: str) -> str:
    if not es_cuit_valido(valor):
        return ""
    inicio = RE_CUIT.match(valor.strip()).group(1)
    if inicio in PREFIXOS_PERSONA:
        return "persona"
    return "sociedad"