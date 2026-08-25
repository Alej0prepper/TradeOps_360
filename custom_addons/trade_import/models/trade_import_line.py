from odoo import fields, models


class TradeImportLine(models.Model):
    _name = "trade.import.line"
    _description = "Trade Import Line"
    _order = "id"

    import_id = fields.Many2one(
        comodel_name="trade.import",
        string="Import",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
        domain=[("active", "=", True)],
    )
    quantity = fields.Float(
        string="Expected Quantity",
        required=True,
        default=1.0,
    )
