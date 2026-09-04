# 007 — Convert eligible presales into standard sale orders

## Context

TradeOps presales capture import-specific commercial commitments, but Odoo
Sales already owns quotations, sales orders, deliveries, and invoices.

## Decision

Keep `trade.presale` as the custom commercial commitment and add an explicit
conversion action. The action is available only for a confirmed presale whose
import is completed. It creates a standard `sale.order` quotation through the
Odoo ORM, mapping the customer, company, product, quantity, and unit price.

`trade.presale.sale_order_id` records the resulting quotation. The action
rejects a presale that already has that link and then changes the presale state
to `converted`, preventing duplicate conversions. The quotation remains in
Odoo Sales' normal workflow; TradeOps does not confirm it or create custom
delivery or invoice records.

## Consequences

The import-to-presale flow now hands off to standard Odoo Sales while retaining
the origin of the quotation. The conversion and presale update remain part of
the same ORM transaction, so a failed quotation creation does not leave the
presale marked as converted.
