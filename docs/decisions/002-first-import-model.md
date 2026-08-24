# 002 — First persistent import model

## Context

TradeOps needs a durable representation of an international import before it
can relate that operation to partners, ports, products, costs, or inventory.

## Decision

Introduce the persistent Odoo model `trade.import` in `trade_import`. The
first version stores only an import number, date, external reference, state,
and notes. New records default to `New`, today's date, and `draft`.

The model declares the future lifecycle states but does not implement action
methods or transition rules yet.

## Consequences

The import domain can now create, search, and update records through the Odoo
ORM. Numbering remains intentionally generic because customers, financiers,
and ports do not exist yet. Workflow enforcement is deferred to Day 165, when
the necessary business rules are introduced.
