# Day 172 — Import-linked presales

## What changed

TradeOps now provides a `trade_presale` addon with `trade.presale` and
`trade.presale.line`. Each presale requires an Odoo customer, company, and
import, and has draft, confirmed, and cancelled states. Its lines contain a
product and a positive quantity.

## Why

Commercial teams need to commit expected imported goods before reception,
without creating a definitive Odoo sale prematurely.

## Odoo concepts learned

- `ondelete="restrict"` protects the import context while a presale exists.
- Relational domains narrow product selection in the form.
- `@api.constrains` enforces relational invariants outside the user interface.
- A custom aggregate can remain separate from standard `sale.order` until a
  later conversion workflow.

## Resulting behavior

Users can open TradeOps > Presales and create import-linked presales. A line
for a product absent from the selected import, or with a non-positive
quantity, raises `ValidationError`. The addon does not implement overpresale
calculation, payments, or conversion to `sale.order`.
