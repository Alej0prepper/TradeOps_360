import math
import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class TradeReconciliationAdjustment(models.Model):
    _name = "trade.reconciliation.adjustment"
    _description = "Immutable Commercial Reconciliation Adjustment"
    _rec_name = "reason"
    _order = "id desc"
    _check_company_auto = True

    reconciliation_id = fields.Many2one("trade.reconciliation", required=True, check_company=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="reconciliation_id.company_id", store=True, readonly=True, index=True)
    currency_id = fields.Many2one(related="reconciliation_id.currency_id", store=True, readonly=True)
    amount = fields.Monetary(required=True)
    reason = fields.Text(required=True)
    request_token = fields.Char(required=True, readonly=True, copy=False, default=lambda self: str(uuid.uuid4()))

    _sql_constraints = [
        ("request_unique", "unique(reconciliation_id, request_token)", "This adjustment request was already processed."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for original in vals_list:
            vals = dict(original)
            parent = self.env["trade.reconciliation"].browse(vals.get("reconciliation_id"))
            if not parent:
                raise ValidationError(_("A reconciliation is required."))
            parent._trade_require_role("manager")
            parent._trade_lock()
            parent._trade_check_state("confirmed")
            if parent.legacy_review_required:
                raise UserError(_("Review the historical reconciliation before adding corrections."))
            for name in ("company_id", "currency_id"):
                if name in vals and vals[name] != parent[name].id:
                    raise ValidationError(_("Adjustment ownership is derived from its reconciliation."))
                vals.pop(name, None)
            vals["reason"] = (vals.get("reason") or "").strip()
            prepared.append(vals)
        records = super().create(prepared)
        for record in records:
            record.reconciliation_id.message_post(body=_(
                "Commercial adjustment %s %s recorded. Reason: %s", record.amount, record.currency_id.name, record.reason,
            ))
        return records

    @api.constrains("amount", "reason")
    def _check_adjustment(self):
        for record in self:
            if not record.reason or not record.reason.strip():
                raise ValidationError(_("A written reason is required."))
            if not math.isfinite(record.amount) or record.currency_id.is_zero(record.amount):
                raise ValidationError(_("An adjustment must have a finite, non-zero amount."))

    def write(self, vals):
        raise UserError(_("Corrections are immutable. Record a separate reversing adjustment instead."))

    def unlink(self):
        raise UserError(_("Commercial adjustments must be retained for traceability."))

    def copy(self, default=None):
        raise UserError(_("Enter a new deliberate adjustment instead of copying an existing correction."))
