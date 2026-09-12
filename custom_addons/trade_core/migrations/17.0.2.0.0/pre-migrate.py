from odoo.addons.trade_core.migration import prepare_core


def migrate(cr, version):
    if version:
        prepare_core(cr)
