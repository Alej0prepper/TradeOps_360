from odoo import api, fields, models
from odoo.exceptions import UserError


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
            ("converted", "Converted"),
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
    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        readonly=True,
        copy=False,
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

    def action_convert_to_sale(self):
        self.ensure_one()

        if self.state != "confirmed":
            raise UserError("Only confirmed presales can be converted.")

        if self.import_id.state != "completed":
            raise UserError(
                "The import must be completed before creating the sale order."
            )

        if self.sale_order_id:
            raise UserError("This presale has already been converted.")

        order_lines = [
            fields.Command.create(
                {
                    "product_id": line.product_id.id,
                    "product_uom_qty": line.quantity,
                    "price_unit": line.unit_price,
                }
            )
            for line in self.line_ids
        ]
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer_id.id,
                "company_id": self.company_id.id,
                "order_line": order_lines,
            }
        )

        self.write(
            {
                "sale_order_id": sale_order.id,
                "state": "converted",
            }
        )

        return sale_order
