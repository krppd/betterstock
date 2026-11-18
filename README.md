# BetterStock — Inventory Control

[![REUSE status](https://api.reuse.software/badge/github.com/krppd/betterstock)](https://api.reuse.software/info/github.com/krppd/betterstock)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=krppd_betterstock&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=krppd_betterstock)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=krppd_betterstock&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=krppd_betterstock)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/16724/badge)](https://www.bestpractices.dev/es/projects/16724/passing)

BetterStock is a point-of-sale and stock control app for small shops. It runs on the shop's own computer: no server, no online account, no license activation, and no internet needed to sell. Products, sales, customers, the cash register and backups live in a local SQLite database, and passwords are stored as bcrypt hashes.

This is the free, MIT-licensed edition. Fixes and improvements are developed here first and then shared with the paid edition, which adds extra tools and is available at [betterstock.tech](https://betterstock.tech).

## Features

- **Inventory**: Manage products with cost price, sale price, minimum stock alerts, categories, and stock counts. Search by barcode or name.
- **Point of Sale**: Barcode scanner or keyboard input, split payments (cash, card, transfer, and store credit), discounts, and sale cancellations authorized via supervisor code.
- **Cash Register**: Shift opening and closing, cash inflows/outflows, reconciliation between expected and counted balances, and automatic local backup upon closing.
- **Customers & Store Credit (Fiados)**: Customer profiles with name, phone, credit limit, tax condition, and running balance history.
- **Statistics & Reports**: Daily sales, average ticket, units sold, and best-selling products over the last 12 months, plus stock valuation and a movement history you can filter.
- **CSV Import & Local Backups**: Bulk product import via CSV and on-demand database backups stored on the local machine.
- **Ticket Printing**: Print receipts with the default system printer. If printing fails, the sale is still recorded and the receipt can be reprinted later (direct ESC/POS thermal printer drivers are not included in this repository).
- **Single Administrator**: Includes one administrator account created on first run, with password management.

> A commercial edition with advanced features (extended store credit tools, advanced analytics, cloud backups, and more) is available at [betterstock.tech](https://betterstock.tech).

## Download

The portable Windows build is available on the [Releases page](https://github.com/krppd/betterstock/releases). Simply unzip the archive and run `BetterStock.exe`—there is no installer and nothing is written to the Windows registry. The SHA-256 checksum for every release archive is published alongside it in `SHA256.txt`.

The executable is not code-signed yet, so Windows SmartScreen will display a warning the first time you run it. See [Code signing policy](#code-signing-policy) for details.

## Running from Source (Windows, PowerShell)

BetterStock requires Python 3.14:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## First Run & Uninstalling

On the first launch, the program prompts for the shop details (name, address, CUIT/CUIL, and phone) and creates the administrator account—there are no default credentials. The CUIT can belong to a company (`30-...`) or a *monotributo* taxpayer CUIL (`20-...`, `23-...`, `24-...`, `27-...`), with or without hyphens; the check digit is validated offline as you type.

All data is stored in `betterstock.db` inside the per-user data directory (`%APPDATA%\BetterStock` on Windows, or `$XDG_DATA_HOME/BetterStock` / `~/.local/share/BetterStock` on Linux).

Because the build is portable, deleting the unzipped application folder removes the program. To remove your data as well, delete the data directory mentioned above.

## Documentation

For architectural details and edition scope, see [docs/overview.md](docs/overview.md) and [docs/interface.md](docs/interface.md).

## Code Signing Policy

The Windows executable is built and published from this repository and, once approved by the [SignPath Foundation](https://about.signpath.io/), will be signed with their certificate:

- **Committers and reviewers**: [@krppd](https://github.com/krppd) (repository owner)
- **Approvers**: [@krppd](https://github.com/krppd) (repository owner)

The release workflow (`.github/workflows/build-free.yml`) compiles the application with PyInstaller (`BetterStock.spec`), uploads the unsigned binary as a workflow artifact, and submits it to SignPath for signing. The signature is applied **before** packaging the final ZIP archive, ensuring both the executable and the published SHA-256 checksum correspond to the signed build. Releases are only published after the signing request is approved.

## Privacy

BetterStock does not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it. All data stays local on the user's computer.

There is only one optional exception, which is disabled by default: the product photo search sends the product name or barcode to Open Food Facts when enabled under **Settings > Privacy > Search for product photos on the internet**. Loading a photo from a pasted URL only occurs upon explicit user request. See [SECURITY.md](SECURITY.md) for full details.

## Project Structure

```text
betterstock/
├── app.py              Application entry point
├── config.py           Project paths
├── requirements.txt    Runtime dependencies
├── models/             Domain entities (Producto, Movimiento, Usuario, Venta, Comercio) and CUIT/CUIL validation
├── repositories/       SQLite persistence and schema migrations
├── services/           Business logic, CSV import, statistics, and ticket printing
├── views/              UI windows and dialogs
├── utils/              Shared formatting helpers
├── ui/
│   ├── designer/       Qt Designer .ui files
│   ├── generated/      Classes compiled with pyuic6
│   ├── manual/         Hand-written UI controls
│   ├── widgets/        Custom widgets (scrolling labels/buttons, notifications)
│   ├── qml/            QML statistics cards
│   ├── tema.py         Color and typography tokens (ui/tokens.json)
│   └── estilos.py      Light/dark theme and typography rules
├── scripts/            UI regeneration script and visual verifiers
├── tests/              Automated pytest suite
├── docs/               Architecture overview and edition scope
├── Recursos/           Images, fonts, and Qt resource files (Recursos.qrc / Recursos_rc.py)
└── output/             Exports and backups (stored inside the per-user data directory)
```

## Regenerating the UI

After modifying a `.ui` file in Qt Designer, run:

```powershell
python scripts\regenerar_ui.py
```

The script compiles `.ui` files with `pyuic6` and restores custom widget imports and manual code blocks delimited by `# --- INICIO CODIGO MANUAL ---`.

Files in `ui/generated/` that already contain hand-written conversions from standard Qt widgets to Fluent widgets (`BodyLabel`, `TableWidget`, `PrimaryPushButton`, icons) are skipped by the script and reported in the console, as `pyuic6` cannot reproduce those conversions. Any updates to those specific files must be made carefully by hand.

Always use the `pyuic6` version pinned in `requirements.txt` (`PyQt6==6.12.0`) to prevent output diffs, and keep `Recursos/` at the repository root so `ui/generated/__init__.py` can load image resources properly.

## Tests & Contributing

To run the test suite and the WCAG/layout visual verifiers:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -q -p no:randomly
python scripts\verificar_todo.py
```

Pull requests are welcome. Please keep each pull request to a single commit (squash merge), document the reason for any behavioral change in the commit body, and ensure all unit and visual tests pass without relying on skipped tests. See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/overview.md](docs/overview.md) for full contribution guidelines.

The interface uses the [Inter](https://github.com/rsms/inter) typeface by Rasmus Andersson, licensed under the [SIL Open Font License 1.1](Recursos/fuentes/OFL.txt).
