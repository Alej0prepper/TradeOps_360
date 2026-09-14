from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TradePort(models.Model):
    _name = "trade.port"
    _description = "Trade Port"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    _sql_constraints = [("code_unique", "unique(code)", "Port codes must be unique.")]

    @api.model
    def _normalize_values(self, vals):
        result = dict(vals)
        for key in ("name", "code"):
            if key in result:
                value = str(result[key] or "").strip()
                if not value:
                    raise ValidationError(_("A port requires a non-empty name and code."))
                result[key] = value.upper() if key == "code" else value
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or not vals.get("code"):
                raise ValidationError(_("A port requires a non-empty name and code."))
        return super().create([self._normalize_values(vals) for vals in vals_list])

    def write(self, vals):
        return super().write(self._normalize_values(vals))
