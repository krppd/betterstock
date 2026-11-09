from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from datetime import date

LARGO_CODIGO = 10
BYTES_SALT = 16
ITERACIONES = 100_000
ALGORITMO = "sha256"
FORMATO_FECHA = "%d/%m/%Y"


def generar_codigo() -> str:
    return f"{secrets.randbelow(10 ** LARGO_CODIGO):0{LARGO_CODIGO}d}"


def generar_salt() -> str:
    return secrets.token_hex(BYTES_SALT)


def hashear_codigo(codigo: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        ALGORITMO, codigo.encode(), bytes.fromhex(salt), ITERACIONES
    ).hex()


@dataclass
class CodigoAnulacion:
    identificador: int
    etiqueta: str = ""
    hash_codigo: str = ""
    salt: str = ""
    creado: date = field(default_factory=date.today)
    activo: bool = True

    @property
    def fecha_texto(self) -> str:
        return self.creado.strftime(FORMATO_FECHA)

    @property
    def estado_texto(self) -> str:
        return "Activo" if self.activo else "Inactivo"

    def verificar(self, codigo: str) -> bool:
        if not self.activo:
            return False
        if not codigo or not self.hash_codigo or not self.salt:
            return False
        try:
            sal = bytes.fromhex(self.salt)
        except ValueError:
            return False
        calculado = hashlib.pbkdf2_hmac(
            ALGORITMO, codigo.encode(), sal, ITERACIONES
        ).hex()
        return hmac.compare_digest(calculado, self.hash_codigo)
