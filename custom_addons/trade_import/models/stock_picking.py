from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        result = super()._action_done()
        operations = self.move_ids.purchase_line_id.trade_import_line_id.import_id
        # Inventory-only users can finish a receipt. The elevation is restricted
        # to recomputing existing imports linked to the just-completed moves.
        operations.sudo()._sync_receipt_state()
        return result
