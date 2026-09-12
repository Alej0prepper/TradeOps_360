{
    "name": "TradeOps Distribution",
    "version": "17.0.2.0.0",
    "summary": "Physical delivery tracking and controlled incident resolution",
    "category": "Operations",
    "license": "LGPL-3",
    "depends": ["trade_presale", "sale_stock", "mail"],
    "data": [
        "security/ir.model.access.csv", "security/trade_rules.xml",
        "views/trade_distribution_views.xml", "views/trade_delivery_incident_views.xml",
        "wizard/trade_delivery_incident_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
