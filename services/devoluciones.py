from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from config import DATA_DIR
from models.movimiento import MOTIVO_DEVOLUCION_PREFIJO, MovimientoEntrada
from models.venta_registrada import leer_detalle
from repositories.codigo_repositorio import CodigoRepositorio
from repositories.sqlite import conectar, ruta_db
from services.excepciones import ErrorValidacion


@dataclass
class ItemDevolucion:
    codigo_producto: str
    cantidad: float
    precio_unitario: float
    subtotal: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "codigo_producto": self.codigo_producto,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal,
        }


@dataclass
class Devolucion:
    id: int | None
    venta_id: int
    fecha: str
    hora: str
    usuario: str
    total: float
    anulada: bool
    motivo: str
    items: list[ItemDevolucion] = field(default_factory=list)

    def __int__(self) -> int:
        return self.id or 0


def _resolver_venta_fila(conexion, venta_id: int | str):
    texto = str(venta_id).strip()
    if texto.isdigit():
        fila = conexion.execute(
            "SELECT id, total, detalle, estado FROM ventas WHERE id = ?",
            (int(texto),),
        ).fetchone()
        if fila is not None:
            return fila
    if " " in texto:
        fecha_iso, _, hora = texto.partition(" ")
        fila = conexion.execute(
            "SELECT id, total, detalle, estado FROM ventas WHERE fecha = ? AND hora = ? ORDER BY id LIMIT 1",
            (fecha_iso, hora),
        ).fetchone()
        if fila is not None:
            return fila
    return None


def cantidades_devueltas(
    venta_id: int | str,
    base: str | Path | None = None,
    conexion=None,
) -> dict[str, float]:
    """Suma las cantidades ya devueltas por producto para una venta activa."""
    propia = False
    if conexion is None:
        conexion = conectar(ruta_db(base or DATA_DIR))
        propia = True
    try:
        fila = _resolver_venta_fila(conexion, venta_id)
        if fila is None:
            return {}
        filas = conexion.execute(
            """
            SELECT di.codigo_producto, SUM(di.cantidad) as total_devuelto
            FROM devolucion_items di
            JOIN devoluciones d ON d.id = di.devolucion_id
            WHERE d.venta_id = ? AND d.anulada = 0
            GROUP BY di.codigo_producto
            """,
            (int(fila["id"]),),
        ).fetchall()
        return {
            str(f["codigo_producto"]): float(f["total_devuelto"])
            for f in filas
        }
    finally:
        if propia:
            conexion.close()


def _normalizar_item(
    item: Any,
    vendidos: dict[str, float],
    precios: dict[str, float],
) -> tuple[str, float, float, float]:
    if isinstance(item, dict):
        codigo = str(item.get("codigo_producto") or item.get("codigo") or "").strip()
        cantidad = float(item.get("cantidad", 0))
        precio = item.get("precio_unitario")
    elif isinstance(item, (tuple, list)):
        codigo = str(item[0]).strip()
        cantidad = float(item[1])
        precio = item[2] if len(item) > 2 else None
    else:
        codigo = str(getattr(item, "codigo_producto", getattr(item, "codigo", ""))).strip()
        cantidad = float(getattr(item, "cantidad", 0))
        precio = getattr(item, "precio_unitario", None)

    if not codigo:
        raise ErrorValidacion("El ítem a devolver no tiene código de producto.")
    if precio is None:
        precio = precios.get(codigo, 0.0)
    precio = float(precio)
    subtotal = round(cantidad * precio, 2)
    return codigo, cantidad, precio, subtotal


def registrar_devolucion(
    venta_id: int | str,
    items: list[Any] | dict[str, float],
    usuario: str = "",
    motivo: str = "",
    base: str | Path | None = None,
    fecha: date | str | None = None,
    hora: str | None = None,
) -> Devolucion:
    """Registra una devolución parcial de una venta en UNA sola transacción.

    Restituye stock con movimientos 'Entrada' y motivo 'Devolución venta <id>'.
    La venta original queda intacta.
    """
    motivo_limpio = (motivo or "").strip()
    if not motivo_limpio:
        raise ErrorValidacion("El motivo de la devolución es obligatorio.")

    if isinstance(items, dict):
        items = [{"codigo_producto": k, "cantidad": v} for k, v in items.items()]
    if not items:
        raise ErrorValidacion("No se indicaron ítems para devolver.")

    conexion = conectar(ruta_db(base or DATA_DIR))
    try:
        with conexion:
            venta_fila = _resolver_venta_fila(conexion, venta_id)
            if venta_fila is None:
                raise ErrorValidacion(f"No se encontró la venta {venta_id}.")
            if str(venta_fila["estado"]).strip().lower() == "anulada":
                raise ErrorValidacion("No se puede devolver una venta anulada.")

            id_numerico_venta = int(venta_fila["id"])
            renglones = leer_detalle(venta_fila["detalle"])
            vendidos: dict[str, float] = {}
            precios: dict[str, float] = {}
            for renglon in renglones:
                vendidos[renglon.codigo] = vendidos.get(renglon.codigo, 0.0) + renglon.cantidad
                if renglon.codigo not in precios:
                    precios[renglon.codigo] = (
                        round(renglon.subtotal / renglon.cantidad, 2)
                        if renglon.cantidad
                        else renglon.precio_unitario
                    )

            devueltos = cantidades_devueltas(id_numerico_venta, conexion=conexion)

            items_procesados: list[ItemDevolucion] = []
            for item_crudo in items:
                codigo, cantidad, precio, subtotal = _normalizar_item(
                    item_crudo, vendidos, precios
                )
                if codigo not in vendidos:
                    raise ErrorValidacion(
                        f"El artículo '{codigo}' no pertenece a la venta {venta_id}."
                    )
                if cantidad <= 0:
                    raise ErrorValidacion("La cantidad a devolver debe ser mayor a 0.")

                disponible = round(vendidos[codigo] - devueltos.get(codigo, 0.0), 4)
                if cantidad > disponible:
                    raise ErrorValidacion(
                        f"No se puede devolver más cantidad de la vendida para el producto '{codigo}'."
                    )

                devueltos[codigo] = devueltos.get(codigo, 0.0) + cantidad
                items_procesados.append(
                    ItemDevolucion(
                        codigo_producto=codigo,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal,
                    )
                )

            total_devolucion = round(sum(i.subtotal for i in items_procesados), 2)
            fecha_iso = (
                fecha.strftime("%Y-%m-%d")
                if isinstance(fecha, date)
                else (fecha or date.today().strftime("%Y-%m-%d"))
            )
            hora_str = hora or datetime.now().strftime("%H:%M:%S")

            cursor_dev = conexion.execute(
                """
                INSERT INTO devoluciones(venta_id, fecha, hora, usuario, total, anulada, motivo)
                VALUES (?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    id_numerico_venta,
                    fecha_iso,
                    hora_str,
                    usuario or "",
                    total_devolucion,
                    motivo_limpio,
                ),
            )
            devolucion_id = cursor_dev.lastrowid

            for item in items_procesados:
                conexion.execute(
                    """
                    INSERT INTO devolucion_items(devolucion_id, codigo_producto, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        devolucion_id,
                        item.codigo_producto,
                        item.cantidad,
                        item.precio_unitario,
                        item.subtotal,
                    ),
                )
                conexion.execute(
                    "UPDATE productos SET stock_actual = stock_actual + ? WHERE codigo = ?",
                    (item.cantidad, item.codigo_producto),
                )
                texto_motivo_mov = (
                    f"{MOTIVO_DEVOLUCION_PREFIJO} {venta_id}: {motivo_limpio}"
                    if motivo_limpio
                    else f"{MOTIVO_DEVOLUCION_PREFIJO} {venta_id}"
                )
                conexion.execute(
                    """
                    INSERT INTO movimientos(fecha, codigo_producto, tipo, cantidad, motivo)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        fecha_iso,
                        item.codigo_producto,
                        MovimientoEntrada.TIPO,
                        item.cantidad,
                        texto_motivo_mov,
                    ),
                )

        return Devolucion(
            id=devolucion_id,
            venta_id=id_numerico_venta,
            fecha=fecha_iso,
            hora=hora_str,
            usuario=usuario or "",
            total=total_devolucion,
            anulada=False,
            motivo=motivo_limpio,
            items=items_procesados,
        )
    finally:
        conexion.close()


def registrar_con_codigo(
    venta_id: int | str,
    items: list[Any] | dict[str, float],
    usuario: str,
    motivo: str,
    codigo: str,
    base: str | Path | None = None,
    codigos: CodigoRepositorio | None = None,
) -> Devolucion:
    """Valida el código de supervisor antes de registrar la devolución."""
    if codigos is None:
        codigos = CodigoRepositorio(ruta_db(base or DATA_DIR))
    encontrado = codigos.buscar_activo_por_codigo((codigo or "").strip())
    if encontrado is None:
        raise ErrorValidacion("El código no es válido.")
    return registrar_devolucion(
        venta_id,
        items,
        usuario=usuario,
        motivo=motivo,
        base=base,
    )


class ServicioDevoluciones:
    def __init__(
        self,
        base: str | Path | None = None,
        codigos: CodigoRepositorio | None = None,
    ) -> None:
        self._base = base
        self._codigos = codigos or CodigoRepositorio(ruta_db(base or DATA_DIR))

    def registrar_devolucion(
        self,
        venta_id: int | str,
        items: list[Any] | dict[str, float],
        usuario: str = "",
        motivo: str = "",
    ) -> Devolucion:
        return registrar_devolucion(
            venta_id, items, usuario=usuario, motivo=motivo, base=self._base
        )

    def registrar_con_codigo(
        self,
        venta_id: int | str,
        items: list[Any] | dict[str, float],
        usuario: str,
        motivo: str,
        codigo: str,
    ) -> Devolucion:
        return registrar_con_codigo(
            venta_id,
            items,
            usuario=usuario,
            motivo=motivo,
            codigo=codigo,
            base=self._base,
            codigos=self._codigos,
        )

    def codigo_valido(self, codigo: str) -> bool:
        return self._codigos.buscar_activo_por_codigo((codigo or "").strip()) is not None

    def cantidades_devueltas(self, venta_id: int | str) -> dict[str, float]:
        return cantidades_devueltas(venta_id, base=self._base)
