# BetterStock — Inventory Control

A desktop application for stock control in a convenience store, built with Python 3 + PyQt6.
Data is stored in a SQLite database and passwords are hashed with bcrypt.

## Structure

```
betterstock-open/
├── app.py              Entry point
├── config.py           Project paths
├── requirements.txt    Dependencies
├── models/             Entities: Producto, Movimiento (Entrada/Salida/Ajuste), Usuario,
│                       Venta, Comercio, and CUIT/CUIL validation
├── repositories/       SQLite read and write
├── services/           Business logic, CSV import, report export and printing
├── views/              UI windows (use the ui/ interfaces)
├── utils/              Shared helpers (number and text formatting)
├── ui/
│   ├── designer/       Qt Designer .ui files
│   ├── generated/      Classes generated with pyuic6
│   ├── manual/         Hand-written controls
│   ├── widgets/        Own widgets (scrolling button and label, notifications)
│   ├── qml/            Statistics cards in QML
│   ├── tema.py         Color and typography tokens (ui/tokens.json)
│   └── estilos.py      Light/dark theme and typography
├── scripts/            UI regeneration script
├── tests/              pytest suite
├── docs/               Architecture overview and edition scope
├── Recursos/           Images, fonts and the Qt resource file (Recursos.qrc / Recursos_rc.py)
└── output/             Exports and backups, inside the per-user data folder
```

## Installation (Windows, PowerShell)

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Running

With the virtual environment activated:

```powershell
python app.py
```

## First run

The first time the program is opened, it asks for the shop details: name, address,
CUIT and phone. They are stored in `betterstock.db`, inside the per-user data
folder: `%APPDATA%\BetterStock` on Windows, `$XDG_DATA_HOME/BetterStock` (or
`~/.local/share/BetterStock`) elsewhere. To start from scratch, delete that file.

The CUIT can be that of a company (`30-...`) or the CUIL of a monotributo taxpayer
(`20-...`, `23-...`, `24-...`, `27-...`); it is accepted with or without hyphens. The
check digit is validated while you type, without querying the internet.

There are no default users: the administrator is created on the first run.

## Ticket printing

At checkout, the ticket is printed with **the system printer** (the one configured
on the computer) or saved as a PDF. No setup is required: after the sale, a dialog
appears with the sale result and the buttons "Print ticket" and "Close".

If printing fails, the sale is still recorded and the ticket can be reprinted later.

The thermal printer (ESC/POS) code is not in this repository: the app prints with
the system printer or saves a PDF.

## Free edition

**BetterStock is open source and free.**

This repository contains the complete free edition. It works fully offline and
does not require a license, a server or any external service.

What the free edition includes:

- Inventory control with products, movements and sales
- Customer and store credit (fiados) management
- CSV import
- Statistics for the last 12 months
- Cash register closing with automatic backup on your computer
- Split payments on sales
- Cancellations with a supervisor code
- A single administrator user, who can change their own password

The free plan allows up to 50 products and one year of statistics. Imports are
not limited.

A paid edition with advanced features (advanced store credit, advanced
statistics, cloud backup and more) is available on
[betterstock.tech](https://betterstock.tech).

## Regenerating an interface

If a `.ui` file is changed in Qt Designer:

```powershell
python scripts\regenerar_ui.py
```

The script compiles each `.ui` with `pyuic6` and puts back what `pyuic6` cannot
generate: the imports of own widgets and the hand-written blocks, marked in the
file with `# --- INICIO CODIGO MANUAL ---`.

The conversion of the Qt widgets to the Fluent ones (`BodyLabel`, `TableWidget`,
`PrimaryPushButton`, the icons) is hand-written in the generated files and
`pyuic6` does not reproduce it, so the script **does not touch** the files that
already have it: it reports them and moves on. Those have to be updated by hand.

`pyuic6` must be the version from `requirements.txt` (`PyQt6==6.11.0`): with another
version the generated file differs (e.g. `setFixedSize` instead of `resize`, plus an
extra resources import) and you have to re-add the custom widgets import by hand.

PyQt6's pyuic6 does not add the resources import; `ui/generated/__init__.py` does,
so the images keep working. The `Recursos/` folder must stay at the root.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -q -p no:randomly
```

The interface uses the [Inter](https://github.com/rsms/inter) typeface by Rasmus Andersson, licensed under the [SIL Open Font License 1.1](Recursos/fuentes/OFL.txt).

## Code signing

The Windows executable is **not code signed**. Windows SmartScreen shows a
warning the first time you run it, because the binary has no publisher
certificate. Everything else about the build is in the open: the spec
(`BetterStock.spec`), the workflow (`.github/workflows/build-free.yml`) and the
SHA-256 of every published archive.

## Privacy

BetterStock Free does not transfer any information to other networked systems
unless specifically requested by the user or the person installing or operating
it. All data stays local on the user's computer.
