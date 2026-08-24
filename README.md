# TradeOps 360

TradeOps 360 is an educational and practical Odoo 17 project focused on commercial and import operations.

The application is built incrementally throughout an Odoo learning course. Each lesson introduces or improves a real part of the same system.

The final objective is to produce both:

1. A functional TradeOps 360 application.
2. An explanatory reference project showing how an Odoo application evolves from architecture to production.

## Current state

Day 160 — first import model.

`trade_core` provides the shared TradeOps foundation. `trade_import` now
contains `trade.import`, the first persistent business model. It records an
import number, date, external reference, state, and notes through the Odoo ORM.

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

## Next step

Day 161 — add relationships and configurable data to imports.
