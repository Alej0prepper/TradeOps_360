# 001 — Initial addon module boundaries

## Context

TradeOps 360 will serve several business areas. Keeping all future work in one
large addon would couple unrelated domains and make later reuse difficult.

## Decision

Create two installable addons in Day 159:

- `trade_core` for shared TradeOps foundations, depending on Odoo's `base`,
  `contacts`, `product`, and `stock` modules.
- `trade_import` for the import domain, depending on `trade_core`.

Neither addon contains a business model in this milestone.

## Consequences

Future shared concepts such as ports, financiers, and common configuration can
be introduced in `trade_core`. Future independent domains, including presales,
can depend on `trade_core` without depending on import-specific behavior.

This introduces a small dependency graph now, but avoids creating a monolithic
TradeOps addon. Module boundaries will be reconsidered only when the business
domain requires them.
