from odoo import api, fields, models
from odoo.exceptions import ValidationError


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
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
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
    expense_ids = fields.One2many(
        comodel_name="trade.import.expense",
        inverse_name="import_id",
        string="Import Expenses",
    )
    line_count = fields.Integer(
        string="Product Lines",
        compute="_compute_import_totals",
    )
    total_quantity = fields.Float(
        string="Total Expected Quantity",
        compute="_compute_import_totals",
        store=True,
    )
    purchase_total = fields.Monetary(
        string="Purchase Total",
        compute="_compute_cost_totals",
        store=True,
        currency_field="currency_id",
    )
    expense_total = fields.Monetary(
        string="Expense Total",
        compute="_compute_cost_totals",
        store=True,
        currency_field="currency_id",
    )
    landed_total = fields.Monetary(
        string="Landed Total",
        compute="_compute_cost_totals",
        store=True,
        currency_field="currency_id",
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

    @api.depends("line_ids", "line_ids.quantity")
    def _compute_import_totals(self):
        for trade_import in self:
            trade_import.line_count = len(trade_import.line_ids)
            trade_import.total_quantity = sum(
                trade_import.line_ids.mapped("quantity")
            )

    @api.depends("line_ids.purchase_subtotal", "expense_ids.amount")
    def _compute_cost_totals(self):
        for trade_import in self:
            trade_import.purchase_total = sum(
                trade_import.line_ids.mapped("purchase_subtotal")
            )
            trade_import.expense_total = sum(
                trade_import.expense_ids.mapped("amount")
            )
            trade_import.landed_total = (
                trade_import.purchase_total + trade_import.expense_total
            )

    @api.constrains("origin_port_id", "destination_port_id")
    def _check_ports(self):
        for trade_import in self:
            if (
                trade_import.origin_port_id
                and trade_import.destination_port_id
                and trade_import.origin_port_id == trade_import.destination_port_id
            ):
                raise ValidationError(
                    "Origin and destination ports must be different."
                )

    @api.onchange("origin_port_id", "destination_port_id")
    def _onchange_ports(self):
        if (
            self.origin_port_id
            and self.origin_port_id == self.destination_port_id
        ):
            return {
                "warning": {
                    "title": "Check the ports",
                    "message": (
                        "Origin and destination are currently the same."
                    ),
                }
            }
