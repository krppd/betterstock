# BetterStock — Data formats

## CSV product import

Columns are matched by header name. Required fields: code, name, cost price, sale price. Optional fields include category, minimum stock, barcode (EAN), expiry date, and promotion fields.

## Database

SQLite schema is defined in `repositories/sqlite.py` and created automatically on first run.