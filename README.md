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
├── services/           Business logic, CSV/PDF export and printing
├── views/              UI windows (use the ui/ interfaces)
├── ui/
│   ├── designer/       Qt Designer .ui files
│   ├── generated/      Classes generated with pyuic6 (do not edit by hand)
│   └── manual/         Hand-written interface (sales, settings)
├── Recursos/           Images and Qt resource file (Recursos.qrc / Recursos_rc.py)
├── data/               betterstock.db (productos, movimientos, usuarios, comercio)
└── output/             Suggested folder for tickets, reports and exports
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
CUIT and phone. They are stored in `data/betterstock.db` and it does not ask for
them again. To start from scratch, delete that file.

The CUIT can be that of a company (`30-...`) or the CUIL of a monotributo taxpayer
(`20-...`, `23-...`, `24-...`, `27-...`); it is accepted with or without hyphens. The
check digit is validated while you type, without querying the internet.

There are no default users: the administrator is created on the first run.

## Ticket printing

At checkout, the ticket is printed with **the system printer** (the one configured
on the computer) or saved as a PDF. No setup is required: after the sale, a dialog
appears with the sale result and the buttons "Print ticket", "Save PDF" and
"Close".

If printing fails, the sale is still recorded and the ticket can be saved as a PDF.

The thermal printer (ESC/POS) code is not in this repository: the app prints with
the system printer or saves a PDF.

## Free edition and premium

**BetterStock is open source and free.**

This repository contains the complete free edition and works without a license or
a server. Premium features are optional: they are delivered as a plugin that is
downloaded and verified when a license is activated from **Settings**. The
**Premium** menu entry opens that panel; without a license it takes you to Settings.

What the free edition includes:

- Inventory control with products, movements and sales
- Customer and store credit (fiados) management
- CSV import/export
- Statistics for the last 12 months
- Cash register closing with automatic backup on your computer
- Split payments on sales
- Mercado Pago with your own token
- Cancellations with a supervisor code
- No limit on products or imports
- A single administrator user, who can change their own password

Premium plans, current pricing and the full feature list are on
[betterstock.tech](https://betterstock.tech).

The only licensing code in this repository is the Ed25519 verifier
(`services/plan_motor.py`) and the activation code (`services/licencia_remota.py`).
The private signing key is not in this repository.

## Regenerating an interface

If a `.ui` file is changed in Qt Designer:

```powershell
pyuic6 ui\designer\main.ui -o ui\generated\main_ui.py
```

`pyuic6` must be the version from `requirements.txt` (`PyQt6==6.11.0`): with another
version the generated file differs (e.g. `setFixedSize` instead of `resize`, plus an
extra resources import) and you have to re-add the custom widgets import by hand.

PyQt6's pyuic6 does not add the resources import; `ui/generated/__init__.py` does,
so the images keep working. The `Recursos/` folder must stay at the root.

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
