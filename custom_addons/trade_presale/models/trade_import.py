from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class TradeImport(models.Model):
    _inherit = "trade.import"

    presale_ids = fields.One2many("trade.presale", "import_id", copy=False, readonly=True)

    def action_cancel(self):
        if self.mapped("presale_ids").filtered(lambda record: record.state != "cancelled"):
            raise UserError(_("Cancel the import's open presales before cancelling the import."))
        return super().action_cancel()


class TradeImportLine(models.Model):
    _inherit = "trade.import.line"

    presale_line_ids = fields.One2many("trade.presale.line", "import_line_id", copy=False, readonly=True)
    committed_quantity = fields.Float(compute="_compute_commitments", store=True, digits="Product Unit of Measure")
    uncommitted_quantity = fields.Float(compute="_compute_commitments", store=True, digits="Product Unit of Measure")
    overcommitted = fields.Boolean(compute="_compute_commitments", store=True)

    @api.depends(
        "quantity", "presale_line_ids.quantity", "presale_line_ids.presale_id.state",
        "presale_line_ids.sale_line_ids.product_uom_qty", "presale_line_ids.sale_line_ids.product_uom",
        "presale_line_ids.sale_line_ids.order_id.state",
    )
    def _compute_commitments(self):
        for line in self:
            committed = 0.0
            for presale_line in line.presale_line_ids:
                state = presale_line.presale_id.state
                if state == "confirmed":
                    committed += presale_line.quantity
                elif state == "converted":
                    committed += sum(
                        sale.product_uom._compute_quantity(sale.product_uom_qty, line.uom_id)
                        for sale in presale_line.sale_line_ids if sale.order_id.state != "cancel"
                    )
            line.committed_quantity = committed
            line.uncommitted_quantity = line.quantity - committed
            line.overcommitted = bool(line.uom_id) and float_compare(
                committed, line.quantity, precision_rounding=line.uom_id.rounding,
            ) > 0

    def write(self, vals):
        if {"presale_line_ids", "committed_quantity", "uncommitted_quantity", "overcommitted"}.intersection(vals):
            raise UserError(_("Commercial commitment totals are derived, not entered manually."))
        if "product_id" in vals and any(line.presale_line_ids and line.product_id.id != vals["product_id"] for line in self):
            raise UserError(_("A product already referenced by a presale cannot be replaced."))
        return super().write(vals)
