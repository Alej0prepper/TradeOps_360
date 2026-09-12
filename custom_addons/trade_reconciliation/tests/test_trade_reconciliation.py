from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from psycopg2 import IntegrityError


class TestTradeReconciliation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})
        cls.supplier = cls.env["res.partner"].create(
            {"name": "Supplier", "supplier_rank": 1}
        )
        cls.product = cls.env["product.product"].create({"name": "Product"})

    def _create_confirmed_sale_line(self, price):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "order_line": [
                    fields.Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": price,
                        }
                    )
                ],
            }
        )
        order.action_confirm()
        return order.order_line

    def _create_reconciliation(self, sale_lines):
        return self.env["trade.reconciliation"].create(
            {
                "name": "RECON-TEST",
                "supplier_id": self.supplier.id,
                "line_ids": [
                    fields.Command.create({"sale_line_id": sale_line.id})
                    for sale_line in sale_lines
                ],
            }
        )

    def test_reconcile_confirmed_sales_and_calculates_total(self):
        first_line = self._create_confirmed_sale_line(20.0)
        second_line = self._create_confirmed_sale_line(30.0)

        reconciliation = self._create_reconciliation([first_line, second_line])
        reconciliation.action_reconcile()

        self.assertEqual(reconciliation.state, "confirmed")
        self.assertEqual(reconciliation.total_amount, 50.0)
        self.assertEqual(len(reconciliation.line_ids), 2)
        self.assertTrue(
            reconciliation.message_ids.filtered(
                lambda message: "Supplier reconciliation confirmed" in message.body
            )
        )

    def test_sale_line_cannot_be_reconciled_twice(self):
        sale_line = self._create_confirmed_sale_line(20.0)
        self._create_reconciliation([sale_line])

        with self.assertRaises(ValidationError):
            self._create_reconciliation([sale_line])

        self.assertEqual(
            self.env["trade.reconciliation.line"].search_count(
                [("sale_line_id", "=", sale_line.id)]
            ),
            1,
        )

    def test_database_constraint_rejects_concurrent_duplicate(self):
        sale_line = self._create_confirmed_sale_line(20.0)
        reconciliation = self._create_reconciliation([sale_line])

        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.env.cr.execute(
                """
                INSERT INTO trade_reconciliation_line (
                    reconciliation_id, sale_line_id,
                    create_uid, create_date, write_uid, write_date
                )
                VALUES (%s, %s, %s, NOW(), %s, NOW())
                """,
                [
                    reconciliation.id,
                    sale_line.id,
                    self.env.uid,
                    self.env.uid,
                ],
            )

    def test_invalid_batch_does_not_create_a_partial_reconciliation(self):
        confirmed_line = self._create_confirmed_sale_line(20.0)
        draft_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "order_line": [
                    fields.Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 30.0,
                        }
                    )
                ],
            }
        )

        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self._create_reconciliation(
                [confirmed_line, draft_order.order_line]
            )

        self.assertFalse(
            self.env["trade.reconciliation"].search(
                [("name", "=", "RECON-TEST")]
            )
        )

    def test_failed_reconciliation_keeps_draft_state(self):
        reconciliation = self.env["trade.reconciliation"].create(
            {"name": "RECON-EMPTY", "supplier_id": self.supplier.id}
        )
        messages_before = reconciliation.message_ids

        with self.assertRaises(ValidationError):
            reconciliation.action_reconcile()

        self.assertEqual(reconciliation.state, "draft")
        self.assertEqual(reconciliation.message_ids, messages_before)
