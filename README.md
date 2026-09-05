# TradeOps 360

TradeOps 360 is an educational and practical Odoo 17 project focused on commercial and import operations.

The application is built incrementally throughout an Odoo learning course. Each lesson introduces or improves a real part of the same system.

The final objective is to produce both:

1. A functional TradeOps 360 application.
2. An explanatory reference project showing how an Odoo application evolves from architecture to production.

## Current state

`trade_core` now provides a configurable port catalog. `trade_import` connects
each import with Odoo customers, financiers, companies, active products, and
its origin and destination ports. Imports calculate line and quantity totals,
enforce valid routes and quantities, and distribute import expenses
proportionally to purchase value to determine each product's landed cost.
`trade_presale` now records commercial commitments linked to imports, restricts
their lines to products present in the selected import, and converts eligible
confirmed presales into standard Odoo quotations with a traceable link.

TradeOps extends Odoo contacts with an optional business code instead of
duplicating customers or financiers. Administrators can manage that code from
the standard contact form, and can manage imports through TradeOps > Imports.
The import lifecycle states are defined as shared vocabulary, but transitions
between them are not yet enforced. The project currently has no TradeOps
access-control configuration, reception or inventory workflow, oversell
monitoring, presale payments, distribution,
supplier reconciliation, API, reports, or automated test suite.

## Core principle

Extend Odoo instead of rebuilding functionality already provided by the ERP.

## Final business flow

Import -> Reception -> Inventory -> Presale -> Sale -> Distribution -> Reconciliation

## Documentation

- [Vision](docs/vision.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Architectural decisions](docs/decisions/README.md)
- [Learning milestones](docs/learning/README.md)

## Remaining work

The remaining work includes the import workflow and its valid state
transitions, access controls and multi-company restrictions, reception and
inventory, presales and sales, distribution, supplier reconciliation,
integrations and reports, testing, and deployment.
