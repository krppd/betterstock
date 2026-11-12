from __future__ import annotations

import ctypes
import sys

from PyQt6.QtWidgets import QWidget

DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
S_OK = 0


def aplicar_estilo_ventana(ventana: QWidget) -> bool:
    if sys.platform != "win32":
        return False
    try:
        from ctypes import wintypes

        manejador = wintypes.HWND(int(ventana.winId()))
        if not manejador:
            return False

        dwmapi = ctypes.windll.dwmapi
        fijar_atributo = getattr(dwmapi, "DwmSetWindowAttribute", None)
        if fijar_atributo is None:
            return False

        fijar_atributo.argtypes = (
            wintypes.HWND,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_int),
            wintypes.DWORD,
        )
        fijar_atributo.restype = ctypes.c_long

        preferencia = ctypes.c_int(DWMWCP_ROUND)
        resultado = fijar_atributo(
            manejador,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(preferencia),
            ctypes.sizeof(preferencia),
        )
        return resultado == S_OK
    except Exception:
        return False
