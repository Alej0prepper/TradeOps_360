import math

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TradeImportLine(models.Model):
    _name = "trade.import.line"
    _description = "Trade Import Line"
    _inherit = "trade.child.mixin"
    _rec_name = "product_id"
    _order = "id"
    _trade_parent_field = "import_id"
    _trade_managed_fields = (
        "purchase_line_ids", "purchase_subtotal", "allocated_expense",
        "real_total_cost", "real_unit_cost", "received_quantity", "uom_id",
    )

    import_id = fields.Many2one("trade.import", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="import_id.company_id", store=True, readonly=True, index=True)
    currency_id = fields.Many2one(related="import_id.currency_id", store=True, readonly=True)
    product_id = fields.Many2one("product.product", required=True, check_company=True, ondelete="restrict", domain=[("active", "=", True)])
    uom_id = fields.Many2one(related="product_id.uom_id", store=True, readonly=True)
    quantity = fields.Float(required=True, default=1.0, digits="Product Unit of Measure")
    unit_purchase_price = fields.Monetary(required=True)
    purchase_subtotal = fields.Monetary(compute="_compute_purchase_subtotal", store=True)
    allocated_expense = fields.Monetary(compute="_compute_landed_cost", store=True)
    real_total_cost = fields.Monetary(compute="_compute_landed_cost", store=True)
    real_unit_cost = fields.Float(
        string="Operational Unit Cost", compute="_compute_landed_cost", store=True, digits=(16, 6),
    )
    purchase_line_ids = fields.One2many("purchase.order.line", "trade_import_line_id", readonly=True, copy=False)
    received_quantity = fields.Float(compute="_compute_received", digits="Product Unit of Measure")

    @api.depends("quantity", "unit_purchase_price", "currency_id")
    def _compute_purchase_subtotal(self):
        for line in self:
            currency = line.currency_id or self.env.company.currency_id
            line.purchase_subtotal = currency.round(line.quantity * line.unit_purchase_price)

    @api.depends("quantity", "import_id.line_ids.purchase_subtotal", "import_id.expense_ids.amount", "currency_id")
    def _compute_landed_cost(self):
        for line in self:
            allocated = 0.0
            operation = line.import_id
            currency = line.currency_id or self.env.company.currency_id
            total = sum(operation.line_ids.mapped("purchase_subtotal"))
            expense = currency.round(sum(operation.expense_ids.mapped("amount")))
            cumulative = previous = 0.0
            if total > 0:
                # Cumulative rounding allocates residual cents deterministically.
                for sibling in operation.line_ids:
                    cumulative += sibling.purchase_subtotal
                    rounded = currency.round(expense * cumulative / total)
                    if sibling == line:
                        allocated = currency.round(rounded - previous)
                        break
                    previous = rounded
            line.allocated_expense = allocated
            line.real_total_cost = currency.round(line.purchase_subtotal + allocated)
            # Unit ratios need more precision than rounded document totals.
            line.real_unit_cost = line.real_total_cost / line.quantity if line.quantity else 0.0

    @api.depends("purchase_line_ids.qty_received", "purchase_line_ids.product_uom", "uom_id")
    def _compute_received(self):
        for line in self:
            line.received_quantity = sum(
                purchase.product_uom._compute_quantity(purchase.qty_received, line.uom_id)
                for purchase in line.purchase_line_ids
            )

    @api.constrains("quantity", "unit_purchase_price")
    def _check_values(self):
        for line in self:
            if not math.isfinite(line.quantity) or line.quantity <= 0:
                raise ValidationError(_("Expected quantity must be greater than zero."))
            if not math.isfinite(line.unit_purchase_price) or line.unit_purchase_price < 0:
                raise ValidationError(_("Purchase price cannot be negative or non-finite."))
