from odoo import api, fields, models
from odoo.exceptions import ValidationError


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
    currency_id = fields.Many2one(
        related="import_id.currency_id",
        store=True,
    )
    unit_purchase_price = fields.Monetary(
        string="Unit Purchase Price",
        required=True,
        currency_field="currency_id",
    )
    purchase_subtotal = fields.Monetary(
        string="Purchase Subtotal",
        compute="_compute_purchase_subtotal",
        store=True,
        currency_field="currency_id",
    )
    allocated_expense = fields.Monetary(
        string="Allocated Import Expense",
        compute="_compute_landed_cost",
        store=True,
        currency_field="currency_id",
    )
    real_total_cost = fields.Monetary(
        string="Real Total Cost",
        compute="_compute_landed_cost",
        store=True,
        currency_field="currency_id",
    )
    real_unit_cost = fields.Monetary(
        string="Real Unit Cost",
        compute="_compute_landed_cost",
        store=True,
        currency_field="currency_id",
    )

    @api.depends("quantity", "unit_purchase_price")
    def _compute_purchase_subtotal(self):
        for line in self:
            line.purchase_subtotal = line.quantity * line.unit_purchase_price

    @api.depends(
        "purchase_subtotal",
        "import_id.purchase_total",
        "import_id.expense_total",
    )
    def _compute_landed_cost(self):
        for line in self:
            purchase_total = line.import_id.purchase_total
            if not purchase_total:
                line.allocated_expense = 0
                line.real_total_cost = line.purchase_subtotal
                line.real_unit_cost = (
                    line.real_total_cost / line.quantity if line.quantity else 0
                )
                continue

            proportion = line.purchase_subtotal / purchase_total
            line.allocated_expense = line.import_id.expense_total * proportion
            line.real_total_cost = (
                line.purchase_subtotal + line.allocated_expense
            )
            line.real_unit_cost = (
                line.real_total_cost / line.quantity if line.quantity else 0
            )

    @api.constrains("quantity")
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(
                    "Expected quantity must be greater than zero."
                )
