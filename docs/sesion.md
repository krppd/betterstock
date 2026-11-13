# Free edition

This repository is the free edition of BetterStock. It runs entirely on the
user's computer: no server, license or activation is required.

## What it includes

- Full point of sale: products, sales and cash register, split payments, customers,
  store credit (fiados), movements, stock counts, expirations, statistics,
  CSV import, report export to CSV and PDF, ticket printing, local backup and
  cash shifts.
- A single administrator user, created on the first run, who can change their own
  password.
- Movement filtering by reason, including the history of each stock count.
- General settings, backups and cancellation codes.

## What it does not include

- Electronic invoicing (ARCA): there is no assistant, issuing, CAE or fiscal QR.
- Optional premium features. They are not part of this repository, and this
  repository has no plugin loader: the plan is always the free one.

## Limits

The free plan allows up to 50 products and one year (365 days) of statistics.
Imports are not limited. These limits live in `services/planes.py` and are
enforced when a product is added (`views/ventana_productos.py`) and when a
statistics period is chosen (`views/ventana_estadisticas.py`).

## Tests

```bash
python3 -m pytest tests/ -q -p no:randomly
```

## Native Windows rendering

The window uses the native Windows stack instead of the cross-platform one:

- Fonts are rendered by DirectWrite, the engine native Windows apps use.
- Widgets that Fluent does not paint itself (combo boxes, spin boxes, menus,
  message boxes) follow the `windowsvista` style. Outside Windows the app keeps
  the `Fusion` style.
- The Mica backdrop is left to the Fluent library. The app only applies the
  native rounded corners, so it does not overwrite the library's frame margins.
- The navigation sidebar can use the acrylic effect.

Two dependencies are required for the acrylic blur: `scipy` and `colorthief`.
They come with the `PyQt6-Fluent-Widgets[full]` extra, pinned to `scipy<2`
because SciPy 2.0 removes `scipy.ndimage.filters`, the module the blur imports.
Run `pip install -r requirements.txt` after pulling.

`ui/compat_fluent.py` patches a bug in qfluentwidgets 1.11.3, where the calendar
scroll view disconnects its animation with a wildcard call and makes Qt print
`wildcard call disconnects from destroyed signal`. `aplicar_parches()` must run
once at startup, before any window is created.

The visual result still has to be confirmed on Windows 10/11: the Mica backdrop
needs Windows 11 22H2 or newer, and `output/fuentes.log` reports whether a font
had to be loaded from memory because DirectWrite could not read it from disk.

