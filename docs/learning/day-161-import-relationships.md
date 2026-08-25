# Day 161 — Import relationships

## What changed

Imports now relate to Odoo partners and companies, TradeOps ports, and product
lines. Ports are maintained as reusable TradeOps configuration.

## Why

An import cannot be operated as a useful business record when its customer,
company, journey, and expected products are disconnected text values.

## Odoo concepts learned

- `Many2one` connects an import or line to one related record.
- `One2many` exposes the lines whose inverse `Many2one` points to an import.
- `ondelete="cascade"` removes dependent lines with their import.
- Domains limit product selection to active Odoo products.

## Resulting behavior

An import requires a customer, company, origin port, and destination port.
It can contain multiple product lines, each with an expected quantity. A line
cannot exist without its import, and deleting an import removes its lines.
