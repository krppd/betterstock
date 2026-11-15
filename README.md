# BetterStock — Inventory Control

A desktop application for stock control in a convenience store, built with Python 3 + PyQt6.
Data is stored in a SQLite database and passwords are hashed with bcrypt.

Everything runs on the computer of the shop: there is no server, no account and no
activation. The whole application is MIT licensed and this repository is where it
is developed.

<!-- Demo video goes here -->

## What it does

- **Stock**: products with cost price, sale price, minimum stock, categories and
  stock counts. Search by code or name.
- **Sales**: barcode reader or keyboard, split payments, discounts, store credit
  (fiados) for customers, cash, card and transfer.
- **Cash register**: shifts with opening and closing, cash in and cash out, and the
  difference between what should be there and what is counted.
- **Customers**: name, phone, credit limit, tax condition and a balance history.
- **Statistics**: sales by day, ticket average, units sold and the best sellers,
  for the last 12 months.
- **Reports**: stock valuation, sales by period and the movement history.
- **Import**: CSV import of the product list.
- **Backup**: a copy of the database on demand, stored on the same computer.
- **Ticket printing** with the system printer or as a PDF.

## Download

The Windows build is published on the [releases page](https://github.com/krppd/betterstock/releases).
It is a portable build: unzip it and run `BetterStock.exe`, there is no installer
and nothing is written to the registry. The SHA-256 of every published archive is
next to it, in `SHA256.txt`.

The executable is not code signed yet, so Windows SmartScreen shows a warning the
first time you run it. See [Code signing policy](#code-signing-policy).

## Installation (Windows, PowerShell)

To run it from the source instead:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Documentation

See [docs/overview.md](docs/overview.md) and [docs/interface.md](docs/interface.md).

## Running

With the virtual environment activated:

```powershell
python app.py
```

## First run

The first time the program is opened, it asks for the shop details: name, address,
CUIT and phone. They are stored in `betterstock.db`, inside the per-user data
folder: `%APPDATA%\BetterStock` on Windows, `$XDG_DATA_HOME/BetterStock` (or
`~/.local/share/BetterStock`) elsewhere.

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

This repository is the free edition, and it is where it is developed: fixes and
improvements land here. It works fully offline and does not require a license, a
server or any external service.

What the free edition includes:

- Inventory control with products, movements and sales
- Customer and store credit (fiados) management
- CSV import
- Statistics for the last 12 months
- Cash register closing with automatic backup on your computer
- Split payments on sales
- Cancellations with a supervisor code
- A single administrator user, who can change their own password


A paid edition with advanced features (advanced store credit, advanced
statistics, cloud backup and more) is available on
[betterstock.tech](https://betterstock.tech).

## Code signing policy

The Windows executable is published from this repository and, once the project is
accepted by SignPath Foundation, it is signed with their certificate:

- Committers and reviewers: [@krppd](https://github.com/krppd) (repository owner)
- Approvers: [@krppd](https://github.com/krppd) (repository owner)

The build that produces the executable is `.github/workflows/build-free.yml`. It
compiles the program with PyInstaller, uploads the unsigned executable as a
workflow artifact and asks SignPath to sign it. The signature is applied **before**
the archive is packed, so the published ZIP contains the signed executable and the
published SHA-256 is the one of the signed archive. The release is only published
after the signing request is approved.

Everything about the build is open: the spec (`BetterStock.spec`), the workflow
(`.github/workflows/build-free.yml`) and the SHA-256 of every published archive.

## Privacy

BetterStock does not transfer any information to other networked systems unless
specifically requested by the user or the person installing or operating it. All
data stays local on the user's computer.

There is exactly one exception, and it is off by default: the product photo
search sends the name or the code of the product to Open Food Facts. It is turned
on in **Settings > Privacy > Search for product photos on the internet**, and while
it is off the application does not contact any external service. Loading a photo
from a URL that the user pastes is always done only on that request.

## Uninstalling

The build is portable: delete the unzipped folder and the application is gone.
To delete the data as well, remove the data folder (`%APPDATA%\BetterStock` on
Windows, `$XDG_DATA_HOME/BetterStock` elsewhere). Nothing else is written outside
that folder.

## Structure

```
betterstock/
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
├── scripts/            UI regeneration script and the visual verifiers
├── tests/              pytest suite
├── docs/               Architecture overview and edition scope
├── Recursos/           Images, fonts and the Qt resource file (Recursos.qrc / Recursos_rc.py)
└── output/             Exports and backups, inside the per-user data folder
```

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
version the generated file differs (e.g. `setFixedSize` instead of `resize`, plus
an extra resources import) and you have to re-add the custom widgets import by hand.

PyQt6's pyuic6 does not add the resources import; `ui/generated/__init__.py` does,
so the images keep working. The `Recursos/` folder must stay at the root.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -q -p no:randomly
```

The visual verifiers check that no text gets cut off, that the colour pairs meet
WCAG AA and that the amounts do not jump around when they update:

```powershell
python scripts\verificar_texto.py
python scripts\verificar_contraste.py
python scripts\verificar_cifras_tabulares.py
```

The interface uses the [Inter](https://github.com/rsms/inter) typeface by Rasmus Andersson, licensed under the [SIL Open Font License 1.1](Recursos/fuentes/OFL.txt).

## Contributing

Pull requests are welcome. The rules that keep the history readable:

- **One commit per pull request.** Squash merge is the only option on this repository, and a single commit keeps the history of `main` to one line per pull request.
- **No behaviour change without a reason in the commit message.** If a fix changes what the app does, say what it did before and what it does now.
- **The test suite has to pass.** `python -m pytest tests/ -q -p no:randomly`, and the visual verifiers too.
- **A test that cannot run says nothing.** If a test only passes because it skips, the code it covers is broken and the fix goes there, not in the skip.
- **Do not edit `ui/generated/` by hand.** Those files carry a hand written conversion to the Fluent widgets that `pyuic6` does not reproduce; `scripts/regenerar_ui.py` knows how to leave them alone.

The architecture and the conventions are in [`docs/overview.md`](docs/overview.md).
