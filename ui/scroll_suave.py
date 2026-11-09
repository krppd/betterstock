from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QScrollBar

DURACION_MS = 150
PASO_RUEDA_PX = 40


def _vista(objeto: QObject) -> QAbstractItemView | None:
    actual = objeto
    while actual is not None:
        if isinstance(actual, QAbstractItemView):
            return actual
        actual = actual.parent()
    return None


def _horizontal(evento) -> bool:
    if evento.modifiers() & Qt.KeyboardModifier.ShiftModifier:
        return True
    delta = evento.angleDelta()
    return abs(delta.x()) > abs(delta.y())


def _pixeles(evento, horizontal: bool) -> int:
    bruto = evento.pixelDelta()
    if not bruto.isNull():
        return bruto.x() if horizontal else bruto.y()
    delta = evento.angleDelta()
    componente = (delta.x() or delta.y()) if horizontal else delta.y()
    return round(componente / 120 * PASO_RUEDA_PX)


class FiltroScrollSuave(QObject):

    def __init__(self, padre: QObject | None = None) -> None:
        super().__init__(padre)
        self._animaciones: dict[int, QPropertyAnimation] = {}
        self._pendiente: dict[int, int] = {}

    def eventFilter(self, objetivo: QObject, evento) -> bool:
        if evento.type() == QEvent.Type.Wheel:
            return self._rueda(objetivo, evento)
        if evento.type() == QEvent.Type.Show:
            self._preparar(objetivo)
        return False

    def _preparar(self, objetivo: QObject) -> None:
        if isinstance(objetivo, QAbstractItemView):
            objetivo.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            objetivo.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

    def _rueda(self, objetivo: QObject, evento) -> bool:
        vista = _vista(objetivo)
        if vista is None:
            return False
        if evento.modifiers() & Qt.KeyboardModifier.ControlModifier:
            return False
        horizontal = _horizontal(evento)
        barra = vista.horizontalScrollBar() if horizontal else vista.verticalScrollBar()
        if barra.maximum() <= barra.minimum():
            return False
        pixeles = _pixeles(evento, horizontal)
        if pixeles == 0:
            return False
        if not evento.pixelDelta().isNull():
            self._detener(barra)
            barra.setValue(barra.value() - pixeles)
            return True
        self._animar(barra, pixeles)
        return True

    def _animar(self, barra: QScrollBar, pixeles: int) -> None:
        clave = id(barra)
        animacion = self._animaciones.get(clave)
        if animacion is None:
            animacion = QPropertyAnimation(barra, b"value", barra)
            animacion.setDuration(DURACION_MS)
            animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
            animacion.finished.connect(lambda k=clave: self._pendiente.pop(k, None))
            barra.destroyed.connect(lambda _obj=None, k=clave: self._olvidar(k))
            self._animaciones[clave] = animacion
            self._pendiente[clave] = barra.value()
        destino = self._pendiente.get(clave, barra.value()) - pixeles
        destino = max(barra.minimum(), min(barra.maximum(), destino))
        self._pendiente[clave] = destino
        if animacion.state() == QPropertyAnimation.State.Running:
            animacion.stop()
        animacion.setStartValue(barra.value())
        animacion.setEndValue(destino)
        animacion.start()

    def _detener(self, barra: QScrollBar) -> None:
        animacion = self._animaciones.get(id(barra))
        if animacion is not None:
            animacion.stop()
        self._pendiente.pop(id(barra), None)

    def _olvidar(self, clave: int) -> None:
        self._animaciones.pop(clave, None)
        self._pendiente.pop(clave, None)

    def _limpiar(self) -> None:
        for animacion in self._animaciones.values():
            if animacion.state() == QPropertyAnimation.State.Running:
                animacion.stop()
        self._animaciones.clear()
        self._pendiente.clear()


def instalar_scroll_suave(aplicacion: QApplication) -> FiltroScrollSuave:
    filtro = FiltroScrollSuave(aplicacion)
    aplicacion.installEventFilter(filtro)
    aplicacion.aboutToQuit.connect(filtro._limpiar)
    return filtro
