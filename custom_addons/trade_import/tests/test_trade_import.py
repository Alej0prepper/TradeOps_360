from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import TradeImportCase


@tagged("post_install", "-at_install")
class TestTradeImport(TradeImportCase):
    def test_expenses_are_allocated_by_purchase_value(self):
        values = self._import_values(quantity=1, price=100)
        values["line_ids"].append(fields.Command.create({
            "product_id": self.second_product.id, "quantity": 1, "unit_purchase_price": 300,
        }))
        values["expense_ids"] = [fields.Command.create({"expense_type": "freight", "amount": 40})]
        operation = self.env["trade.import"].create(values)
        first, second = operation.line_ids
        self.assertEqual(operation.purchase_total, 400)
        self.assertEqual(operation.expense_total, 40)
        self.assertEqual(first.allocated_expense, 10)
        self.assertEqual(second.allocated_expense, 30)
        self.assertEqual(second.real_unit_cost, 330)

    def test_rounding_residuals_and_recomputation(self):
        values = self._import_values(quantity=1, price=1)
        values["line_ids"] += [fields.Command.create({
            "product_id": self.second_product.id, "quantity": 1, "unit_purchase_price": 1,
        }) for _ in range(2)]
        values["expense_ids"] = [fields.Command.create({"expense_type": "freight", "amount": 0.02})]
        operation = self.env["trade.import"].create(values)
        self.assertAlmostEqual(sum(operation.line_ids.mapped("allocated_expense")), 0.02)
        self.assertTrue(all(line.allocated_expense >= 0 for line in operation.line_ids))
        operation.line_ids[0].quantity = 2
        self.assertAlmostEqual(sum(operation.line_ids.mapped("real_total_cost")), operation.landed_total)
        self.assertAlmostEqual(operation.line_ids[0].real_unit_cost * 2, operation.line_ids[0].real_total_cost)

    def test_invalid_costs_and_missing_allocation_basis(self):
        operation = self._create_import(price=0)
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["trade.import.expense"].create({"import_id": operation.id, "expense_type": "freight", "amount": 1})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            operation.line_ids.write({"unit_purchase_price": -1})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            operation.line_ids.write({"quantity": 0})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["trade.import.expense"].create({"import_id": operation.id, "expense_type": "freight", "amount": -1})

    def test_import_requires_different_ports(self):
        values = self._import_values()
        values["destination_port_id"] = self.origin_port.id
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["trade.import"].create(values)

    def test_initial_state_sequences_and_safe_copy(self):
        operation = self._create_import()
        duplicate = operation.copy()
        self.assertNotEqual(operation.name, "New")
        self.assertNotEqual(operation.name, duplicate.name)
        self.assertEqual(duplicate.state, "draft")
        self.assertFalse(duplicate.purchase_order_ids)
        self.assertEqual(len(operation.line_ids), len(duplicate.line_ids))
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["trade.import"].create(dict(self._import_values(), state="completed"))
        with self.assertRaises(UserError), self.env.cr.savepoint():
            operation.write({"state": "completed"})

    def test_roles_and_direct_child_protection(self):
        operation = self.env["trade.import"].with_user(self.operator).create(self._import_values())
        self.assertEqual(operation.with_user(self.viewer).name, operation.name)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            operation.with_user(self.outsider).read(["name"])
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            operation.with_user(self.viewer).action_submit()
        operation.action_submit()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            operation.action_validate()
        with self.assertRaises(UserError), self.env.cr.savepoint():
            operation.line_ids.with_user(self.operator).write({"quantity": 20})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            operation.line_ids.with_user(self.operator).unlink()
        operation.with_user(self.manager).action_validate()
        with self.assertRaises(UserError), self.env.cr.savepoint():
            operation.with_user(self.manager).unlink()

    def test_company_isolation_including_lines(self):
        other = self.env["res.company"].create({"name": "Other TradeOps company"})
        other_user = self.outsider.copy({
            "login": "trade_other_company", "company_id": other.id,
            "company_ids": [fields.Command.set(other.ids)],
            "groups_id": [fields.Command.set(self.env.ref("trade_core.group_trade_operator").ids)],
        })
        operation = self._create_import()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            operation.with_user(other_user).read(["name"])
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            operation.line_ids.with_user(other_user).read(["quantity"])
        product = self.env["product.product"].create({"name": "Private B product", "company_id": other.id})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            operation.line_ids.write({"product_id": product.id})

    def test_partial_receipts_complete_only_after_physical_receipt(self):
        operation = self._start_import(self._create_import())
        self.assertEqual(operation.state, "in_transit")
        self.assertEqual(operation.line_ids.received_quantity, 0)
        self._receive(operation.picking_ids, {self.first_product.id: 6})
        self.assertEqual(operation.state, "partially_received")
        self.assertEqual(operation.line_ids.received_quantity, 6)
        backorder = operation.picking_ids.filtered(lambda picking: picking.state not in ("done", "cancel"))
        self.assertEqual(len(backorder), 1)
        self._receive(backorder)
        self.assertEqual(operation.state, "completed")
        self.assertEqual(operation.line_ids.received_quantity, 10)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            operation.action_cancel()

    def test_lot_is_required_and_standard_inventory_creates_it(self):
        self.first_product.tracking = "lot"
        operation = self._start_import(self._create_import())
        picking = operation.picking_ids
        picking.move_ids.quantity = 10
        with self.assertRaises(UserError), self.env.cr.savepoint():
            picking.with_context(skip_backorder=True).button_validate()
        picking.move_line_ids.lot_name = operation.name
        picking.with_context(skip_backorder=True).button_validate()
        self.assertEqual(operation.state, "completed")
        self.assertEqual(picking.move_line_ids.lot_id.name, operation.name)
        self.assertEqual(picking.move_line_ids.lot_id.product_id, self.first_product)

    def test_no_duplicate_purchase_or_source_mutation(self):
        operation = self._start_import(self._create_import())
        self.assertEqual(len(operation.purchase_order_ids), 1)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            operation.action_validate()
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            operation.purchase_order_ids.order_line.write({"product_qty": 99})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            operation.purchase_order_ids.button_cancel()

    def test_cancel_before_receipt_uses_standard_purchase_cancellation(self):
        operation = self._start_import(self._create_import())
        operation.with_user(self.manager).action_cancel()
        self.assertEqual(operation.state, "cancelled")
        self.assertEqual(operation.purchase_order_ids.state, "cancel")
        self.assertTrue(all(picking.state == "cancel" for picking in operation.picking_ids))

    def test_report_renders_operational_summary(self):
        operation = self._create_import()
        report = self.env.ref("trade_import.action_report_trade_import")
        html, _kind = report._render_qweb_html(report.report_name, operation.ids)
        self.assertIn(operation.name.encode(), html)
        self.assertIn(b"Operational costs only", html)
