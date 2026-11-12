from __future__ import annotations

import time

from PyQt6.QtCore import QDate, QtMsgType, qInstallMessageHandler
from PyQt6.QtWidgets import QApplication


def test_el_calendario_no_deja_warnings_al_desconectar() -> None:
    from qfluentwidgets import CalendarPicker

    warnings: list[str] = []
    qInstallMessageHandler(
        lambda tipo, contexto, mensaje: warnings.append(mensaje)
        if tipo == QtMsgType.QtWarningMsg else None
    )
    try:
        selector = CalendarPicker()
        selector.setDate(QDate.currentDate())
        selector._showCalendarView()
        limite = time.time() + 1.0
        while time.time() < limite:
            QApplication.processEvents()
            time.sleep(0.01)
    finally:
        qInstallMessageHandler(None)

    assert not [w for w in warnings if "wildcard" in w], warnings
