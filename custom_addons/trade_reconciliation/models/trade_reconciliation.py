from psycopg2.errors import UniqueViolation

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import SQL


class TradeReconciliation(models.Model):
    _name = "trade.reconciliation"
    _description = "Trade Supplier Commercial Reconciliation"
    _inherit = ["trade.document.mixin", "mail.thread"]
    _order = "id desc"
    _trade_managed_fields = (
        "total_amount", "adjustment_total", "net_total", "adjustment_ids",
        "confirmed_at", "confirmed_by_id", "legacy_review_required",
    )

    supplier_id = fields.Many2one("res.partner", required=True, check_company=True, ondelete="restrict", domain=[("supplier_rank", ">", 0)])
    reconciliation_date = fields.Date(required=True, default=fields.Date.context_today)
    line_ids = fields.One2many("trade.reconciliation.line", "reconciliation_id", string="Confirmed Sales", copy=False)
    adjustment_ids = fields.One2many("trade.reconciliation.adjustment", "reconciliation_id", readonly=True, copy=False)
    total_amount = fields.Monetary(string="Confirmed Sales Subtotal", compute="_compute_totals", store=True)
    adjustment_total = fields.Monetary(compute="_compute_totals", store=True)
    net_total = fields.Monetary(string="Adjusted Commercial Total", compute="_compute_totals", store=True)
    state = fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed")], required=True, default="draft", readonly=True, copy=False, tracking=True)
    confirmed_at = fields.Datetime(readonly=True, copy=False)
    confirmed_by_id = fields.Many2one("res.users", readonly=True, copy=False, ondelete="restrict")
    legacy_review_required = fields.Boolean(readonly=True, copy=False)

    @api.depends("line_ids.amount", "adjustment_ids.amount")
    def _compute_totals(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped("amount"))
            record.adjustment_total = sum(record.adjustment_ids.mapped("amount"))
            record.net_total = record.total_amount + record.adjustment_total

    @api.constrains("supplier_id", "line_ids", "company_id")
    def _trade_check_invariants(self):
        self.mapped("line_ids")._check_reconcilable_sale_lines()
        return True

    def action_reconcile(self):
        self.ensure_one()
        self._trade_require_role("manager")
        self._trade_lock()
        self._trade_check_state("draft")
        if self.legacy_review_required:
            raise UserError(_("Review the provenance of this migrated reconciliation first."))
        if not self.line_ids:
            raise ValidationError(_("There are no sales to reconcile."))
        self.line_ids._lock_sources()
        self.line_ids._check_reconcilable_sale_lines()
        for line in self.line_ids:
            sale = line.sale_line_id
            line._trade_internal_write({
                "snapshot_amount": sale.price_subtotal,
                "snapshot_quantity": sale.product_uom_qty,
                "snapshot_unit_price": sale.price_unit,
                "snapshot_product_name": sale.product_id.display_name,
                "snapshot_sale_reference": sale.order_id.name,
                "snapshot_uom_name": sale.product_uom.name,
            })
        self._trade_internal_write({
            "state": "confirmed", "confirmed_at": fields.Datetime.now(), "confirmed_by_id": self.env.user.id,
        })
        self.message_post(body=_("Commercial reconciliation confirmed. Values are frozen; subsequent corrections require separate adjustments."))
        return True

    def action_add_adjustment(self):
        self.ensure_one()
        self._trade_require_role("manager")
        self.check_access_rights("write")
        self.check_access_rule("write")
        self._trade_check_state("confirmed")
        return {"type": "ir.actions.act_window", "res_model": "trade.reconciliation.adjustment.wizard",
                "view_mode": "form", "target": "new", "context": {"default_reconciliation_id": self.id}}


class TradeReconciliationLine(models.Model):
    _name = "trade.reconciliation.line"
    _description = "Commercial Reconciliation Sale"
    _inherit = "trade.child.mixin"
    _order = "id"
    _trade_parent_field = "reconciliation_id"
    _trade_managed_fields = (
        "amount", "snapshot_amount", "snapshot_quantity", "snapshot_unit_price",
        "snapshot_product_name", "snapshot_sale_reference", "snapshot_uom_name",
    )

    reconciliation_id = fields.Many2one("trade.reconciliation", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="reconciliation_id.company_id", store=True, readonly=True, index=True)
    currency_id = fields.Many2one(related="reconciliation_id.currency_id", store=True, readonly=True)
    sale_line_id = fields.Many2one("sale.order.line", required=True, check_company=True, ondelete="restrict", index=True)
    amount = fields.Monetary(compute="_compute_amount", store=True)
    snapshot_amount = fields.Monetary(readonly=True, copy=False)
    snapshot_quantity = fields.Float(readonly=True, copy=False, digits="Product Unit of Measure")
    snapshot_unit_price = fields.Float(readonly=True, copy=False, digits="Product Price")
    snapshot_product_name = fields.Char(readonly=True, copy=False)
    snapshot_sale_reference = fields.Char(readonly=True, copy=False)
    snapshot_uom_name = fields.Char(readonly=True, copy=False)

    _sql_constraints = [
        ("trade_reconciliation_sale_line_unique", "unique(sale_line_id)", "A sale line can only belong to one reconciliation."),
    ]

    @api.depends("sale_line_id.price_subtotal", "reconciliation_id.state", "snapshot_amount")
    def _compute_amount(self):
        for line in self:
            line.amount = line.snapshot_amount if line.reconciliation_id.state == "confirmed" else line.sale_line_id.price_subtotal

    @api.model_create_multi
    def create(self, vals_list):
        source_ids = [vals["sale_line_id"] for vals in vals_list if vals.get("sale_line_id")]
        if len(source_ids) != len(set(source_ids)) or self.search_count([("sale_line_id", "in", source_ids)]):
            raise ValidationError(_("A selected sale line already belongs to a reconciliation."))
        try:
            with self.env.cr.savepoint():
                return super().create(vals_list)
        except UniqueViolation as error:
            if error.diag.constraint_name.endswith("trade_reconciliation_sale_line_unique"):
                raise ValidationError(_("A selected sale line was reconciled by another operation.")) from error
            raise

    def write(self, vals):
        try:
            with self.env.cr.savepoint():
                return super().write(vals)
        except UniqueViolation as error:
            if error.diag.constraint_name.endswith("trade_reconciliation_sale_line_unique"):
                raise ValidationError(_("A selected sale line already belongs to a reconciliation.")) from error
            raise

    def _lock_sources(self):
        sales = self.mapped("sale_line_id")
        for records in (sales.order_id, sales):
            records.check_access_rights("read")
            records.check_access_rule("read")
            records.flush_recordset()
            if records:
                self.env.cr.execute(SQL(
                    "SELECT id FROM %s WHERE id IN %s ORDER BY id FOR UPDATE",
                    SQL.identifier(records._table), tuple(records.ids),
                ))
                records.invalidate_recordset()

    @api.constrains("reconciliation_id", "sale_line_id")
    def _check_reconcilable_sale_lines(self):
        for line in self:
            sale = line.sale_line_id
            parent = line.reconciliation_id
            if sale.display_type or sale.order_id.state != "sale":
                raise ValidationError(_("Only product lines from confirmed sales can be reconciled."))
            if sale.company_id != parent.company_id or sale.currency_id != parent.currency_id:
                raise ValidationError(_("The sale must match the reconciliation company and currency."))
            source = sale.trade_presale_line_id.import_line_id.import_id
            if not source or source.supplier_id != parent.supplier_id:
                raise ValidationError(_("The sale's import provenance must match the selected supplier."))
