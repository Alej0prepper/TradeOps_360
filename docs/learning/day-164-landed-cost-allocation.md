# Day 164 — Import expenses and landed cost allocation

## What changed

Imports now hold a currency, product purchase prices, and reusable expense
records. They calculate purchase, expense, and landed totals. Each product line
calculates its purchase subtotal, allocated expense, real total cost, and real
unit cost.

## Why

Supplier price alone is not the cost of an imported item. Freight,
nationalization, transport, and similar costs must be included before later
inventory and profitability work can rely on the amount.

## Odoo concepts learned

- `fields.Monetary` uses an explicit currency field for monetary values.
- Stored computed fields propagate cost changes through import relationships.
- A separate expense model represents a variable number of expense entries.
- Constraints prevent negative expense amounts from entering the model.

## Resulting behavior

The expense total is distributed to product lines according to their share of
the total purchase value. A line that represents 80% of the purchased value is
assigned 80% of the import expenses. Lines with no import expenses retain their
purchase cost as their real cost.
