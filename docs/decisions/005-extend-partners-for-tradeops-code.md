# 005 — Extend Odoo contacts with a TradeOps code

## Context

TradeOps needs a concise code for customers and financiers that can later be
used in business references. Odoo already owns these contacts through
`res.partner`, so a new customer or financier model would duplicate an
existing business concept.

## Decision

Extend `res.partner` with the optional `trade_code` field using `_inherit`.
Expose the field by inheriting the standard contact form and inserting it after
the VAT field with XPath. Do not override standard partner methods for this
addition.

## Consequences

All existing Odoo contact behavior remains available while TradeOps gains the
additional code on the same records. The code is not made mandatory or unique
until a later business rule requires those constraints. The contact form stays
connected to future changes in Odoo because TradeOps declares only its small
view extension instead of copying the complete standard view.
