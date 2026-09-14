from odoo import fields

from odoo.addons.trade_import.tests.common import TradeImportCase


class TradePresaleCase(TradeImportCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env["product.pricelist"].create({
            "name": "TradeOps test company-currency pricelist",
            "currency_id": cls.company.currency_id.id,
            "company_id": cls.company.id,
        })

    def _create_presale(self, operation, quantity=2.0, price=125.0):
        return self.env["trade.presale"].create({
            "import_id": operation.id, "customer_id": self.customer.id,
            "pricelist_id": self.pricelist.id,
            "line_ids": [fields.Command.create({
                "import_line_id": operation.line_ids[0].id,
                "quantity": quantity, "unit_price": price,
            })],
        })

    def _create_sale(self, quantity=10.0):
        operation = self._complete_import(self._create_import(quantity=quantity))
        presale = self._create_presale(operation, quantity=quantity)
        presale.with_user(self.operator).action_confirm()
        action = presale.with_user(self.operator).action_convert_to_sale()
        order = self.env["sale.order"].browse(action["res_id"])
        order.with_user(self.operator).action_confirm()
        return order
