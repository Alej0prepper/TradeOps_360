# TradeOps 360 — Vision

TradeOps 360 is a suite of custom Odoo 17 modules for commercial and import operations. The project will be built incrementally as part of an Odoo learning process.

## Main goal

Create a realistic business application while learning how to extend Odoo correctly.

## Final business flow

Import -> Products and Expenses -> Real Cost -> Reception -> Inventory -> Presale -> Sale -> Distribution -> Supplier Reconciliation

## Cross-cutting concerns

- Users
- Permissions
- Companies
- Warehouses
- Traceability
- Notifications
- Audit

## Architectural principle

TradeOps 360 must extend Odoo rather than rebuilding features already available in the ERP. Standard Odoo entities should be reused whenever possible. Custom models should represent business concepts genuinely specific to TradeOps.

## Incremental evolution

The repository is the course project itself, not a finished application used to illustrate the course. Every lesson must leave the project in a functional, coherent, and demonstrably improved state. The final code, documentation, and Git history should make its technical evolution understandable.
