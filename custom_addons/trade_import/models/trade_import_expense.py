import math

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TradeImportExpense(models.Model):
    _name = "trade.import.expense"
    _description = "Trade Import Expense"
    _inherit = "trade.child.mixin"
    _order = "id"
    _trade_parent_field = "import_id"

    import_id = fields.Many2one("trade.import", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="import_id.company_id", store=True, readonly=True, index=True)
    currency_id = fields.Many2one(related="import_id.currency_id", store=True, readonly=True)
    expense_type = fields.Selection([
        ("freight", "Freight"), ("nationalization", "Nationalization"),
        ("transport", "Transport"), ("financing", "Financing"), ("other", "Other"),
    ], required=True)
    amount = fields.Monetary(required=True)

    @api.constrains("amount")
    def _check_amount(self):
        if any(not math.isfinite(expense.amount) or expense.amount < 0 for expense in self):
            raise ValidationError(_("Import expenses must be finite and non-negative."))
