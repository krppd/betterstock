from __future__ import annotations

import ctypes
import sys

from PyQt6.QtWidgets import QWidget

DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
S_OK = 0
MARGEN_UNO = 1


class Margenes(ctypes.Structure):
    _fields_ = (
        ("cxLeftWidth", ctypes.c_long),
        ("cxRightWidth", ctypes.c_long),
        ("cyTopHeight", ctypes.c_long),
        ("cyBottomHeight", ctypes.c_long),
    )


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
        extender_marco = getattr(dwmapi, "DwmExtendFrameIntoClientArea", None)
        if fijar_atributo is None or extender_marco is None:
            return False

        fijar_atributo.argtypes = (
            wintypes.HWND,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_int),
            wintypes.DWORD,
        )
        fijar_atributo.restype = ctypes.c_long
        extender_marco.argtypes = (wintypes.HWND, ctypes.POINTER(Margenes))
        extender_marco.restype = ctypes.c_long

        preferencia = ctypes.c_int(DWMWCP_ROUND)
        resultado = fijar_atributo(
            manejador,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(preferencia),
            ctypes.sizeof(preferencia),
        )
        margenes = Margenes(MARGEN_UNO, MARGEN_UNO, MARGEN_UNO, MARGEN_UNO)
        extender_marco(manejador, ctypes.byref(margenes))
        return resultado == S_OK
    except Exception:
        return False
