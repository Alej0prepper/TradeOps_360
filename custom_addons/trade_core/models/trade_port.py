from odoo import fields, models


class TradePort(models.Model):
    _name = "trade.port"
    _description = "Trade Port"
    _order = "name"

    name = fields.Char(
        required=True,
    )
    code = fields.Char(
        required=True,
        index=True,
    )
    active = fields.Boolean(
        default=True,
    )
