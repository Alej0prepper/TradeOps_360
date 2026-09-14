import uuid

from odoo import _, fields, models
from odoo.exceptions import UserError


class TradeReconciliationAdjustmentWizard(models.TransientModel):
    _name = "trade.reconciliation.adjustment.wizard"
    _description = "Record Commercial Adjustment"
    _check_company_auto = True

    reconciliation_id = fields.Many2one("trade.reconciliation", required=True, check_company=True)
    company_id = fields.Many2one(related="reconciliation_id.company_id", store=True, readonly=True)
    currency_id = fields.Many2one(related="reconciliation_id.currency_id", readonly=True)
    amount = fields.Monetary(required=True)
    reason = fields.Text(required=True)
    request_token = fields.Char(required=True, readonly=True, default=lambda self: str(uuid.uuid4()))

    def action_apply(self):
        self.ensure_one()
        self.check_access_rights("read")
        self.check_access_rule("read")
        parent = self.reconciliation_id
        parent._trade_require_role("manager")
        parent._trade_lock()
        parent._trade_check_state("confirmed")
        Adjustment = self.env["trade.reconciliation.adjustment"]
        existing = Adjustment.search([
            ("reconciliation_id", "=", parent.id), ("request_token", "=", self.request_token),
        ], limit=1)
        reason = (self.reason or "").strip()
        if existing:
            if existing.reason != reason or self.currency_id.compare_amounts(existing.amount, self.amount):
                raise UserError(_("An already-applied request cannot be reused with different values."))
        else:
            Adjustment.create({"reconciliation_id": parent.id, "amount": self.amount,
                               "reason": reason, "request_token": self.request_token})
        return {"type": "ir.actions.act_window_close"}
