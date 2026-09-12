{
    "name": "TradeOps Commercial Reconciliation",
    "version": "17.0.2.0.0",
    "summary": "Supplier provenance, frozen sales subtotals and traceable corrections",
    "category": "Operations",
    "license": "LGPL-3",
    "depends": ["trade_presale", "sale", "mail"],
    "data": [
        "security/ir.model.access.csv", "security/trade_rules.xml",
        "views/trade_reconciliation_views.xml", "wizard/trade_reconciliation_adjustment_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
