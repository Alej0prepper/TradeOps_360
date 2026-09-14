import math

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    trade_presale_id = fields.Many2one(
        "trade.presale", readonly=True, copy=False, check_company=True,
        ondelete="restrict", index=True,
    )
    trade_import_id = fields.Many2one(related="trade_presale_id.import_id", store=True, readonly=True)
    _sql_constraints = [
        ("trade_presale_unique", "unique(trade_presale_id)", "A presale can generate only one quotation."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("trade_import_id"):
                raise ValidationError(_("The import is derived from the presale."))
            if vals.get("trade_presale_id"):
                presale = self.env["trade.presale"].browse(vals["trade_presale_id"])
                presale._trade_require_role()
                presale._trade_lock()
                presale._trade_check_state("confirmed")
                presale._check_ready()
                if presale.import_id.state != "completed":
                    raise UserError(_("The import must be fully received."))
        orders = super().create(vals_list)
        for order in orders.filtered("trade_presale_id"):
            lines = order.order_line.filtered(lambda line: not line.display_type)
            sources = order.trade_presale_id.line_ids
            if set(lines.trade_presale_line_id.ids) != set(sources.ids) or len(lines) != len(sources):
                raise ValidationError(_("The quotation must contain every presale line exactly once."))
            for line in lines:
                source = line.trade_presale_line_id
                if (float_compare(line.product_uom_qty, source.quantity, precision_rounding=source.uom_id.rounding)
                        or line.currency_id.compare_amounts(line.price_unit, source.unit_price)):
                    raise ValidationError(_("Initial quotation quantities and prices must match the confirmed presale."))
        return orders

    @api.constrains("trade_presale_id", "company_id", "partner_id", "pricelist_id", "warehouse_id", "currency_id")
    def _check_trade_origin(self):
        for order in self.filtered("trade_presale_id"):
            presale = order.trade_presale_id
            if (order.company_id != presale.company_id or order.partner_id != presale.customer_id
                    or order.currency_id != presale.currency_id
                    or order.warehouse_id != presale.import_id.warehouse_id):
                raise ValidationError(_("The quotation must preserve its presale company, customer, currency and warehouse."))

    def write(self, vals):
        if "trade_import_id" in vals:
            raise UserError(_("The import is derived from the presale."))
        if "trade_presale_id" in vals and any(order.trade_presale_id.id != vals["trade_presale_id"] for order in self):
            raise UserError(_("Quotation provenance cannot be changed."))
        return super().write(vals)

    def unlink(self):
        if self.filtered("trade_presale_id"):
            raise UserError(_("Cancel linked quotations instead of deleting their traceability."))
        return super().unlink()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    trade_presale_line_id = fields.Many2one(
        "trade.presale.line", readonly=True, copy=False, check_company=True,
        ondelete="restrict", index=True,
    )
    _sql_constraints = [
        ("trade_presale_line_unique", "unique(trade_presale_line_id)", "A presale line can generate only one sale line."),
    ]

    @api.constrains("trade_presale_line_id", "order_id", "product_id", "product_uom", "product_uom_qty", "price_unit", "display_type")
    def _check_trade_source(self):
        for line in self:
            source = line.trade_presale_line_id
            if source:
                if (source.presale_id != line.order_id.trade_presale_id or line.product_id != source.product_id
                        or line.product_uom != source.uom_id or line.display_type):
                    raise ValidationError(_("The sale line must preserve its presale product and unit."))
                if not math.isfinite(line.product_uom_qty) or line.product_uom_qty <= 0:
                    raise ValidationError(_("A TradeOps sale quantity must be positive and finite."))
                if not math.isfinite(line.price_unit) or line.price_unit < 0:
                    raise ValidationError(_("A TradeOps sale price must be non-negative and finite."))
            elif line.order_id.trade_presale_id and not line.display_type:
                raise ValidationError(_("Product lines on this quotation need a presale source."))

    def write(self, vals):
        if "trade_presale_line_id" in vals and any(line.trade_presale_line_id.id != vals["trade_presale_line_id"] for line in self):
            raise UserError(_("A sale line's presale provenance cannot be changed."))
        return super().write(vals)

    def unlink(self):
        if self.filtered("trade_presale_line_id"):
            raise UserError(_("Retain generated sale lines; cancel the quotation when necessary."))
        return super().unlink()
