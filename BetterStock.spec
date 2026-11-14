# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the BetterStock free edition (Windows build target).
#
# Build locally:
#   python -m venv .venv
#   .\.venv\Scripts\activate
#   pip install -r requirements.txt pyinstaller
#   pyinstaller --noconfirm BetterStock.spec
#
# The version comes from BETTERSTOCK_VERSION (set by CI from the tag) or
# config.APP_VERSION. The metadata has to be set on every binary so the
# executable reports its own version.

import os
import sys
from pathlib import Path

root = Path(SPECPATH).resolve()
sys.path.insert(0, str(root))

from config import APP_VERSION  # noqa: E402
from PyInstaller.utils.hooks import collect_data_files, collect_submodules  # noqa: E402
from PyInstaller.utils.win32 import versioninfo  # noqa: E402

block_cipher = None


def _version() -> str:
    cruda = os.environ.get("BETTERSTOCK_VERSION") or APP_VERSION
    cruda = cruda.strip().lstrip("vV")
    partes = cruda.split(".")
    # Si el ref no es un tag (workflow_dispatch en una rama), cae a APP_VERSION.
    if not partes or not all(p.isdigit() for p in partes):
        partes = APP_VERSION.strip().lstrip("vV").split(".")
    while len(partes) < 4:
        partes.append("0")
    return ".".join(partes[:4])


VERSION = _version()
VERSION_TUPLE = tuple(int(x) for x in VERSION.split("."))

VERSIONINFO = versioninfo.VSVersionInfo(
    ffi=versioninfo.FixedFileInfo(
        filevers=VERSION_TUPLE,
        prodvers=VERSION_TUPLE,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        versioninfo.StringFileInfo(
            [
                versioninfo.StringTable(
                    u"040904B0",
                    [
                        versioninfo.StringStruct(u"CompanyName", "BetterStock"),
                        versioninfo.StringStruct(u"FileDescription", "BetterStock"),
                        versioninfo.StringStruct(u"FileVersion", VERSION),
                        versioninfo.StringStruct(u"InternalName", "BetterStock"),
                        versioninfo.StringStruct(u"LegalCopyright", "MIT License"),
                        versioninfo.StringStruct(u"OriginalFilename", "BetterStock.exe"),
                        versioninfo.StringStruct(u"ProductName", "BetterStock"),
                        versioninfo.StringStruct(u"ProductVersion", VERSION),
                    ],
                )
            ]
        ),
        versioninfo.VarFileInfo([versioninfo.VarStruct(u"Translation", [1033, 1200])]),
    ],
)

datas = [
    (str(root / "Recursos"), "Recursos"),
    (str(root / "ui"), "ui"),
    (str(root / "config.py"), "."),
] + collect_data_files("qfluentwidgets")

# Collect submodules that PyInstaller may miss (Qt backends, crypto, etc.).
hiddenimports = [
    "bcrypt",
    "matplotlib.backends.backend_qtagg",
    "PyQt6.QtSvg",
    "PyQt6.QtPrintSupport",
    "sqlite3",
    "numpy",
    "scipy",
    "scipy.ndimage",
    "scipy.ndimage.filters",
    "colorthief",
] + collect_submodules("qfluentwidgets")

a = Analysis(
    ["app.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tests", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BetterStock",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "Recursos" / "icono.ico") if (root / "Recursos" / "icono.ico").exists() else None,
    version=VERSIONINFO,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="BetterStock",
)
