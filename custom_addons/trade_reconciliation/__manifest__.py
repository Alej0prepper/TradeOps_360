{
    "name": "TradeOps Reconciliation",
    "version": "17.0.1.0.0",
    "summary": "Supplier reconciliation with sale-line integrity",
    "category": "Operations",
    "license": "LGPL-3",
    "depends": [
        "trade_presale",
        "sale",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/trade_reconciliation_views.xml",
    ],
    "installable": True,
    "application": False,
}
