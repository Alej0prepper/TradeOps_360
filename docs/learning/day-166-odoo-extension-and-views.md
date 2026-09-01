# Day 166 — Extend Odoo models and expose import views

## What changed

`trade_core` now extends Odoo's `res.partner` model with an optional
`trade_code`. The field is added to the standard contact form through view
inheritance and XPath. `trade_import` now supplies a list and form view for
imports, an action, and the TradeOps > Imports menu.

## Why

Customers and financiers already exist in Odoo as contacts, so TradeOps needs
to add its business-specific code to `res.partner` rather than duplicate that
model. Import records also need an observable interface so users can create,
review, and update the import, its products, and its expenses.

## Odoo concepts learned

- `_inherit` adds fields to an existing Odoo model without creating a new
  model.
- View inheritance and XPath add one field to the standard contact form
  without copying it.
- XML list and form views determine how the same import records are presented.
- An `ir.actions.act_window` and menu item provide the navigation path from
  TradeOps to import records.
- `super()` remains the pattern for a future method override that preserves
  inherited behavior; this milestone does not override a standard method.

## Resulting behavior

Users with Odoo administrative access can save a TradeOps code on any contact.
They can open TradeOps > Imports to manage import headers, product lines, and
expense lines from a list and form interface. Access rights are not introduced
by this milestone, so normal-user access remains the responsibility of the
upcoming security work.
