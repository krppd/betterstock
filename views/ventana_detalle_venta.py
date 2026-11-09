from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import QDialog, QHeaderView

from models.medio_pago import descripcion_de, es_efectivo
from models.venta_registrada import RenglonVenta, VentaRegistrada
from services.devoluciones import registrar_devolucion
from services.excepciones import ErrorNegocio
from services.gestor_anulaciones import (
    MENSAJE_SIN_SERVICIO,
    GestorAnulaciones,
    servicio_actual,
)
from ui.estilos import escala
from ui.manual.detalle_venta_ui import Ui_DetalleVentaForm
from ui.widgets.notificacion import Notificacion
from utils.formato import formatear_cantidad, formatear_dinero
from views.dialogo_anulacion import DialogoAnulacion
from views.dialogo_devolucion import DialogoDevolucion
from views.ventana_base import VentanaBase

YA_ANULADA = "Esta venta ya está anulada."
LARGO_MEDIOS = 48


def _acotar(texto: str, largo: int = LARGO_MEDIOS) -> str:
    return texto if len(texto) <= largo else texto[:largo - 3] + "..."


def _pagos_con_importe(venta: VentaRegistrada) -> str:
    """Cada medio con su importe: 'Efectivo $1.000,00 + Transferencia $1.500,00'."""
    return " + ".join(
        f"{descripcion_de(pago.medio, pago.datos)} {formatear_dinero(pago.importe)}"
        for pago in venta.pagos)


class VentanaDetalleVenta(QDialog, VentanaBase):
    def __init__(self, venta: VentaRegistrada, parent=None,
                 gestor_anulaciones: GestorAnulaciones | None = None) -> None:
        super().__init__(parent)
        self._venta = venta
        self._gestor_anulaciones = gestor_anulaciones or servicio_actual()
        self.ui = Ui_DetalleVentaForm()
        self.ui.setupUi(self)
        self._acomodar_escala()
        self.ui.btnCerrar.clicked.connect(self.accept)
        self.ui.btnAnular.clicked.connect(self.anular_venta)
        self.ui.btnDevolucion.clicked.connect(self.devolucion_parcial)
        self.llenar()
        self._actualizar_boton_anular()
        self._actualizar_boton_devolucion()

    def _acomodar_escala(self) -> None:
        encabezado = self.ui.tblDetalle.horizontalHeader()
        encabezado.setStretchLastSection(False)
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        valor = escala()
        self._escala = valor
        self._alto_fila = round(34 * valor)
        for tabla in (self.ui.tblDetalle, self.ui.tblDatos):
            tabla.verticalHeader().setDefaultSectionSize(self._alto_fila)
        if valor == 1.0:
            return
        disponible = self.screen().availableGeometry().height() if self.screen() else 0
        alto = round(550 * valor)
        if disponible:
            alto = min(alto, disponible - 40)
        self.setMinimumSize(round(720 * valor), alto)
        self.ui.tblDetalle.horizontalHeader().setDefaultSectionSize(round(90 * valor))
        self.ui.tblDatos.horizontalHeader().setDefaultSectionSize(round(130 * valor))
        self.ui.tblDatos.setFixedHeight(round(160 * valor))

    def llenar(self) -> None:
        self._mostrar_cabecera()
        self._cargar_renglones()
        self._mostrar_resumen()
        self._cargar_datos_pago()

    def _mostrar_cabecera(self) -> None:
        venta = self._venta
        self.ui.lblCabecera.setText(
            f"Venta del {venta.fecha_texto} a las {venta.hora}"
            + (" — ANULADA" if venta.anulada else ""))

    def _cargar_renglones(self) -> None:
        filas = [self._armar_fila(renglon) for renglon in self._venta.detalle]
        self.llenar_tabla(self.ui.tblDetalle, filas)

    @staticmethod
    def _armar_fila(renglon: RenglonVenta) -> list[str]:
        nombre = renglon.nombre
        if renglon.descuento:
            nombre += f"  (-{renglon.descuento:g}%)"
        return [
            renglon.codigo,
            nombre,
            formatear_cantidad(renglon.cantidad),
            formatear_dinero(renglon.precio_unitario),
            formatear_dinero(renglon.subtotal),
            formatear_dinero(renglon.iva),
        ]

    def _mostrar_resumen(self) -> None:
        self.ui.lblResumen.setText("\n".join(self._lineas_del_resumen()))

    def _lineas_del_resumen(self) -> list[str]:
        venta = self._venta
        ajustada = bool(venta.descuento_global or venta.recargo)
        lineas = [
            f"Subtotal con descuentos: {formatear_dinero(venta.subtotal_detalle)}",
        ]
        if venta.descuento_global:
            lineas.append(
                f"Descuento total ({venta.descuento_global:g}%): "
                f"- {formatear_dinero(venta.monto_descuento_global)}")
        if venta.recargo:
            lineas.append(
                f"Recargo ({venta.recargo:g}%): "
                f"+ {formatear_dinero(venta.monto_recargo)}")
        alicuota = venta.alicuota_promedio
        lineas.append(f"IVA ({alicuota:g}% promedio): {formatear_dinero(venta.iva_total)}")
        if not ajustada:
            lineas.append(f"Total: {formatear_dinero(venta.total)}")
        return lineas

    def _cargar_datos_pago(self) -> None:
        venta = self._venta
        mixta = len(venta.pagos) > 1
        detalle = [
            ("Medio de pago", _acotar(_pagos_con_importe(venta)) if mixta
             else venta.medio_pago_texto),
            ("Referencia", venta.datos_pago or "—"),
            ("Cobró", venta.usuario or "—"),
            ("Unidades", formatear_cantidad(venta.unidades)),
            ("Total", formatear_dinero(venta.total)),
        ]
        if not mixta and (es_efectivo(venta.medio_pago) or venta.monto_recibido):
            detalle.append(("Recibido", formatear_dinero(venta.monto_recibido)))
            detalle.append(("Vuelto", formatear_dinero(venta.vuelto)))
        tabla = self.ui.tblDatos
        self.llenar_tabla(tabla, [[clave, valor] for clave, valor in detalle])
        tabla.setFixedHeight(self._alto_fila * (tabla.rowCount() + 1)
                             + round(4 * self._escala))

    def _actualizar_boton_anular(self) -> None:
        boton = self.ui.btnAnular
        if self._venta.anulada:
            boton.setEnabled(False)
            boton.setToolTip(YA_ANULADA)
            return
        if self._gestor_anulaciones is None:
            boton.setEnabled(False)
            boton.setToolTip(MENSAJE_SIN_SERVICIO)
            return
        bloqueo = self._gestor_anulaciones.motivo_bloqueo(self._venta)
        if bloqueo:
            boton.setEnabled(False)
            boton.setToolTip(bloqueo)
            return
        boton.setEnabled(True)
        boton.setToolTip("Anular la venta con el código del supervisor.")

    def anular_venta(self) -> None:
        if self._gestor_anulaciones is None:
            self.mostrar_advertencia("Anular venta", MENSAJE_SIN_SERVICIO)
            return
        if self._venta.anulada:
            self.mostrar_advertencia("Anular venta", YA_ANULADA)
            return
        bloqueo = self._gestor_anulaciones.motivo_bloqueo(self._venta)
        if bloqueo:
            self.mostrar_advertencia("Anular venta", bloqueo)
            return
        dialogo = DialogoAnulacion(
            self, f"Venta del {self._venta.fecha_texto} a las {self._venta.hora} "
                  f"por {formatear_dinero(self._venta.total)}",
            validar_codigo=self._gestor_anulaciones.codigo_valido)
        if dialogo.exec() != DialogoAnulacion.DialogCode.Accepted:
            return
        codigo, motivo = dialogo.resultado
        try:
            etiqueta = self._gestor_anulaciones.anular_con_codigo(
                self._venta.identificador, date.today(), codigo, motivo)
        except ErrorNegocio as error:
            self.mostrar_advertencia("Anular venta", str(error))
            return
        self._venta.anular()
        self._mostrar_cabecera()
        self._actualizar_boton_anular()
        self._actualizar_boton_devolucion()
        faltantes = self._gestor_anulaciones.ultimos_faltantes
        if faltantes:
            self.mostrar_advertencia(
                "Anulada con faltantes",
                "La venta quedó anulada, pero estos productos ya no existen "
                f"y su stock no volvió: {', '.join(faltantes)}.")
        supervisor = f" (supervisor: {etiqueta})" if etiqueta else ""
        Notificacion(self).mostrar(
            "Venta anulada",
            f"Motivo: {motivo}{supervisor}")

    def _actualizar_boton_devolucion(self) -> None:
        boton = self.ui.btnDevolucion
        if self._venta.anulada:
            boton.setEnabled(False)
            boton.setToolTip(YA_ANULADA)
            return
        boton.setEnabled(True)
        boton.setToolTip("Devolver ítems de la venta sin anular el ticket completo.")

    def devolucion_parcial(self) -> None:
        if self._venta.anulada:
            self.mostrar_advertencia("Devolución parcial", YA_ANULADA)
            return
        base = None
        validar_codigo = None
        if self._gestor_anulaciones is not None:
            validar_codigo = self._gestor_anulaciones.codigo_valido
            if hasattr(self._gestor_anulaciones, "_codigos") and hasattr(
                self._gestor_anulaciones._codigos, "ruta_archivo"
            ):
                base = self._gestor_anulaciones._codigos.ruta_archivo

        dialogo = DialogoDevolucion(
            self, self._venta, validar_codigo=validar_codigo, base=base
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            dev = registrar_devolucion(
                self._venta.identificador,
                dialogo.items_a_devolver,
                usuario=self._venta.usuario or "vendedor",
                motivo=dialogo.motivo,
                base=base,
            )
        except ErrorNegocio as error:
            self.mostrar_advertencia("Devolución parcial", str(error))
            return
        Notificacion(self).mostrar(
            "Devolución parcial registrada",
            f"Se devolvieron {formatear_dinero(dev.total)} en mercadería.",
        )

