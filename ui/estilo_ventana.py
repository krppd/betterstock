from __future__ import annotations

import ctypes
import sys

from PyQt6.QtWidgets import QWidget

DWMWA_NCRENDERING_POLICY = 2
DWMNCRP_ENABLED = 2
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
S_OK = 0

GWL_STYLE = -16
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_FRAME = WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_FLAGS = SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED


class _MARGINS(ctypes.Structure):
    _fields_ = (
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cyTopHeight", ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int),
    )


def aplicar_estilo_ventana(ventana: QWidget) -> bool:
    """Fuerza el marco y la sombra nativos de DWM en Windows 10.

    ``FluentWindow`` (vía qframelesswindow) quita los estilos de marco y en
    Windows 10 la sombra no se materializa hasta que se reenvía
    ``WM_NCCALCSIZE`` con ``SWP_FRAMECHANGED``. No propaga excepciones y
    devuelve ``False`` fuera de Windows o si falta cualquier API.
    """
    if sys.platform != "win32":
        return False
    try:
        from ctypes import wintypes

        manejador = wintypes.HWND(int(ventana.winId()))
        if not manejador:
            return False

        dwmapi = ctypes.windll.dwmapi
        user32 = ctypes.windll.user32

        composicion_activa = getattr(dwmapi, "DwmIsCompositionEnabled", None)
        fijar_atributo = getattr(dwmapi, "DwmSetWindowAttribute", None)
        extender = getattr(dwmapi, "DwmExtendFrameIntoClientArea", None)
        mover = getattr(user32, "SetWindowPos", None)
        if None in (composicion_activa, fijar_atributo, extender, mover):
            return False

        composicion_activa.argtypes = (ctypes.POINTER(wintypes.BOOL),)
        composicion_activa.restype = ctypes.c_long
        composicion = wintypes.BOOL()
        if (
            composicion_activa(ctypes.byref(composicion)) != S_OK
            or not composicion.value
        ):
            return False

        # Get/SetWindowLongPtrW es la variante segura en 64 bits; en 32 bits
        # esos símbolos no existen y se cae a Get/SetWindowLongW.
        obtener_largo = getattr(user32, "GetWindowLongPtrW", None)
        poner_largo = getattr(user32, "SetWindowLongPtrW", None)
        tipo_largo = ctypes.c_ssize_t
        if obtener_largo is None or poner_largo is None:
            obtener_largo = user32.GetWindowLongW
            poner_largo = user32.SetWindowLongW
            tipo_largo = ctypes.c_long
        obtener_largo.argtypes = (wintypes.HWND, ctypes.c_int)
        obtener_largo.restype = tipo_largo
        poner_largo.argtypes = (wintypes.HWND, ctypes.c_int, tipo_largo)
        poner_largo.restype = tipo_largo

        estilo = obtener_largo(manejador, GWL_STYLE)
        poner_largo(manejador, GWL_STYLE, estilo | WS_FRAME)

        fijar_atributo.argtypes = (
            wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD
        )
        fijar_atributo.restype = ctypes.c_long
        politica = ctypes.c_int(DWMNCRP_ENABLED)
        fijar_atributo(
            manejador,
            DWMWA_NCRENDERING_POLICY,
            ctypes.cast(ctypes.byref(politica), ctypes.c_void_p),
            ctypes.sizeof(politica),
        )

        extender.argtypes = (wintypes.HWND, ctypes.POINTER(_MARGINS))
        extender.restype = ctypes.c_long
        margenes = _MARGINS(-1, -1, -1, -1)
        extender(manejador, ctypes.byref(margenes))

        mover.argtypes = (
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        )
        mover.restype = wintypes.BOOL
        mover(manejador, None, 0, 0, 0, 0, SWP_FLAGS)

        # Esquinas redondeadas recién en Windows 11 (build 22000+).
        if (
            hasattr(sys, "getwindowsversion")
            and sys.getwindowsversion().build >= 22000
        ):
            preferencia = ctypes.c_int(DWMWCP_ROUND)
            fijar_atributo(
                manejador,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.cast(ctypes.byref(preferencia), ctypes.c_void_p),
                ctypes.sizeof(preferencia),
            )
        return True
    except Exception:
        return False
