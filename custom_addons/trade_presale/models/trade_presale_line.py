import math

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TradePresaleLine(models.Model):
    _name = "trade.presale.line"
    _description = "Trade Presale Line"
    _inherit = "trade.child.mixin"
    _order = "id"
    _trade_parent_field = "presale_id"
    _trade_managed_fields = ("sale_line_ids", "uom_id")

    presale_id = fields.Many2one("trade.presale", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="presale_id.company_id", store=True, readonly=True, index=True)
    currency_id = fields.Many2one(related="presale_id.currency_id", store=True, readonly=True)
    import_line_id = fields.Many2one("trade.import.line", required=True, ondelete="restrict", check_company=True, index=True)
    product_id = fields.Many2one("product.product", required=True, check_company=True, readonly=True, ondelete="restrict")
    uom_id = fields.Many2one(related="import_line_id.uom_id", store=True, readonly=True)
    quantity = fields.Float(required=True, default=1, digits="Product Unit of Measure")
    unit_price = fields.Monetary(required=True, default=0)
    sale_line_ids = fields.One2many("sale.order.line", "trade_presale_line_id", readonly=True, copy=False)

    @api.onchange("import_line_id")
    def _onchange_import_line(self):
        self.product_id = self.import_line_id.product_id

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for original in vals_list:
            vals = dict(original)
            if not vals.get("import_line_id") and vals.get("product_id") and vals.get("presale_id"):
                presale = self.env["trade.presale"].browse(vals["presale_id"])
                matches = presale.import_id.line_ids.filtered(lambda line: line.product_id.id == vals["product_id"])
                if len(matches) != 1:
                    raise ValidationError(_("Select the exact import line; the product is absent or ambiguous."))
                vals["import_line_id"] = matches.id
            if vals.get("import_line_id"):
                source = self.env["trade.import.line"].browse(vals["import_line_id"])
                vals.setdefault("product_id", source.product_id.id)
            prepared.append(vals)
        return super().create(prepared)

    def write(self, vals):
        if vals.get("import_line_id"):
            source = self.env["trade.import.line"].browse(vals["import_line_id"])
            vals = dict(vals)
            vals.setdefault("product_id", source.product_id.id)
        return super().write(vals)

    @api.constrains("presale_id", "import_line_id", "product_id", "quantity", "unit_price")
    def _check_source(self):
        for line in self:
            if (line.import_line_id.import_id != line.presale_id.import_id
                    or line.import_line_id.product_id != line.product_id):
                raise ValidationError(_("The selected product and source line must belong to the presale import."))
            if not math.isfinite(line.quantity) or line.quantity <= 0:
                raise ValidationError(_("Presale quantity must be greater than zero."))
            if not math.isfinite(line.unit_price) or line.unit_price < 0:
                raise ValidationError(_("Presale price must be finite and non-negative."))
