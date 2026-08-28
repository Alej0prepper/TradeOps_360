# Day 162 — Computed fields and business constraints

## What changed

Imports now calculate their number of product lines and total expected
quantity. The model also rejects identical origin and destination ports, and
lines reject zero or negative quantities. The form receives an additional
warning while the user is selecting identical ports.

## Why

These values are consequences of the import lines and should not be entered
manually. Invalid routes and quantities violate business invariants regardless
of whether the record comes from a form, an import, an API, or Odoo shell.

## Odoo concepts learned

- `@api.depends` declares dependencies for computed fields.
- `store=True` persists `total_quantity` and makes it searchable.
- `@api.constrains` protects invariants on every ORM write.
- `@api.onchange` improves form feedback but is not a substitute for a
  constraint.

## Resulting behavior

`line_count` and `total_quantity` update when lines or their quantities change.
Saving an import with the same port at both ends raises `ValidationError`, as
does saving a line with a quantity less than or equal to zero.
