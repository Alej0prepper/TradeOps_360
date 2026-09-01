from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    trade_code = fields.Char(
        string="TradeOps Code",
        help="Short code used by TradeOps references.",
    )
