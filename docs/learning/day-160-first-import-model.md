# Day 160 — First import model

## What changed

`trade.import` is now a persistent Odoo model with a number, date, external
reference, lifecycle state, and notes.

## Why

TradeOps needs a real business record before it can add import relationships
and operational rules.

## Odoo concepts learned

- `models.Model` creates a persistent ORM-managed model.
- `_name` exposes the model as `env["trade.import"]`.
- Odoo fields describe stored values and their defaults.
- `create`, `search`, and `write` work with recordsets through the ORM.

## Resulting behavior

An import can be created without a date or state and begins today in `draft`.
It can be searched and updated through Odoo's ORM. The visible state choices
prepare the vocabulary for a later workflow; they do not yet enforce it.
