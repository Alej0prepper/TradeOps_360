from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TradeReconciliation(models.Model):
    _name = "trade.reconciliation"
    _description = "Trade Supplier Reconciliation"
    _order = "id desc"

    name = fields.Char(
        string="Reconciliation Number",
        required=True,
        default="New",
    )
    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        required=True,
        domain="[('supplier_rank', '>', 0)]",
        ondelete="restrict",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    reconciliation_date = fields.Date(
        string="Reconciliation Date",
        required=True,
        default=fields.Date.context_today,
    )
    line_ids = fields.One2many(
        comodel_name="trade.reconciliation.line",
        inverse_name="reconciliation_id",
        string="Sales",
    )
    total_amount = fields.Monetary(
        string="Total",
        compute="_compute_total_amount",
        store=True,
        currency_field="currency_id",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
        ],
        string="Status",
        required=True,
        default="draft",
    )

    @api.depends("line_ids.amount")
    def _compute_total_amount(self):
        for reconciliation in self:
            reconciliation.total_amount = sum(
                reconciliation.line_ids.mapped("amount")
            )

    def action_reconcile(self):
        self.ensure_one()

        if self.state != "draft":
            raise ValidationError("Only draft reconciliations can be confirmed.")
        if not self.line_ids:
            raise ValidationError("There are no sales to reconcile.")

        self.line_ids._check_reconcilable_sale_lines()
        self.write({"state": "confirmed"})


class TradeReconciliationLine(models.Model):
    _name = "trade.reconciliation.line"
    _description = "Trade Reconciliation Sale"
    _order = "id"

    reconciliation_id = fields.Many2one(
        comodel_name="trade.reconciliation",
        string="Reconciliation",
        required=True,
        ondelete="cascade",
    )
    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Sale Line",
        required=True,
        ondelete="restrict",
    )
    currency_id = fields.Many2one(
        related="reconciliation_id.currency_id",
        store=True,
        readonly=True,
    )
    amount = fields.Monetary(
        string="Amount",
        related="sale_line_id.price_subtotal",
        currency_field="currency_id",
        readonly=True,
    )

    _sql_constraints = [
        (
            "trade_reconciliation_sale_line_unique",
            "unique(sale_line_id)",
            "A sale line can only belong to one reconciliation.",
        ),
    ]

    @api.constrains(
        "reconciliation_id",
        "sale_line_id",
    )
    def _check_reconcilable_sale_lines(self):
        for line in self:
            sale_line = line.sale_line_id
            reconciliation = line.reconciliation_id
            if sale_line.order_id.state != "sale":
                raise ValidationError(
                    "Only confirmed sale order lines can be reconciled."
                )
            if sale_line.company_id != reconciliation.company_id:
                raise ValidationError(
                    "The sale line company must match the reconciliation company."
                )
            if sale_line.currency_id != reconciliation.currency_id:
                raise ValidationError(
                    "The sale line currency must match the reconciliation currency."
                )

    @api.constrains("sale_line_id")
    def _check_sale_line_is_available(self):
        for line in self:
            duplicate = self.search(
                [
                    ("sale_line_id", "=", line.sale_line_id.id),
                    ("id", "!=", line.id),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    "This sale line has already been reconciled."
                )
