# BetterStock — Architecture overview

BetterStock is a local-first desktop application. It has no always-on backend and
no telemetry: the user enters shop details and an administrator account, and every
record is stored on the user's computer.

## Components

- `models/` — plain Python entities and validation (`Producto`, `Venta`, `Usuario`,
  CUIT/CUIL verification).
- `repositories/` — SQLite read/write layer. There is one repository per entity;
  no ORM is used.
- `services/` — business rules: inventory, sales, store credit, backups, CSV/PDF
  exports, printing, and password hashing.
- `views/` — PyQt6 windows. Long operations are kept off the UI thread.
- `ui/` — Qt Designer files (`designer/`), generated classes (`generated/`, do not
  edit), and hand-written interfaces (`manual/`).
- `Recursos/` — images, fonts (Inter typeface under SIL Open Font License 1.1),
  and the compiled Qt resource file.

## Data storage

All runtime data lives in `data/betterstock.db` (SQLite) and exports are written to
`output/`. Both directories are created automatically and are ignored by Git.

Backups are stored in `output/backups/`. Passwords are hashed with bcrypt and the
CUIT verification digit is checked offline, so the application does not need a
network connection to validate a tax identifier.

## Scope

This repository is the **base edition** and works without a license or a server.
It does not include electronic invoicing (ARCA) or optional premium features,
which are delivered as a plugin when a license is activated. The base edition has
a single administrator account.

## Limits

The base edition has no hard product, statistics, or import limits. Statistics
cover the last 12 months.

## Development

Windows PowerShell:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -q -p no:randomly
```

Use the `pyuic6` version from `requirements.txt` when regenerating
`ui/generated/*.py`. Do not edit generated files by hand.

## Portability

The application targets Windows (PowerShell) but the source is cross-platform and
is also exercised on Linux with `QT_QPA_PLATFORM=offscreen` in the test suite.
