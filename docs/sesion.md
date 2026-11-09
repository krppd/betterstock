# Free edition

This repository is the free edition of BetterStock. It runs entirely on the
user's computer: no server, license or activation is required.

## What it includes

- Full point of sale: products, sales and cash register, split payments, customers,
  store credit (fiados), movements, stock counts, expirations, dead stock,
  statistics, CSV import, tickets and PDF, local backup and cash shifts.
- A single administrator user, created on the first run, who can change their own
  password.
- Movement filtering by reason, including the history of each stock count.
- Store-credit statement via WhatsApp, from Customer accounts.
- General settings, backups and cancellation codes.

## What it does not include

- Electronic invoicing (ARCA): there is no assistant, issuing, CAE or fiscal QR.
- Optional premium features. They are delivered as a plugin when a license is
  activated and are not part of this repository.

## Limits

There is no hard limit on products or imports. Statistics cover the last 12 months.

## Tests

```bash
python3 -m pytest tests/ -q -p no:randomly
```
