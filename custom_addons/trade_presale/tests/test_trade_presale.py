from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import TradePresaleCase


@tagged("post_install", "-at_install")
class TestTradePresale(TradePresaleCase):
    def test_confirmed_presale_converts_once_to_sale_order(self):
        operation = self._complete_import(self._create_import())
        presale = self._create_presale(operation)
        presale.with_user(self.operator).action_confirm()
        action = presale.with_user(self.operator).action_convert_to_sale()
        second_action = presale.with_user(self.operator).action_convert_to_sale()
        order = presale.sale_order_id
        self.assertEqual(action["res_id"], second_action["res_id"])
        self.assertEqual(action["res_model"], "sale.order")
        self.assertEqual(presale.state, "converted")
        self.assertEqual(order.state, "draft")
        self.assertEqual(order.trade_presale_id, presale)
        self.assertEqual(order.trade_import_id, operation)
        self.assertEqual(order.order_line.product_uom_qty, 2)
        self.assertEqual(order.order_line.price_unit, 125)
        self.assertEqual(order.company_id, presale.company_id)
        self.assertEqual(order.currency_id, presale.currency_id)
        self.assertEqual(self.env["sale.order"].search_count([("trade_presale_id", "=", presale.id)]), 1)

    def test_draft_presale_cannot_convert(self):
        presale = self._create_presale(self._complete_import(self._create_import()))
        with self.assertRaises(UserError), self.env.cr.savepoint():
            presale.action_convert_to_sale()
        self.assertFalse(presale.sale_order_id)
        self.assertEqual(presale.state, "draft")

    def test_incomplete_import_cannot_convert(self):
        presale = self._create_presale(self._start_import(self._create_import()))
        presale.action_confirm()
        with self.assertRaises(UserError), self.env.cr.savepoint():
            presale.action_convert_to_sale()
        self.assertFalse(presale.sale_order_id)
        self.assertFalse(self.env["sale.order"].search([("trade_presale_id", "=", presale.id)]))

    def test_presale_product_must_belong_to_import(self):
        presale = self._create_presale(self._create_import())
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["trade.presale.line"].create({
                "presale_id": presale.id, "product_id": self.second_product.id,
                "quantity": 1, "unit_price": 25,
            })
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            presale.line_ids.write({"product_id": self.second_product.id})

    def test_header_change_revalidates_existing_lines(self):
        presale = self._create_presale(self._create_import())
        other_import = self._create_import()
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            presale.write({"import_id": other_import.id})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            presale.import_id.line_ids.write({"product_id": self.second_product.id})

    def test_no_empty_or_invalid_commercial_commitment(self):
        operation = self._start_import(self._create_import())
        empty = self.env["trade.presale"].create({"import_id": operation.id, "customer_id": self.customer.id})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            empty.action_confirm()
        presale = self._create_presale(operation)
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            presale.line_ids.write({"quantity": 0})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            presale.line_ids.write({"unit_price": -1})

    def test_overcommitment_is_warning_and_conversion_is_counted_once(self):
        operation = self._start_import(self._create_import())
        first = self._create_presale(operation, quantity=6)
        second = self._create_presale(operation, quantity=6)
        first.action_confirm()
        second.action_confirm()
        self.assertEqual(operation.line_ids.committed_quantity, 12)
        self.assertTrue(operation.line_ids.overcommitted)
        self.assertTrue(second.is_overcommitted)
        first.action_cancel()
        self.assertEqual(operation.line_ids.committed_quantity, 6)
        self.assertFalse(operation.line_ids.overcommitted)
        self._receive(operation.picking_ids)
        second.action_convert_to_sale()
        self.assertEqual(operation.line_ids.committed_quantity, 6)
        second.sale_order_id.order_line.product_uom_qty = 7
        self.assertEqual(operation.line_ids.committed_quantity, 7)
        second.sale_order_id.action_cancel()
        self.assertEqual(operation.line_ids.committed_quantity, 0)

    def test_confirmed_and_converted_data_are_protected(self):
        operation = self._complete_import(self._create_import())
        presale = self._create_presale(operation)
        presale.action_confirm()
        with self.assertRaises(UserError), self.env.cr.savepoint():
            presale.line_ids.write({"quantity": 3})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            presale.write({"state": "converted"})
        presale.action_convert_to_sale()
        with self.assertRaises(UserError), self.env.cr.savepoint():
            presale.sale_order_id.write({"trade_presale_id": False})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            presale.sale_order_id.unlink()
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            presale.sale_order_id.order_line.write({"product_id": self.second_product.id})

    def test_viewer_cannot_confirm_or_convert(self):
        presale = self._create_presale(self._complete_import(self._create_import()))
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            presale.with_user(self.viewer).action_confirm()
        presale.action_confirm()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            presale.with_user(self.viewer).action_convert_to_sale()

    def test_pricelist_currency_must_match(self):
        presale = self._create_presale(self._create_import())
        currency = self.env["res.currency"].with_context(active_test=False).search([("id", "!=", self.company.currency_id.id)], limit=1)
        pricelist = self.env["product.pricelist"].create({"name": "Foreign currency test", "currency_id": currency.id})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            presale.write({"pricelist_id": pricelist.id})
