# BetterStock — Architecture overview

BetterStock is a local-first desktop application. It has no always-on backend and
no telemetry: the user enters shop details and an administrator account, and every
record is stored on the user's computer.

## Components

- `models/` — plain Python entities and validation (`Producto`, `Venta`, `Usuario`,
  CUIT/CUIL verification).
- `repositories/` — SQLite read/write layer. There is one repository per entity;
  no ORM is used.
- `services/` — business rules: inventory, sales, store credit, backups, CSV
  import, report export, printing, and password hashing.
- `views/` — PyQt6 windows. Long operations are kept off the UI thread.
- `ui/` — Qt Designer files (`designer/`), generated classes (`generated/`), hand-written controls (`manual/`), own widgets (`widgets/`) and the statistics cards in QML (`qml/`). The colors and the typography come from `ui/tokens.json` and are exposed through `ui/tema.py`.
- `Recursos/` — images, fonts (Inter typeface under SIL Open Font License 1.1), and the compiled Qt resource file.

## Data storage

All runtime data lives in a SQLite database named `betterstock.db`, inside the
per-user data folder: `%APPDATA%\BetterStock` on Windows,
`$XDG_DATA_HOME/BetterStock` (or `~/.local/share/BetterStock`) elsewhere. The
`BETTERSTOCK_HOME` or `BETTERSTOCK_DATA_DIR` environment variables override
that folder, which is what the tests use. Exports and backups are written to an
`output/` folder next to the database. The folder is created automatically.

Backups are stored in `output/backups/`. Passwords are hashed with bcrypt and the
CUIT verification digit is checked offline, so the application does not need a
network connection to validate a tax identifier.

## Scope

This repository is the **base edition** and works without a license or a server.
It does not include electronic invoicing (ARCA) or optional premium features,
and it has no plugin loader: the plan is always the free one. The base edition
has a single administrator account.

## Limits

The free plan allows up to 50 products and one year (365 days) of statistics.
Imports are not limited. The limits live in `services/planes.py` and are
enforced when a product is added and when a statistics period is chosen.

## Development

Windows PowerShell:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -q -p no:randomly
```

To regenerate the classes in `ui/generated/`, use `python scripts/regenerar_ui.py`
instead of calling `pyuic6` directly: the Fluent conversion of the generated
files is hand-written and `pyuic6` does not reproduce it, so the script leaves
those files alone. Do not edit generated files by hand.

## Portability

The application targets Windows (PowerShell) but the source is cross-platform and
is also exercised on Linux with `QT_QPA_PLATFORM=offscreen` in the test suite.
