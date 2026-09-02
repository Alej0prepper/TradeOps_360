# 006 — Link presales to import lines

## Context

TradeOps needs to capture commercial commitments before imported goods arrive,
without duplicating Odoo's `sale.order` model or converting the commitment yet.

## Decision

Create a separate `trade_presale` addon with `trade.presale` and
`trade.presale.line`. A presale must reference one `trade.import`, and each
line must reference a product present on that import. The product domain
improves form selection, while an ORM constraint protects the invariant for
all ORM entry points. Presale lines use cascade deletion from their root;
imports use restrict deletion while a presale depends on them.

The addon declares `sale` as a dependency to make the future integration
explicit, but this milestone does not create or modify `sale.order` records.

## Consequences

Users can record draft, confirmed, or cancelled commitments against expected
imported products. Overpresale warnings, payments, and conversion to a sale
remain separate milestones.
