from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TradePresaleLine(models.Model):
    _name = "trade.presale.line"
    _description = "Trade Presale Line"
    _order = "id"

    presale_id = fields.Many2one(
        comodel_name="trade.presale",
        string="Presale",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
        domain="[('id', 'in', presale_id.allowed_product_ids)]",
    )
    quantity = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
    )
    unit_price = fields.Float(
        string="Unit Price",
        required=True,
        default=0.0,
    )

    @api.constrains("presale_id", "product_id")
    def _check_product_belongs_to_import(self):
        for line in self:
            import_products = (
                line.presale_id.import_id.line_ids.mapped("product_id")
            )
            if line.product_id and line.product_id not in import_products:
                raise ValidationError(
                    "The selected product does not belong to the presale import."
                )

    @api.constrains("quantity")
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(
                    "Presale quantity must be greater than zero."
                )
