from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TradePort(models.Model):
    _name = "trade.port"
    _description = "Trade Port"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_unique", "unique(code)", "Port codes must be unique."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([
            dict(vals, code=(vals.get("code") or "").strip().upper())
            for vals in vals_list
        ])

    def write(self, vals):
        if "code" in vals:
            vals = dict(vals, code=(vals["code"] or "").strip().upper())
        return super().write(vals)

    @api.constrains("code", "name")
    def _check_not_blank(self):
        if any(not record.code.strip() or not record.name.strip() for record in self):
            raise ValidationError(_("A port requires a non-empty name and code."))
