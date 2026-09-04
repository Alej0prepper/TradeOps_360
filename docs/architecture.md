# TradeOps 360 — Architecture

## Runtime

TradeOps executes inside Odoo 17.

```text
User
  -> Odoo Web Client
  -> Odoo Server
  -> Models / Business Logic
  -> Odoo ORM
  -> PostgreSQL
```

TradeOps is not an independent backend. Its modules will live inside the Odoo server and reuse Odoo's standard capabilities.

## Standard models

TradeOps will reuse:

- `res.partner` for customers, suppliers, and financiers
- `res.users` for users
- `res.company` for companies
- `product.product` for products
- `stock.warehouse` for warehouses
- `sale.order` for sales
- `stock.picking` for inventory operations

When TradeOps needs additional behavior or information on one of these concepts, it should extend the corresponding standard model (for example, with `_inherit`) rather than create a duplicate model.

## Custom domains

TradeOps-specific domains will include Imports, Presales, Distribution, and Supplier Reconciliation.

The current custom models are `trade.port` for the TradeOps port catalog and
`trade.import` with its `trade.import.line` children for the import domain.
`res.partner` is extended with the optional `trade_code` field; no separate
TradeOps customer model exists. Other custom models must represent genuine
TradeOps domain concepts and be introduced only when their lesson creates the
architectural need.

## ORM policy

Business logic should normally use the Odoo ORM. Direct SQL is not the normal mechanism for business operations because it can bypass permissions, record rules, computed fields, tracking, cache, automations, and Python business logic. Any direct SQL requires explicit technical justification.

## Multi-company and warehouses

The project must remain compatible with multiple Odoo companies and multiple warehouses. Business logic must never assume that there is only one company, and a company and warehouse must not be treated as equivalent concepts.

## Security

Security will progressively include groups, ACLs, record rules, company restrictions, and warehouse restrictions. These controls will be added when their corresponding lessons introduce the business requirements.

## Traceability

Important business operations must eventually preserve what happened, who performed it, when it happened, which company was involved, and which business object was affected.

## Extension policy

Before creating a new model:

1. Check whether Odoo already models the concept.
2. Identify the responsible Odoo module.
3. Prefer extending the existing model.
4. Create a TradeOps model only for a custom domain concept.

## Module boundaries

`trade_core` provides the shared TradeOps foundation and depends on the
standard Contacts, Product, and Inventory capabilities. `trade_import`
contains the import domain boundary and depends on `trade_core`.
`trade_presale` contains import-linked commercial commitments and depends on
`trade_import` and the standard `sale` module. It converts an eligible
confirmed presale into a standard `sale.order` quotation; it does not duplicate
the Sales workflow.

Potential modules such as `trade_distribution` and `trade_reconciliation` will
be created only when there is a concrete architectural reason to separate
responsibilities. No business model is part of `trade_core`, which currently
owns `trade.port`; `trade_import` owns `trade.import` and its import children;
and `trade_presale` owns `trade.presale` and `trade.presale.line`.

## User interface

`trade_core` extends the standard contact form through view inheritance and
XPath so that `trade_code` appears without copying Odoo's view. `trade_import`
provides the import list and form views, plus the TradeOps > Imports action and
menu. `trade_presale` provides the TradeOps > Presales action and form. Access
controls are deliberately not part of these modules yet; they will be
introduced with the corresponding security milestone.
