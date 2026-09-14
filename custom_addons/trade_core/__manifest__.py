{
    "name": "TradeOps Core",
    "version": "17.0.2.0.0",
    "summary": "Shared roles, references and catalogs for TradeOps 360",
    "category": "Operations",
    "license": "LGPL-3",
    "depends": ["contacts", "sale_stock", "purchase_stock", "mail"],
    "data": [
        "security/trade_groups.xml", "security/ir.model.access.csv",
        "data/trade_sequences.xml", "views/res_partner_views.xml",
        "views/trade_port_views.xml",
    ],
    "installable": True,
    "application": False,
}
