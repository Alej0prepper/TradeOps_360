{
    "name": "TradeOps Imports",
    "version": "17.0.2.0.0",
    "summary": "Controlled imports, operational costs and standard receipts",
    "category": "Operations",
    "license": "LGPL-3",
    "depends": ["trade_core", "purchase_stock", "mail"],
    "data": [
        "security/ir.model.access.csv", "security/trade_rules.xml",
        "views/trade_import_views.xml", "views/purchase_order_views.xml",
        "report/trade_import_report.xml",
    ],
    "installable": True,
    "application": True,
}
