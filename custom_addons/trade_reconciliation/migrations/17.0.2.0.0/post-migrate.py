from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    statements = env["trade.reconciliation"].search([
        ("legacy_review_required", "=", True), ("state", "=", "confirmed"),
    ])
    for statement in statements:
        for line in statement.line_ids:
            sale = line.sale_line_id
            # Explicitly identified as migration-time snapshots, not invented
            # evidence of the amount originally approved in the old application.
            line._trade_internal_write({
                "snapshot_amount": sale.price_subtotal,
                "snapshot_quantity": sale.product_uom_qty,
                "snapshot_unit_price": sale.price_unit,
                "snapshot_product_name": sale.product_id.display_name,
                "snapshot_sale_reference": sale.order_id.name,
                "snapshot_uom_name": sale.product_uom.name,
            })
    env.flush_all()
