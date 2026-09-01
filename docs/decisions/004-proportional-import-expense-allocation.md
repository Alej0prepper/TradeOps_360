# 004 — Allocate import expenses by purchase value

## Context

An imported product's supplier price does not include the costs required to
bring it into the business, such as freight, nationalization, or transport.
TradeOps needs a reproducible landed cost before inventory and profitability
milestones use that value.

## Decision

Model additional costs as `trade.import.expense` records related to an import.
Allocate their total to each import line in proportion to that line's purchase
subtotal. The line's real total cost is its purchase subtotal plus its assigned
expense, and its real unit cost divides that result by quantity.

## Consequences

New expense categories can be added as records without adding a database field
for every cost type. The allocation is transparent and recalculates whenever
purchase values or expenses change. Currency rounding residual allocation is
intentionally deferred until the calculation becomes financially definitive.
