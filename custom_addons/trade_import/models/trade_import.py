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
