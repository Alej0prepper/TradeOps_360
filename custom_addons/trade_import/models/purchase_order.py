from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    trade_import_id = fields.Many2one(
        "trade.import", copy=False, readonly=True, check_company=True,
        ondelete="restrict", index=True,
    )
    _sql_constraints = [
        ("trade_import_unique", "unique(trade_import_id)", "An import can have only one purchase document."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("trade_import_id"):
                operation = self.env["trade.import"].browse(vals["trade_import_id"])
                operation._trade_require_role("manager")
                operation._trade_lock()
                operation._trade_check_state("document_review")
        orders = super().create(vals_list)
        orders._check_trade_origin()
        return orders

    @api.constrains("trade_import_id", "partner_id", "company_id", "currency_id", "picking_type_id", "order_line")
    def _check_trade_origin(self):
        for order in self.filtered("trade_import_id"):
            operation = order.trade_import_id
            if (order.partner_id != operation.supplier_id or order.company_id != operation.company_id
                    or order.currency_id != operation.currency_id
                    or order.picking_type_id != operation.warehouse_id.in_type_id):
                raise ValidationError(_("Purchase header must match its TradeOps import."))
            lines = order.order_line.filtered(lambda line: not line.display_type)
            if set(lines.trade_import_line_id.ids) != set(operation.line_ids.ids) or len(lines) != len(operation.line_ids):
                raise ValidationError(_("Purchase lines must map exactly to the import lines."))

    def write(self, vals):
        if "trade_import_id" in vals and any(order.trade_import_id.id != vals["trade_import_id"] for order in self):
            raise UserError(_("A purchase's import provenance cannot be changed."))
        return super().write(vals)

    def button_cancel(self):
        if any(order.trade_import_id and order.trade_import_id.state != "cancelled" for order in self):
            raise UserError(_("Cancel the linked import first; received goods require returns."))
        return super().button_cancel()

    def button_draft(self):
        if self.filtered("trade_import_id"):
            raise UserError(_("A linked TradeOps purchase cannot be reset independently."))
        return super().button_draft()

    def unlink(self):
        if self.filtered("trade_import_id"):
            raise UserError(_("Retain linked purchase documents for traceability."))
        return super().unlink()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    trade_import_line_id = fields.Many2one(
        "trade.import.line", copy=False, readonly=True, check_company=True,
        ondelete="restrict", index=True,
    )
    _sql_constraints = [
        ("trade_import_line_unique", "unique(trade_import_line_id)", "An import line can have only one purchase line."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("trade_import_line_id"):
                source = self.env["trade.import.line"].browse(vals["trade_import_line_id"])
                source.import_id._trade_require_role("manager")
                source.import_id._trade_check_state("document_review")
        return super().create(vals_list)

    @api.constrains("trade_import_line_id", "order_id", "product_id", "product_qty", "product_uom", "price_unit", "display_type")
    def _check_trade_line(self):
        for line in self:
            source = line.trade_import_line_id
            if source:
                if (source.import_id != line.order_id.trade_import_id or line.product_id != source.product_id
                        or line.product_uom != source.uom_id or line.display_type
                        or float_compare(line.product_qty, source.quantity, precision_rounding=source.uom_id.rounding)
                        or line.currency_id.compare_amounts(line.price_unit, source.unit_purchase_price)):
                    raise ValidationError(_("The purchase line does not match its import source."))
            elif line.order_id.trade_import_id and not line.display_type:
                raise ValidationError(_("Every imported purchase line needs its source line."))

    def write(self, vals):
        if "trade_import_line_id" in vals and any(line.trade_import_line_id.id != vals["trade_import_line_id"] for line in self):
            raise UserError(_("A purchase line's import provenance cannot be changed."))
        return super().write(vals)

    def unlink(self):
        if self.filtered("trade_import_line_id"):
            raise UserError(_("Retain imported purchase lines for traceability."))
        return super().unlink()
