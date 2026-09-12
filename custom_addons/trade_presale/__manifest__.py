{
    "name": "TradeOps Presales",
    "version": "17.0.2.0.0",
    "summary": "Controlled commercial commitments and idempotent quotations",
    "category": "Operations",
    "license": "LGPL-3",
    "depends": ["trade_import", "sale_stock", "mail"],
    "data": [
        "security/ir.model.access.csv", "security/trade_rules.xml",
        "views/trade_presale_views.xml", "views/sale_order_views.xml",
        "views/trade_import_views.xml",
    ],
    "installable": True,
    "application": False,
}
