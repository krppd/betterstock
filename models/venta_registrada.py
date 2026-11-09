from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime

from models import medio_pago
from models.entidad import Entidad
from models.venta import Venta
from utils.formato import cantidad_a_texto, diferencia as diferencia_montos
from utils.formato import redondear_cantidad

FORMATO_FECHA = "%d/%m/%Y"

PREFIJO_DETALLE_JSON = "J1:"
SEPARADOR_FILA = "|"
SEPARADOR_CAMPO = ";"
FORMATO_PRECIO_LEGADO = re.compile(r"^\d+\.\d{2}$")
CAMPOS_LEGADO = (4, 5, 6)
PREFIJO_PAGOS_JSON = "P1:"


@dataclass(frozen=True)
class RenglonVenta:
    codigo: str
    nombre: str
    cantidad: float
    precio_unitario: float
    alicuota_iva: float = 21.0
    descuento: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "cantidad", redondear_cantidad(self.cantidad))

    @property
    def subtotal(self) -> float:
        return self.precio_unitario * self.cantidad * (1 - self.descuento / 100)

    @property
    def iva(self) -> float:
        if not self.alicuota_iva:
            return 0.0
        return self.subtotal - self.subtotal / (1 + self.alicuota_iva / 100)


@dataclass(frozen=True)
class PagoVenta:
    medio: str
    importe: float
    datos: str = ""
    recibido: float = 0.0

    def __post_init__(self) -> None:
        medio = str(self.medio).strip()
        if not medio:
            raise ValueError("El pago no tiene medio de pago.")
        object.__setattr__(self, "medio", medio)
        importe = round(float(self.importe), 2)
        if importe <= 0:
            raise ValueError("El importe del pago debe ser mayor a 0.")
        object.__setattr__(self, "importe", importe)
        if medio == medio_pago.METODO_EFECTIVO:
            recibido = float(self.recibido or importe)
            if recibido < importe:
                raise ValueError("El efectivo recibido es menor al importe aplicado.")
        else:
            recibido = importe
        object.__setattr__(self, "recibido", round(recibido, 2))
        object.__setattr__(self, "datos", str(self.datos).strip())

    @property
    def vuelto(self) -> float:
        return round(float(diferencia_montos(self.recibido, self.importe)), 2)


def _serializar_pagos(pagos: tuple[PagoVenta, ...]) -> str:
    if not pagos:
        return ""
    datos = [
        {
            "medio": pago.medio,
            "importe": pago.importe,
            "datos": pago.datos,
            "recibido": pago.recibido,
        }
        for pago in pagos
    ]
    return PREFIJO_PAGOS_JSON + json.dumps(
        datos, ensure_ascii=False, separators=(",", ":")
    )


def leer_pagos(texto: str) -> tuple[PagoVenta, ...]:
    if not texto:
        return ()
    if not texto.startswith(PREFIJO_PAGOS_JSON):
        raise ValueError(f"Pagos con formato inválido: {texto!r}")
    try:
        datos = json.loads(texto[len(PREFIJO_PAGOS_JSON):])
    except json.JSONDecodeError as error:
        raise ValueError(f"Pagos con JSON inválido: {error}") from error
    if not isinstance(datos, list):
        raise ValueError("Pagos con JSON inválido: no es una lista de pagos.")
    try:
        return tuple(
            PagoVenta(
                medio=str(item.get("medio") or ""),
                importe=item.get("importe") or 0.0,
                datos=str(item.get("datos") or ""),
                recibido=item.get("recibido") or 0.0,
            )
            for item in datos
        )
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError(f"Pagos con JSON inválido: {error}") from error


def _numero(valor, defecto: float) -> float:
    if valor is None:
        return defecto
    try:
        return float(valor)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Detalle de venta con número inválido: {valor!r}") from error


def _cantidad_legada(texto: str) -> float | None:
    try:
        return redondear_cantidad(float(str(texto).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return None


def _cantidad(valor, defecto: float = 0.0) -> float:
    if valor is None:
        return defecto
    if isinstance(valor, bool):
        raise ValueError(f"Detalle de venta con cantidad inválida: {valor!r}")
    try:
        cantidad = float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError) as error:
        raise ValueError(f"Detalle de venta con cantidad inválida: {valor!r}") from error
    return redondear_cantidad(cantidad)


def _serializar_detalle(renglones) -> str:
    datos = [
        {
            "codigo": renglon.codigo,
            "nombre": renglon.nombre,
            "cantidad": cantidad_a_texto(renglon.cantidad),
            "precio_unitario": renglon.precio_unitario,
            "alicuota_iva": renglon.alicuota_iva,
            "descuento": renglon.descuento,
        }
        for renglon in renglones
    ]
    return PREFIJO_DETALLE_JSON + json.dumps(
        datos, ensure_ascii=False, separators=(",", ":")
    )


def _leer_detalle_json(texto: str) -> list[RenglonVenta]:
    try:
        datos = json.loads(texto[len(PREFIJO_DETALLE_JSON):])
    except json.JSONDecodeError as error:
        raise ValueError(f"Detalle de venta con JSON inválido: {error}") from error
    if not isinstance(datos, list):
        raise ValueError("Detalle de venta con JSON inválido: no es una lista de renglones.")
    renglones: list[RenglonVenta] = []
    for item in datos:
        if not isinstance(item, dict):
            raise ValueError("Detalle de venta con JSON inválido: renglón ilegible.")
        renglones.append(
            RenglonVenta(
                codigo=str(item.get("codigo") or ""),
                nombre=str(item.get("nombre") or ""),
                cantidad=_cantidad(item.get("cantidad"), 0.0),
                precio_unitario=_numero(item.get("precio_unitario"), 0.0),
                alicuota_iva=_numero(item.get("alicuota_iva"), 21.0),
                descuento=_numero(item.get("descuento"), 0.0),
            )
        )
    return renglones


def _interpretar_legado(campos: list[str], exigir_precio: bool):
    total = len(campos)
    for canonico in range(min(max(CAMPOS_LEGADO), total), min(CAMPOS_LEGADO) - 1, -1):
        fin_nombre = total - canonico + 2
        if fin_nombre < 2 or fin_nombre + 1 >= total:
            continue
        try:
            cantidad = _cantidad_legada(campos[fin_nombre])
        except ValueError:
            continue
        if cantidad is None:
            continue
        texto_precio = campos[fin_nombre + 1]
        if exigir_precio and not FORMATO_PRECIO_LEGADO.match(texto_precio):
            continue
        try:
            precio = float(texto_precio)
        except ValueError:
            continue
        alicuota = 21.0
        descuento = 0.0
        if canonico >= 5:
            if fin_nombre + 2 >= total:
                continue
            try:
                alicuota = float(campos[fin_nombre + 2])
            except ValueError:
                continue
        if canonico >= 6:
            if fin_nombre + 3 >= total:
                continue
            try:
                descuento = float(campos[fin_nombre + 3])
            except ValueError:
                continue
        nombre = SEPARADOR_CAMPO.join(campos[1:fin_nombre])
        return RenglonVenta(
            codigo=campos[0],
            nombre=nombre,
            cantidad=cantidad,
            precio_unitario=precio,
            alicuota_iva=alicuota,
            descuento=descuento,
        )
    return None


def _leer_renglon_legado(texto: str) -> RenglonVenta:
    campos = texto.split(SEPARADOR_CAMPO)
    if len(campos) < 4:
        raise ValueError(f"Detalle de venta inválido: {texto!r}")
    for exigir_precio in (True, False):
        renglon = _interpretar_legado(campos, exigir_precio)
        if renglon is not None:
            return renglon
    raise ValueError(f"Detalle de venta inválido: {texto!r}")


def _leer_detalle_legado(texto: str) -> list[RenglonVenta]:
    partes = [parte for parte in texto.split(SEPARADOR_FILA) if parte.strip()]
    renglones: list[RenglonVenta] = []
    indice = 0
    while indice < len(partes):
        renglon = None
        for alcance in range(0, 4):
            if indice + alcance >= len(partes):
                break
            unido = SEPARADOR_FILA.join(partes[indice:indice + alcance + 1])
            try:
                renglon = _leer_renglon_legado(unido)
            except ValueError:
                continue
            indice += alcance + 1
            break
        if renglon is None:
            raise ValueError(f"Detalle de venta inválido: {partes[indice]!r}")
        renglones.append(renglon)
    return renglones


def leer_detalle(texto: str) -> list[RenglonVenta]:
    if texto.startswith(PREFIJO_DETALLE_JSON):
        try:
            return _leer_detalle_json(texto)
        except ValueError as error_json:
            try:
                return _leer_detalle_legado(texto)
            except ValueError:
                raise error_json
    return _leer_detalle_legado(texto)


class VentaRegistrada(Entidad):
    COLUMNAS = ("fecha", "hora", "total", "detalle", "descuento_global", "recargo",
                "monto_recibido", "vuelto", "estado", "medio_pago", "datos_pago",
                "usuario", "cliente", "pagos")

    ESTADO_ACTIVA = "activa"
    ESTADO_ANULADA = "anulada"

    def __init__(self, fecha: date, hora: str, total: float, detalle: list[RenglonVenta],
                 descuento_global: float = 0.0, recargo: float = 0.0,
                 monto_recibido: float = 0.0, vuelto: float = 0.0,
                 estado: str = ESTADO_ACTIVA, medio_pago: str = "",
                 datos_pago: str = "", usuario: str = "", cliente: str = "",
                 pagos: tuple[PagoVenta, ...] = ()) -> None:
        self._fecha = fecha
        self._hora = hora
        self._total = total
        self._detalle = list(detalle)
        self._descuento_global = descuento_global
        self._recargo = recargo
        self._monto_recibido = monto_recibido
        self._vuelto = vuelto
        self._estado = estado
        self._medio_pago = medio_pago
        self._datos_pago = datos_pago
        self._usuario = usuario
        self._cliente = cliente.strip()
        self._pagos: tuple[PagoVenta, ...] = ()
        if pagos:
            self._pagos = tuple(pagos)
            self._aplicar_pagos()
        elif medio_pago:
            self._pagos = (PagoVenta(
                medio_pago, total, datos_pago, monto_recibido or total),)

    def _aplicar_pagos(self) -> None:
        if not self._pagos:
            return
        medios = {pago.medio for pago in self._pagos}
        self._medio_pago = (next(iter(medios)) if len(medios) == 1
                            else medio_pago.METODO_MIXTO)
        self._datos_pago = " + ".join(
            pago.datos for pago in self._pagos if pago.datos)
        efectivo = [
            pago for pago in self._pagos if pago.medio == medio_pago.METODO_EFECTIVO
        ]
        self._monto_recibido = round(sum(pago.recibido for pago in efectivo), 2)
        self._vuelto = round(sum(pago.vuelto for pago in efectivo), 2)

    @property
    def pagos(self) -> tuple[PagoVenta, ...]:
        return self._pagos

    @property
    def importe_fiado(self) -> float:
        return round(sum(
            pago.importe for pago in self._pagos
            if pago.medio == medio_pago.METODO_FIADO), 2)

    @property
    def cliente(self) -> str:
        return self._cliente

    @property
    def medio_pago(self) -> str:
        return self._medio_pago

    @property
    def datos_pago(self) -> str:
        return self._datos_pago

    @property
    def usuario(self) -> str:
        return self._usuario

    @property
    def medio_pago_texto(self) -> str:
        if len(self._pagos) > 1:
            return self.medios_texto
        return medio_pago.descripcion_de(self._medio_pago, self._datos_pago)

    @property
    def medios_texto(self) -> str:
        return " + ".join(
            medio_pago.descripcion_de(pago.medio, pago.datos)
            for pago in self._pagos
        )

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def anulada(self) -> bool:
        return self._estado == self.ESTADO_ANULADA

    def anular(self) -> None:
        self._estado = self.ESTADO_ANULADA

    @property
    def monto_recibido(self) -> float:
        return self._monto_recibido

    @property
    def vuelto(self) -> float:
        return self._vuelto

    @classmethod
    def desde_venta(cls, venta: Venta, fecha: date, momento: datetime,
                    monto_recibido: float = 0.0, medio_pago: str = "",
                    datos_pago: str = "", usuario: str = "", cliente: str = "",
                    pagos: tuple[PagoVenta, ...] = ()) -> VentaRegistrada:
        detalle = [
            RenglonVenta(item.codigo, item.nombre, item.cantidad, item.precio_unitario,
                         item.alicuota_iva, item.descuento)
            for item in venta.items
        ]
        total = venta.total
        if pagos:
            return cls(fecha, momento.strftime("%H:%M:%S"), total, detalle,
                       descuento_global=venta.descuento_global, recargo=venta.recargo,
                       usuario=usuario, cliente=cliente, pagos=tuple(pagos))
        if not monto_recibido:
            monto_recibido = total
        return cls(fecha, momento.strftime("%H:%M:%S"), total, detalle,
                   descuento_global=venta.descuento_global, recargo=venta.recargo,
                   monto_recibido=monto_recibido,
                   vuelto=float(diferencia_montos(monto_recibido, total)),
                   medio_pago=medio_pago, datos_pago=datos_pago, usuario=usuario,
                   cliente=cliente)

    @property
    def fecha(self) -> date:
        return self._fecha

    @property
    def hora(self) -> str:
        return self._hora

    @property
    def total(self) -> float:
        return self._total

    @property
    def detalle(self) -> list[RenglonVenta]:
        return list(self._detalle)

    @property
    def unidades(self) -> float:
        return redondear_cantidad(sum(renglon.cantidad for renglon in self._detalle))

    @property
    def descuento_global(self) -> float:
        return self._descuento_global

    @property
    def recargo(self) -> float:
        return self._recargo

    @property
    def subtotal_detalle(self) -> float:
        return sum(renglon.subtotal for renglon in self._detalle)

    @property
    def iva_detalle(self) -> float:
        return sum(renglon.iva for renglon in self._detalle)

    @property
    def monto_descuento_global(self) -> float:
        return self.subtotal_detalle * self._descuento_global / 100

    @property
    def monto_recargo(self) -> float:
        return (self.subtotal_detalle - self.monto_descuento_global) * self._recargo / 100

    @property
    def alicuota_promedio(self) -> float:
        base = self.subtotal_detalle - self.iva_detalle
        if base <= 0:
            return 0.0
        return self.iva_detalle / base * 100

    @property
    def factor_total(self) -> float:
        if self.subtotal_detalle <= 0:
            return 1.0
        return self.total / self.subtotal_detalle

    @property
    def iva_total(self) -> float:
        return self.iva_detalle * self.factor_total

    @property
    def identificador(self) -> str:
        return f"{self._fecha.isoformat()} {self._hora}"

    @property
    def fecha_texto(self) -> str:
        return self._fecha.strftime(FORMATO_FECHA)

    def to_dict(self) -> dict[str, str]:
        detalle = _serializar_detalle(self._detalle)
        return {
            "fecha": self.fecha_texto,
            "hora": self._hora,
            "total": f"{self._total:.2f}",
            "detalle": detalle,
            "descuento_global": f"{self._descuento_global:g}",
            "recargo": f"{self._recargo:g}",
            "monto_recibido": f"{self._monto_recibido:.2f}",
            "vuelto": f"{self._vuelto:.2f}",
            "estado": self._estado,
            "medio_pago": self._medio_pago,
            "datos_pago": self._datos_pago,
            "usuario": self._usuario,
            "cliente": self._cliente,
            "pagos": _serializar_pagos(self._pagos),
        }

    @classmethod
    def from_dict(cls, datos: dict[str, str]) -> VentaRegistrada:
        fecha = datetime.strptime(datos.get("fecha") or "", FORMATO_FECHA).date()
        detalle = leer_detalle(datos.get("detalle") or "")
        return cls(
            fecha, datos.get("hora") or "", float(datos.get("total") or 0), detalle,
            descuento_global=float(datos.get("descuento_global") or 0),
            recargo=float(datos.get("recargo") or 0),
            monto_recibido=float(datos.get("monto_recibido") or 0),
            vuelto=float(datos.get("vuelto") or 0),
            estado=datos.get("estado") or cls.ESTADO_ACTIVA,
            medio_pago=datos.get("medio_pago") or "",
            datos_pago=datos.get("datos_pago") or "",
            usuario=datos.get("usuario") or "",
            cliente=datos.get("cliente") or "",
            pagos=leer_pagos(datos.get("pagos") or ""),
        )