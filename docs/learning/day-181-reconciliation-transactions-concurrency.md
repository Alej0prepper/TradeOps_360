# Day 181 — Supplier reconciliation, transactions, and concurrency

## What changed

`trade_reconciliation` adds draft and confirmed supplier reconciliations.
Each reconciliation groups confirmed Odoo sale lines from one company and one
currency, and derives its total from those lines.

## Why

A sale line must not be processed by two reconciliations. A Python validation
provides a useful ordinary error, while the database unique constraint is the
final guarantee if concurrent requests reach the write at the same time.

## Odoo concepts learned

- `Many2one` and `One2many` model the reconciliation and its sales.
- `_sql_constraints` keeps the critical uniqueness invariant in PostgreSQL.
- Odoo's request transaction keeps reconciliation confirmation atomic; the
  business action does not call `env.cr.commit()`.
- `ondelete="cascade"` frees related sale lines when a reconciliation is
  deleted, avoiding orphaned processed markers.

## Resulting behavior

Users can add confirmed sale lines to a draft reconciliation and confirm it.
Empty reconciliations, unconfirmed sales, company or currency mismatches, and
already-associated sale lines are rejected. The test suite covers successful
confirmation, duplicate-line rejection, and a failed empty confirmation.
