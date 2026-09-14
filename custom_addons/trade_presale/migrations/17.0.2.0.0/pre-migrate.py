from odoo.addons.trade_core.migration import prepare_presales


def migrate(cr, version):
    if version:
        prepare_presales(cr)
