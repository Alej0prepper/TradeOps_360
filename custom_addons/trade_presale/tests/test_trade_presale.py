from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestTradePresale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})
        cls.origin_port = cls.env["trade.port"].create({"name": "Origin", "code": "ORI"})
        cls.destination_port = cls.env["trade.port"].create({"name": "Destination", "code": "DST"})
        cls.import_product = cls.env["product.product"].create({"name": "Imported product"})
        cls.other_product = cls.env["product.product"].create({"name": "Other product"})

    def _create_import(self, state="draft"):
        return self.env["trade.import"].create({
            "name": "IMP-PRESALE", "customer_id": self.customer.id,
            "origin_port_id": self.origin_port.id, "destination_port_id": self.destination_port.id,
            "state": state,
            "line_ids": [fields.Command.create({"product_id": self.import_product.id, "quantity": 2.0, "unit_purchase_price": 10.0})],
        })

    def _create_presale(self, trade_import, state="draft"):
        return self.env["trade.presale"].create({
            "name": "PRE-TEST", "import_id": trade_import.id, "customer_id": self.customer.id, "state": state,
            "line_ids": [fields.Command.create({"product_id": self.import_product.id, "quantity": 2.0, "unit_price": 25.0})],
        })

    def test_confirmed_presale_converts_once_to_sale_order(self):
        presale = self._create_presale(self._create_import(state="completed"), state="confirmed")

        sale_order = presale.action_convert_to_sale()

        self.assertEqual(presale.state, "converted")
        self.assertEqual(presale.sale_order_id, sale_order)
        self.assertEqual(sale_order.order_line.product_uom_qty, 2.0)
        with self.assertRaises(UserError):
            presale.action_convert_to_sale()

    def test_draft_presale_cannot_convert(self):
        presale = self._create_presale(self._create_import(state="completed"))

        with self.assertRaises(UserError):
            presale.action_convert_to_sale()

        self.assertFalse(presale.sale_order_id)

    def test_presale_product_must_belong_to_import(self):
        presale = self._create_presale(self._create_import())

        with self.assertRaises(ValidationError):
            self.env["trade.presale.line"].create({
                "presale_id": presale.id, "product_id": self.other_product.id,
                "quantity": 1.0, "unit_price": 25.0,
            })
