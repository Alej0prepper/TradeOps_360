from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TradeDocumentLegacyEvidence(models.AbstractModel):
    _inherit = "trade.document.mixin"

    legacy_original_reference = fields.Char(readonly=True, copy=False)
    legacy_payload = fields.Json(readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get("legacy_payload") or vals.get("legacy_original_reference") for vals in vals_list):
            raise UserError(_("Historical migration evidence cannot be supplied by a business request."))
        return super().create(vals_list)

    def write(self, vals):
        if {"legacy_payload", "legacy_original_reference"}.intersection(vals):
            raise UserError(_("Historical migration evidence is immutable."))
        return super().write(vals)
