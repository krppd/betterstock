# BetterStock — External interface

This document describes the external interfaces of the free edition.

## Data location

- Database: `betterstock.db` inside the per-user data folder.
- Windows: `%APPDATA%\BetterStock`
- Linux/macOS: `$XDG_DATA_HOME/BetterStock` or `~/.local/share/BetterStock`
- Override: `BETTERSTOCK_HOME` or `BETTERSTOCK_DATA_DIR`
- Exports and backups: `output/` next to the database.

## Backup

- On-demand copy of the SQLite database, stored locally in `output/backups/`.

## Import

- CSV import of the product list (code, name, prices, stock, category, etc.).

## Printing

- System printer or PDF export from the sale dialog. No external service.

## Network

- No outbound requests by default.
- Optional: Open Food Facts API for product photos (disabled by default).