from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.trade_presale.tests.common import TradePresaleCase


@tagged("post_install", "-at_install")
class TestTradeReconciliation(TradePresaleCase):
    def _create_confirmed_sale_line(self, price):
        order = self._create_sale(quantity=1)
        order.order_line.price_unit = price
        return order.order_line

    def _create_reconciliation(self, sale_lines):
        return self.env["trade.reconciliation"].create({
            "supplier_id": self.supplier.id,
            "line_ids": [fields.Command.create({"sale_line_id": line.id}) for line in sale_lines],
        })

    def test_reconcile_confirmed_sales_and_calculates_total(self):
        first = self._create_confirmed_sale_line(20)
        second = self._create_confirmed_sale_line(30)
        reconciliation = self._create_reconciliation([first, second])
        reconciliation.with_user(self.manager).action_reconcile()
        self.assertEqual(reconciliation.state, "confirmed")
        self.assertEqual(reconciliation.total_amount, 50)
        self.assertEqual(reconciliation.net_total, 50)
        self.assertEqual(len(reconciliation.line_ids), 2)
        self.assertEqual(reconciliation.confirmed_by_id, self.manager)
        self.assertTrue(reconciliation.confirmed_at)
        self.assertTrue(reconciliation.message_ids.filtered(lambda message: "Commercial reconciliation confirmed" in message.body))

    def test_sale_line_cannot_be_reconciled_twice(self):
        line = self._create_confirmed_sale_line(20)
        self._create_reconciliation([line])
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self._create_reconciliation([line])
        self.assertEqual(self.env["trade.reconciliation.line"].search_count([("sale_line_id", "=", line.id)]), 1)

    def test_database_unique_constraint_is_the_final_guard(self):
        line = self._create_confirmed_sale_line(20)
        reconciliation = self._create_reconciliation([line])
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.env.cr.execute(
                """INSERT INTO trade_reconciliation_line
                   (reconciliation_id, sale_line_id, create_uid, create_date, write_uid, write_date)
                   VALUES (%s, %s, %s, NOW(), %s, NOW())""",
                [reconciliation.id, line.id, self.env.uid, self.env.uid],
            )

    def test_invalid_batch_does_not_create_a_partial_reconciliation(self):
        confirmed = self._create_confirmed_sale_line(20)
        draft = self.env["sale.order"].create({
            "partner_id": self.customer.id,
            "order_line": [fields.Command.create({"product_id": self.first_product.id, "product_uom_qty": 1, "price_unit": 30})],
        })
        before = self.env["trade.reconciliation"].search_count([])
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self._create_reconciliation([confirmed, draft.order_line])
        self.assertEqual(self.env["trade.reconciliation"].search_count([]), before)
        self.assertFalse(self.env["trade.reconciliation.line"].search([("sale_line_id", "=", confirmed.id)]))

    def test_failed_reconciliation_keeps_draft_state(self):
        reconciliation = self.env["trade.reconciliation"].create({"supplier_id": self.supplier.id})
        messages_before = reconciliation.message_ids
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            reconciliation.action_reconcile()
        self.assertEqual(reconciliation.state, "draft")
        self.assertEqual(reconciliation.message_ids, messages_before)

    def test_supplier_provenance_and_header_mutations_are_checked(self):
        line = self._create_confirmed_sale_line(20)
        other_supplier = self.env["res.partner"].create({"name": "Unrelated supplier", "supplier_rank": 1})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["trade.reconciliation"].create({
                "supplier_id": other_supplier.id,
                "line_ids": [fields.Command.create({"sale_line_id": line.id})],
            })
        reconciliation = self._create_reconciliation([line])
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            reconciliation.write({"supplier_id": other_supplier.id})

    def test_confirmed_statement_is_frozen_even_if_sale_changes(self):
        sale_line = self._create_confirmed_sale_line(20)
        reconciliation = self._create_reconciliation([sale_line])
        reconciliation.action_reconcile()
        sale_line.price_unit = 70
        self.assertEqual(sale_line.price_subtotal, 70)
        self.assertEqual(reconciliation.total_amount, 20)
        self.assertEqual(reconciliation.line_ids.snapshot_amount, 20)
        self.assertEqual(reconciliation.line_ids.snapshot_unit_price, 20)
        self.assertEqual(reconciliation.line_ids.snapshot_sale_reference, sale_line.order_id.name)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            reconciliation.write({"supplier_id": self.customer.id})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            reconciliation.line_ids.write({"snapshot_amount": 999})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            reconciliation.unlink()

    def test_only_responsible_role_can_confirm(self):
        reconciliation = self._create_reconciliation([self._create_confirmed_sale_line(20)])
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            reconciliation.with_user(self.operator).action_reconcile()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            reconciliation.with_user(self.viewer).action_reconcile()
        reconciliation.with_user(self.manager).action_reconcile()
        self.assertEqual(reconciliation.state, "confirmed")

    def test_correction_is_separate_immutable_and_replay_safe(self):
        reconciliation = self._create_reconciliation([self._create_confirmed_sale_line(20)])
        reconciliation.with_user(self.manager).action_reconcile()
        action = reconciliation.with_user(self.manager).action_add_adjustment()
        wizard = self.env[action["res_model"]].with_user(self.manager).with_context(action["context"]).create({
            "amount": -5, "reason": "Documented commercial correction",
        })
        wizard.action_apply()
        wizard.action_apply()
        self.assertEqual(len(reconciliation.adjustment_ids), 1)
        self.assertEqual(reconciliation.total_amount, 20)
        self.assertEqual(reconciliation.adjustment_total, -5)
        self.assertEqual(reconciliation.net_total, 15)
        self.assertEqual(reconciliation.adjustment_ids.create_uid, self.manager)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            reconciliation.adjustment_ids.write({"amount": -10})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            reconciliation.adjustment_ids.unlink()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env["trade.reconciliation.adjustment"].with_user(self.operator).create({
                "reconciliation_id": reconciliation.id, "amount": 1, "reason": "Unauthorized correction",
            })

    def test_empty_or_zero_correction_is_rejected(self):
        reconciliation = self._create_reconciliation([self._create_confirmed_sale_line(20)])
        reconciliation.action_reconcile()
        for amount, reason in [(0, "No amount"), (1, " ")]:
            with self.subTest(amount=amount, reason=reason):
                with self.assertRaises(ValidationError), self.env.cr.savepoint():
                    self.env["trade.reconciliation.adjustment"].create({
                        "reconciliation_id": reconciliation.id, "amount": amount, "reason": reason,
                    })
        self.assertFalse(reconciliation.adjustment_ids)
