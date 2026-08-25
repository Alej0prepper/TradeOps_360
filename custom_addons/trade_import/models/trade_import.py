from odoo import fields, models


class TradeImport(models.Model):
    _name = "trade.import"
    _description = "Trade Import"
    _order = "id desc"

    name = fields.Char(
        string="Import Number",
        required=True,
        default="New",
    )
    import_date = fields.Date(
        string="Import Date",
        required=True,
        default=fields.Date.context_today,
    )
    reference = fields.Char(
        string="External Reference",
    )
    customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=True,
    )
    financier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Financier",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    origin_port_id = fields.Many2one(
        comodel_name="trade.port",
        string="Origin Port",
        required=True,
    )
    destination_port_id = fields.Many2one(
        comodel_name="trade.port",
        string="Destination Port",
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name="trade.import.line",
        inverse_name="import_id",
        string="Products",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("document_review", "Document Review"),
            ("validated", "Validated"),
            ("in_transit", "In Transit"),
            ("receiving", "Receiving"),
            ("partially_received", "Partially Received"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="draft",
    )
    notes = fields.Text(
        string="Notes",
    )
