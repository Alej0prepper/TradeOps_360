# 003 — Configurable port catalog

## Context

Imports must identify their origin and destination consistently. Free-text
ports would allow spelling variants and could not safely support the import
numbering planned for a later milestone.

## Decision

Create `trade.port` in `trade_core` with a name, code, and active flag.
`trade.import` references origin and destination ports through `Many2one`
fields.

## Consequences

Ports become reusable configuration shared by present and future TradeOps
domains. Their codes are ready for later numbering logic without inventing
that identifier early. This milestone intentionally does not prevent an
origin and destination from being the same; Day 162 will introduce that
business constraint.
