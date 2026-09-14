from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.trade_presale.tests.common import TradePresaleCase


@tagged("post_install", "-at_install")
class TestTradeDistribution(TradePresaleCase):
    def _create_distribution(self, sale=None):
        sale = sale or self._create_sale()
        distribution = self.env["trade.distribution"].with_user(self.operator).create({"sale_order_id": sale.id})
        distribution.action_start()
        return distribution

    def test_reservation_is_not_delivery_and_partial_receipts_recompute(self):
        distribution = self._create_distribution()
        delivery = distribution.sale_order_id.picking_ids
        delivery.action_assign()
        self.assertEqual(distribution.line_ids.expected_quantity, 10)
        self.assertEqual(distribution.line_ids.delivered_quantity, 0)
        delivery.move_ids.quantity = 6
        self.assertEqual(distribution.line_ids.delivered_quantity, 0)
        self._receive(delivery, {self.first_product.id: 6})
        self.assertEqual(distribution.line_ids.delivered_quantity, 6)
        self.assertEqual(distribution.line_ids.pending_quantity, 4)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            distribution.with_user(self.manager).action_close()
        backorder = distribution.picking_ids.filtered(lambda picking: picking.state not in ("done", "cancel"))
        self._receive(backorder)
        self.assertEqual(distribution.line_ids.delivered_quantity, 10)
        distribution.with_user(self.manager).action_close()
        self.assertEqual(distribution.state, "closed")

    def test_standard_return_updates_net_delivery_and_reopens_distribution(self):
        distribution = self._create_distribution()
        delivery = distribution.picking_ids
        self._receive(delivery)
        distribution.with_user(self.manager).action_close()
        wizard = self.env["stock.return.picking"].create({"picking_id": delivery.id})
        wizard.product_return_moves.quantity = 2
        action = wizard.create_returns()
        returned = self.env["stock.picking"].browse(action["res_id"])
        returned.move_ids.to_refund = True
        self.assertEqual(distribution.line_ids.delivered_quantity, 10)
        self._receive(returned)
        self.assertEqual(distribution.line_ids.delivered_quantity, 8)
        self.assertEqual(distribution.line_ids.pending_quantity, 2)
        self.assertEqual(distribution.state, "active")

    def test_reporting_incident_creates_record_and_audit_message(self):
        distribution = self._create_distribution()
        action = distribution.action_report_incident()
        wizard = self.env[action["res_model"]].with_user(self.operator).with_context(action["context"]).create({
            "incident_type": "damaged_goods", "description": "Packaging was damaged.",
        })
        result = wizard.action_confirm()
        incident = distribution.incident_ids
        self.assertEqual(result["type"], "ir.actions.act_window_close")
        self.assertEqual(len(incident), 1)
        self.assertEqual(incident.responsible_id, self.operator)
        self.assertTrue(distribution.message_ids.filtered(lambda message: "Packaging was damaged" in message.body))
        self.assertEqual(distribution.line_ids.delivered_quantity, 0)

    def test_incident_requires_description_without_side_effects(self):
        distribution = self._create_distribution()
        messages_before = distribution.message_ids
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            distribution._report_incident("other", " ")
        self.assertFalse(distribution.incident_ids)
        self.assertEqual(distribution.message_ids, messages_before)

    def test_incident_resolution_requires_manager_and_is_immutable(self):
        distribution = self._create_distribution()
        incident = distribution._report_incident("other", "Delivery access problem")
        self._receive(distribution.picking_ids)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            distribution.with_user(self.manager).action_close()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            incident.with_user(self.operator).write({"resolution": "New delivery appointment"})
        incident.with_user(self.manager).write({"resolution": "New delivery appointment confirmed"})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            incident.with_user(self.operator).action_resolve()
        incident.with_user(self.manager).action_resolve()
        self.assertEqual(incident.state, "resolved")
        self.assertEqual(incident.resolved_by_id, self.manager)
        self.assertTrue(incident.resolved_at)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            incident.write({"description": "Rewrite historical incident"})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            incident.unlink()
        distribution.with_user(self.manager).action_close()
        self.assertEqual(distribution.state, "closed")

    def test_unrelated_picking_and_unauthorized_user_are_rejected(self):
        sale = self._create_sale()
        other_sale = self._create_sale()
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["trade.distribution"].create({"sale_order_id": sale.id, "picking_id": other_sale.picking_ids.id})
        distribution = self._create_distribution(sale)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            distribution.with_user(self.viewer).action_report_incident()
        with self.assertRaises(UserError), self.env.cr.savepoint():
            distribution.line_ids.with_user(self.operator).write({"sale_line_id": other_sale.order_line.id})

    def test_mixed_units_are_never_added_into_a_quantity_summary(self):
        kg = self.env.ref("uom.product_uom_kgm")
        self.second_product.write({"uom_id": kg.id, "uom_po_id": kg.id})
        values = self._import_values()
        values["line_ids"].append(fields.Command.create({
            "product_id": self.second_product.id, "quantity": 5, "unit_purchase_price": 10,
        }))
        operation = self._complete_import(self.env["trade.import"].create(values))
        presale = self._create_presale(operation, quantity=10)
        presale.write({"line_ids": [fields.Command.create({
            "import_line_id": operation.line_ids[1].id, "quantity": 5, "unit_price": 15,
        })]})
        presale.action_confirm()
        presale.action_convert_to_sale()
        presale.sale_order_id.action_confirm()
        distribution = self._create_distribution(presale.sale_order_id)
        self.assertEqual(len(distribution.line_ids), 2)
        self.assertFalse(distribution.has_uniform_uom)
        self.assertFalse(distribution.summary_uom_id)
        self.assertEqual(distribution.expected_quantity, 0)
        self.assertEqual(sorted(distribution.line_ids.mapped("expected_quantity")), [5, 10])
