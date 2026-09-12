from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestTradeImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})
        cls.origin_port = cls.env["trade.port"].create(
            {"name": "Origin", "code": "ORI"}
        )
        cls.destination_port = cls.env["trade.port"].create(
            {"name": "Destination", "code": "DST"}
        )
        cls.first_product = cls.env["product.product"].create(
            {"name": "First product"}
        )
        cls.second_product = cls.env["product.product"].create(
            {"name": "Second product"}
        )

    def _import_values(self):
        return {
            "name": "IMP-TEST",
            "customer_id": self.customer.id,
            "origin_port_id": self.origin_port.id,
            "destination_port_id": self.destination_port.id,
        }

    def test_expenses_are_allocated_by_purchase_value(self):
        trade_import = self.env["trade.import"].create(
            {
                **self._import_values(),
                "line_ids": [
                    fields.Command.create({"product_id": self.first_product.id, "quantity": 1, "unit_purchase_price": 100.0}),
                    fields.Command.create({"product_id": self.second_product.id, "quantity": 1, "unit_purchase_price": 300.0}),
                ],
                "expense_ids": [
                    fields.Command.create({"expense_type": "freight", "amount": 40.0})
                ],
            }
        )

        first_line, second_line = trade_import.line_ids
        self.assertEqual(trade_import.purchase_total, 400.0)
        self.assertEqual(trade_import.expense_total, 40.0)
        self.assertEqual(first_line.allocated_expense, 10.0)
        self.assertEqual(second_line.allocated_expense, 30.0)
        self.assertEqual(second_line.real_unit_cost, 330.0)

    def test_import_requires_different_ports(self):
        values = self._import_values()
        values["destination_port_id"] = self.origin_port.id

        with self.assertRaises(ValidationError):
            self.env["trade.import"].create(values)

    def test_import_line_quantity_must_be_positive(self):
        trade_import = self.env["trade.import"].create(self._import_values())

        with self.assertRaises(ValidationError):
            self.env["trade.import.line"].create(
                {"import_id": trade_import.id, "product_id": self.first_product.id, "quantity": 0.0, "unit_purchase_price": 10.0}
            )
