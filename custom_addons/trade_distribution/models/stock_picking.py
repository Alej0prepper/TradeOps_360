from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        result = super()._action_done()
        orders = self.move_ids.sale_line_id.order_id | self.move_ids.origin_returned_move_id.sale_line_id.order_id
        # Only update existing operational records derived from these movements.
        distributions = self.env["trade.distribution"].sudo().search([("sale_order_id", "in", orders.ids)])
        distributions._sync_delivery_state()
        return result


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def write(self, vals):
        result = super().write(vals)
        if "product_uom_qty" in vals:
            distributions = self.env["trade.distribution"].sudo().search([("sale_order_id", "in", self.order_id.ids)])
            distributions._sync_delivery_state()
        return result
