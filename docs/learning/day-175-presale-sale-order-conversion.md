# Day 175 — Presale to standard sale order

## What changed

An eligible `trade.presale` can now be converted explicitly into a standard
Odoo `sale.order` quotation. Presale lines now include a unit price so the
conversion maps products, quantities, and prices into `sale.order.line`.

## Why

TradeOps owns import-specific presale rules, but Odoo Sales owns the standard
quotation, order, delivery, and invoice lifecycle. Creating a quotation only
after the commercial commitment is confirmed and its import is completed keeps
that boundary explicit.

## Odoo concepts learned

- `ensure_one()` makes the action's one-presale expectation explicit.
- `fields.Command.create()` creates related sale order lines through the ORM.
- A `Many2one` link preserves traceability from the presale to its quotation.
- Validation before creation and the existing link check make the action
  idempotent for ordinary repeated requests.
- Odoo's transaction handles quotation creation and the presale update as one
  business operation; the action does not issue a manual commit.

## Resulting behavior

The **Convert to Sale Order** button is available only on confirmed, unconverted
presales. The action rejects an incomplete import, an unconfirmed presale, or a
previously converted presale. On success it creates a standard quotation,
stores the link on the presale, and changes its status to **Converted**.
