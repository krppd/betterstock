from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from ui.tema import color


class PuenteTarjetas(QObject):
    ventasValorChanged = pyqtSignal()
    ventasVariacionChanged = pyqtSignal()
    ventasColorChanged = pyqtSignal()
    unidadesValorChanged = pyqtSignal()
    unidadesVariacionChanged = pyqtSignal()
    unidadesColorChanged = pyqtSignal()
    totalValorChanged = pyqtSignal()
    totalVariacionChanged = pyqtSignal()
    totalColorChanged = pyqtSignal()
    ticketValorChanged = pyqtSignal()
    ticketVariacionChanged = pyqtSignal()
    ticketColorChanged = pyqtSignal()
    serieVentasChanged = pyqtSignal()
    serieUnidadesChanged = pyqtSignal()
    serieFacturadoChanged = pyqtSignal()
    serieTicketChanged = pyqtSignal()
    ventasTendenciaChanged = pyqtSignal()
    unidadesTendenciaChanged = pyqtSignal()
    totalTendenciaChanged = pyqtSignal()
    ticketTendenciaChanged = pyqtSignal()
    ventasDetalleChanged = pyqtSignal()
    unidadesDetalleChanged = pyqtSignal()
    totalDetalleChanged = pyqtSignal()
    ticketDetalleChanged = pyqtSignal()
    periodoDescripcionChanged = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._ventas_valor = "0"
        self._ventas_variacion = "—"
        self._ventas_color = color("texto_suave")
        self._unidades_valor = "0"
        self._unidades_variacion = "—"
        self._unidades_color = color("texto_suave")
        self._total_valor = "$ 0,00"
        self._total_variacion = "—"
        self._total_color = color("texto_suave")
        self._ticket_valor = "$ 0,00"
        self._ticket_variacion = "—"
        self._ticket_color = color("texto_suave")
        self._serie_ventas: list = []
        self._serie_unidades: list = []
        self._serie_facturado: list = []
        self._serie_ticket: list = []
        self._ventas_tendencia = 0
        self._unidades_tendencia = 0
        self._total_tendencia = 0
        self._ticket_tendencia = 0
        self._ventas_detalle: dict = {}
        self._unidades_detalle: dict = {}
        self._total_detalle: dict = {}
        self._ticket_detalle: dict = {}
        self._periodo_descripcion = ""

    def _fijar(self, nombre: str, senal: pyqtSignal, nuevo) -> None:
        if getattr(self, nombre) != nuevo:
            setattr(self, nombre, nuevo)
            senal.emit()

    @pyqtProperty(str, notify=ventasValorChanged)
    def ventasValor(self) -> str:
        return self._ventas_valor

    @ventasValor.setter
    def ventasValor(self, valor: str) -> None:
        self._fijar("_ventas_valor", self.ventasValorChanged, valor)

    @pyqtProperty(str, notify=ventasVariacionChanged)
    def ventasVariacion(self) -> str:
        return self._ventas_variacion

    @ventasVariacion.setter
    def ventasVariacion(self, valor: str) -> None:
        self._fijar("_ventas_variacion", self.ventasVariacionChanged, valor)

    @pyqtProperty(str, notify=ventasColorChanged)
    def ventasColor(self) -> str:
        return self._ventas_color

    @ventasColor.setter
    def ventasColor(self, valor: str) -> None:
        self._fijar("_ventas_color", self.ventasColorChanged, valor)

    @pyqtProperty(str, notify=unidadesValorChanged)
    def unidadesValor(self) -> str:
        return self._unidades_valor

    @unidadesValor.setter
    def unidadesValor(self, valor: str) -> None:
        self._fijar("_unidades_valor", self.unidadesValorChanged, valor)

    @pyqtProperty(str, notify=unidadesVariacionChanged)
    def unidadesVariacion(self) -> str:
        return self._unidades_variacion

    @unidadesVariacion.setter
    def unidadesVariacion(self, valor: str) -> None:
        self._fijar("_unidades_variacion", self.unidadesVariacionChanged, valor)

    @pyqtProperty(str, notify=unidadesColorChanged)
    def unidadesColor(self) -> str:
        return self._unidades_color

    @unidadesColor.setter
    def unidadesColor(self, valor: str) -> None:
        self._fijar("_unidades_color", self.unidadesColorChanged, valor)

    @pyqtProperty(str, notify=totalValorChanged)
    def totalValor(self) -> str:
        return self._total_valor

    @totalValor.setter
    def totalValor(self, valor: str) -> None:
        self._fijar("_total_valor", self.totalValorChanged, valor)

    @pyqtProperty(str, notify=totalVariacionChanged)
    def totalVariacion(self) -> str:
        return self._total_variacion

    @totalVariacion.setter
    def totalVariacion(self, valor: str) -> None:
        self._fijar("_total_variacion", self.totalVariacionChanged, valor)

    @pyqtProperty(str, notify=totalColorChanged)
    def totalColor(self) -> str:
        return self._total_color

    @totalColor.setter
    def totalColor(self, valor: str) -> None:
        self._fijar("_total_color", self.totalColorChanged, valor)

    @pyqtProperty(str, notify=ticketValorChanged)
    def ticketValor(self) -> str:
        return self._ticket_valor

    @ticketValor.setter
    def ticketValor(self, valor: str) -> None:
        self._fijar("_ticket_valor", self.ticketValorChanged, valor)

    @pyqtProperty(str, notify=ticketVariacionChanged)
    def ticketVariacion(self) -> str:
        return self._ticket_variacion

    @ticketVariacion.setter
    def ticketVariacion(self, valor: str) -> None:
        self._fijar("_ticket_variacion", self.ticketVariacionChanged, valor)

    @pyqtProperty(str, notify=ticketColorChanged)
    def ticketColor(self) -> str:
        return self._ticket_color

    @ticketColor.setter
    def ticketColor(self, valor: str) -> None:
        self._fijar("_ticket_color", self.ticketColorChanged, valor)

    @pyqtProperty(int, notify=ventasTendenciaChanged)
    def ventasTendencia(self) -> int:
        return self._ventas_tendencia

    @ventasTendencia.setter
    def ventasTendencia(self, valor: int) -> None:
        if self._ventas_tendencia != valor:
            self._ventas_tendencia = valor
            self.ventasTendenciaChanged.emit()

    @pyqtProperty(int, notify=unidadesTendenciaChanged)
    def unidadesTendencia(self) -> int:
        return self._unidades_tendencia

    @unidadesTendencia.setter
    def unidadesTendencia(self, valor: int) -> None:
        if self._unidades_tendencia != valor:
            self._unidades_tendencia = valor
            self.unidadesTendenciaChanged.emit()

    @pyqtProperty(int, notify=totalTendenciaChanged)
    def totalTendencia(self) -> int:
        return self._total_tendencia

    @totalTendencia.setter
    def totalTendencia(self, valor: int) -> None:
        if self._total_tendencia != valor:
            self._total_tendencia = valor
            self.totalTendenciaChanged.emit()

    @pyqtProperty(int, notify=ticketTendenciaChanged)
    def ticketTendencia(self) -> int:
        return self._ticket_tendencia

    @ticketTendencia.setter
    def ticketTendencia(self, valor: int) -> None:
        if self._ticket_tendencia != valor:
            self._ticket_tendencia = valor
            self.ticketTendenciaChanged.emit()

    @pyqtProperty("QVariantList", notify=serieVentasChanged)
    def serieVentas(self) -> list:
        return self._serie_ventas

    @serieVentas.setter
    def serieVentas(self, valores: list) -> None:
        if self._serie_ventas != valores:
            self._serie_ventas = valores
            self.serieVentasChanged.emit()

    @pyqtProperty("QVariantList", notify=serieUnidadesChanged)
    def serieUnidades(self) -> list:
        return self._serie_unidades

    @serieUnidades.setter
    def serieUnidades(self, valores: list) -> None:
        if self._serie_unidades != valores:
            self._serie_unidades = valores
            self.serieUnidadesChanged.emit()

    @pyqtProperty("QVariantList", notify=serieFacturadoChanged)
    def serieFacturado(self) -> list:
        return self._serie_facturado

    @serieFacturado.setter
    def serieFacturado(self, valores: list) -> None:
        if self._serie_facturado != valores:
            self._serie_facturado = valores
            self.serieFacturadoChanged.emit()

    @pyqtProperty("QVariantList", notify=serieTicketChanged)
    def serieTicket(self) -> list:
        return self._serie_ticket

    @serieTicket.setter
    def serieTicket(self, valores: list) -> None:
        if self._serie_ticket != valores:
            self._serie_ticket = valores
            self.serieTicketChanged.emit()

    def actualizar_series(self, ventas: list, unidades: list,
                          facturado: list, ticket: list) -> None:
        self.serieVentas = ventas
        self.serieUnidades = unidades
        self.serieFacturado = facturado
        self.serieTicket = ticket

    @pyqtProperty("QVariantMap", notify=ventasDetalleChanged)
    def ventasDetalle(self) -> dict:
        return self._ventas_detalle

    @ventasDetalle.setter
    def ventasDetalle(self, valor: dict) -> None:
        self._fijar("_ventas_detalle", self.ventasDetalleChanged, valor)

    @pyqtProperty("QVariantMap", notify=unidadesDetalleChanged)
    def unidadesDetalle(self) -> dict:
        return self._unidades_detalle

    @unidadesDetalle.setter
    def unidadesDetalle(self, valor: dict) -> None:
        self._fijar("_unidades_detalle", self.unidadesDetalleChanged, valor)

    @pyqtProperty("QVariantMap", notify=totalDetalleChanged)
    def totalDetalle(self) -> dict:
        return self._total_detalle

    @totalDetalle.setter
    def totalDetalle(self, valor: dict) -> None:
        self._fijar("_total_detalle", self.totalDetalleChanged, valor)

    @pyqtProperty("QVariantMap", notify=ticketDetalleChanged)
    def ticketDetalle(self) -> dict:
        return self._ticket_detalle

    @ticketDetalle.setter
    def ticketDetalle(self, valor: dict) -> None:
        self._fijar("_ticket_detalle", self.ticketDetalleChanged, valor)

    @pyqtProperty(str, notify=periodoDescripcionChanged)
    def periodoDescripcion(self) -> str:
        return self._periodo_descripcion

    @periodoDescripcion.setter
    def periodoDescripcion(self, valor: str) -> None:
        self._fijar("_periodo_descripcion", self.periodoDescripcionChanged, valor)

    def actualizar_detalles(self, ventas: dict, unidades: dict, total: dict,
                             ticket: dict, periodo: str) -> None:
        self.ventasDetalle = ventas
        self.unidadesDetalle = unidades
        self.totalDetalle = total
        self.ticketDetalle = ticket
        self.periodoDescripcion = periodo

    @staticmethod
    def _signo(texto: str) -> int:
        if texto.startswith("▲"):
            return 1
        if texto.startswith("▼"):
            return -1
        return 0

    @pyqtSlot(str, str, str, str, str, str, str, str, str, str, str, str)
    def actualizar(
        self,
        ventas_valor: str,
        ventas_variacion: str,
        ventas_color: str,
        unidades_valor: str,
        unidades_variacion: str,
        unidades_color: str,
        total_valor: str,
        total_variacion: str,
        total_color: str,
        ticket_valor: str,
        ticket_variacion: str,
        ticket_color: str,
    ) -> None:
        self.ventasValor = ventas_valor
        self.ventasVariacion = ventas_variacion
        self.ventasColor = ventas_color
        self.unidadesValor = unidades_valor
        self.unidadesVariacion = unidades_variacion
        self.unidadesColor = unidades_color
        self.totalValor = total_valor
        self.totalVariacion = total_variacion
        self.totalColor = total_color
        self.ticketValor = ticket_valor
        self.ticketVariacion = ticket_variacion
        self.ticketColor = ticket_color
        self.ventasTendencia = self._signo(ventas_variacion)
        self.unidadesTendencia = self._signo(unidades_variacion)
        self.totalTendencia = self._signo(total_variacion)
        self.ticketTendencia = self._signo(ticket_variacion)
