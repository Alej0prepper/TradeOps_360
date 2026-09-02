from odoo import api, fields, models


class TradePresale(models.Model):
    _name = "trade.presale"
    _description = "Trade Presale"
    _order = "id desc"

    name = fields.Char(
        string="Presale Number",
        required=True,
        default="New",
    )
    import_id = fields.Many2one(
        comodel_name="trade.import",
        string="Import",
        required=True,
        ondelete="restrict",
    )
    customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="draft",
    )
    line_ids = fields.One2many(
        comodel_name="trade.presale.line",
        inverse_name="presale_id",
        string="Products",
    )

    allowed_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Import Products",
        compute="_compute_allowed_products",
    )

    @api.depends("import_id", "import_id.line_ids.product_id")
    def _compute_allowed_products(self):
        for presale in self:
            presale.allowed_product_ids = (
                presale.import_id.line_ids.mapped("product_id")
            )
