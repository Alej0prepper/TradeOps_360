from odoo.addons.trade_core.migration import prepare_distributions


def migrate(cr, version):
    if version:
        prepare_distributions(cr)
