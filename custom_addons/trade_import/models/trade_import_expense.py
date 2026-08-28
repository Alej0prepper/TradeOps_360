from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TradeImportExpense(models.Model):
    _name = "trade.import.expense"
    _description = "Trade Import Expense"
    _order = "id"

    import_id = fields.Many2one(
        comodel_name="trade.import",
        string="Import",
        required=True,
        ondelete="cascade",
    )
    expense_type = fields.Selection(
        selection=[
            ("freight", "Freight"),
            ("nationalization", "Nationalization"),
            ("transport", "Transport"),
            ("financing", "Financing"),
            ("other", "Other"),
        ],
        string="Expense Type",
        required=True,
    )
    amount = fields.Monetary(
        string="Amount",
        required=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="import_id.currency_id",
        store=True,
    )

    @api.constrains("amount")
    def _check_amount(self):
        for expense in self:
            if expense.amount < 0:
                raise ValidationError("Import expenses cannot be negative.")
