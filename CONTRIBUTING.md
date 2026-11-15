# Contributing to BetterStock

Thank you for taking the time to contribute. This repository hosts the free edition of BetterStock, where all shared development, bug fixes, and improvements take place.

## Before you start

Search existing issues first, as someone may have already reported or addressed the same problem. If you plan to make a major change, open an issue first so the approach can be discussed before writing code; for minor fixes, you can open a pull request directly.

Keep each pull request to a single commit so the Git history remains clean and readable. Write all descriptions and messages in English, structure your pull request using the `Objective`, `Changes`, and `Scope` sections, and do not use emojis anywhere in code, commits, issues, or pull requests.

## Running it

BetterStock runs on Windows and Linux and requires Python 3.14.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

Start the application with `python app.py`. On the first run, the program prompts for your shop details and creates an administrator account.

## Tests

Every change must pass the automated test suite:

```bash
python -m pytest tests/ -q -p no:randomly
```

On Linux, run the suite with `QT_QPA_PLATFORM=offscreen` so it does not require an active display server.

The repository also includes three automated visual checks that evaluate the rendered interface as a user sees it, catching truncated text, insufficient color contrast, and misaligned tabular numbers:

```bash
python scripts/verificar_texto.py
python scripts/verificar_contraste.py
python scripts/verificar_cifras_tabulares.py
```

Running `scripts/verificar_todo.py` executes all three checks at once. They are enforced in CI, so any pull request that fails them will not pass.

## How the code is laid out

```text
views/         UI windows and dialogs (no direct database access)
services/      business logic and domain rules
repositories/  data persistence and database queries
models/        domain entities
ui/            theme tokens, custom widgets, and generated interfaces
utils/         shared helper utilities
tests/         automated test suite
```

The core architectural rule is simple: windows in `views/` call `services/`, never `repositories/`. This separation makes it possible to modify the storage layer without touching the user interface.

Similarly, a model never imports a service. If a model requires helper logic, that function belongs in `models/`. Importing the other way around creates circular dependencies, which is why `validacion_identificador` lives in `models/`.

## The interface

The user interface is built with PyQt6 and PyQt6-Fluent-Widgets. Qt Designer `.ui` files live in `ui/designer/`, and the compiled Python code in `ui/generated/` must never be edited by hand. After modifying a `.ui` file, regenerate the code by running:

```bash
python scripts/regenerar_ui.py
```

Hand-written widgets live in `ui/manual/` and `ui/widgets/`. The visual theme is defined in `ui/tokens.json` and applied through `ui/tema.py`. Colors, dimensions, and fonts belong in the theme configuration rather than hardcoded inside individual widgets.

## The database

All application data is stored in a single SQLite file. The database schema is defined in `repositories/sqlite.py` and initialized automatically on the first run.

If you add a column, include it in both the initial schema definition and the migration logic within `repositories/sqlite.py`, and add a test that loads an older database to verify the new column is applied properly. Upgrades must preserve existing user data without loss.

## Commit messages

Write the commit title as a single line in the imperative mood:

```text
fix(fotos): make the photo search window work
feat(productos): add the barcode (EAN) field
```

Use the commit body to explain why the change was made rather than what changed: describe what broke, the root cause, and why this solution was chosen over alternatives. The diff itself already shows what changed.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
