from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged

from .common import TradePresaleCase


@tagged("post_install", "-at_install")
class TestTradeForms(TradePresaleCase):
    def test_import_and_presale_forms_create_coherent_records(self):
        form = Form(self.env["trade.import"].with_user(self.operator))
        form.customer_id = self.customer
        form.supplier_id = self.supplier
        form.warehouse_id = self.warehouse
        form.origin_port_id = self.origin_port
        form.destination_port_id = self.destination_port
        with form.line_ids.new() as line:
            line.product_id = self.first_product
            line.quantity = 10
            line.unit_purchase_price = 100
        operation = form.save()
        self._start_import(operation)
        commitment = Form(self.env["trade.presale"].with_user(self.operator))
        commitment.import_id = operation
        commitment.customer_id = self.customer
        commitment.pricelist_id = self.pricelist
        with commitment.line_ids.new() as line:
            line.import_line_id = operation.line_ids[0]
            line.quantity = 2
            line.unit_price = 125
        presale = commitment.save()
        self.assertEqual(presale.line_ids.product_id, self.first_product)
        self.assertEqual(presale.line_ids.import_line_id, operation.line_ids)
        presale.action_confirm()
        self.assertEqual(presale.state, "confirmed")

    def test_children_cannot_spoof_company_or_currency(self):
        operation = self._create_import()
        other = self.env["res.company"].create({"name": "Child spoof company"})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["trade.import.line"].with_user(self.operator).create({
                "import_id": operation.id, "company_id": other.id,
                "product_id": self.second_product.id, "quantity": 1, "unit_purchase_price": 1,
            })
        foreign = self.env["res.currency"].with_context(active_test=False).search([
            ("id", "!=", self.company.currency_id.id),
        ], limit=1)
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["trade.import.expense"].with_user(self.operator).create({
                "import_id": operation.id, "currency_id": foreign.id,
                "expense_type": "freight", "amount": 10,
            })
