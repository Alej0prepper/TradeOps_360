# Changelog

All notable changes to TradeOps 360 are documented in this file.

The project follows the principles of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) once released versions exist.

## [Unreleased]

### Added

- Established the Day 157 architecture baseline: project vision, architecture contract, roadmap, decision log, learning log, and the empty custom addons directory.
- TradeOps gained its first installable boundaries: `trade_core` now gathers the standard Odoo capabilities shared by the suite, while `trade_import` opens a separate home for import operations before any business records exist.
- Imports can now be persisted through the Odoo ORM. A new record begins as `New` and `Draft`, receives today's date automatically, and can retain its external reference and operational notes while later classes add its relationships and workflow.
- An import stopped being an isolated note and became a connected operation: it now belongs to a customer and company, can name a financier, travels between configured ports, and gathers product lines without duplicating Odoo's partners or products.
- Trade imports now expose computed line and quantity totals and enforce valid routes and positive expected quantities.
- Imports now calculate landed costs by allocating registered expenses in
  proportion to each product line's purchase value.
- TradeOps now extends Odoo contacts with a reusable business code and exposes
  import operations through the TradeOps menu, a list view, and a form that
  includes product and expense lines.
- TradeOps now captures presales linked to imports. Presale product selectors
  are limited to products in the selected import, and ORM constraints reject
  invalid products and non-positive quantities while preserving the future
  integration point with Odoo Sales.
- A confirmed presale for a completed import can now create one standard Odoo
  quotation. TradeOps maps its customer, company, products, quantities, and
  unit prices into `sale.order`, retains the resulting quotation link, and
  marks the presale as converted so a repeated conversion cannot create a
  duplicate sale.

## [0.0.0] - 2026-08-21

### Added

- Initialized the TradeOps 360 repository and its initial documentation baseline.
