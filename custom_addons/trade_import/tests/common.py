from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user


class TradeImportCase(TransactionCase):
    """Factories use real public workflows and non-administrator operators."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.customer = cls.env["res.partner"].create({"name": "TradeOps test customer"})
        cls.supplier = cls.env["res.partner"].create({"name": "TradeOps test supplier", "supplier_rank": 1})
        cls.origin_port = cls.env["trade.port"].create({"name": "Origin", "code": "TSTORI"})
        cls.destination_port = cls.env["trade.port"].create({"name": "Destination", "code": "TSTDST"})
        cls.first_product = cls.env["product.product"].create({"name": "Product A", "detailed_type": "product"})
        cls.second_product = cls.env["product.product"].create({"name": "Product B", "detailed_type": "product"})
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.company.id)], limit=1)
        cls.operator = new_test_user(cls.env, login="trade_test_operator", groups="trade_core.group_trade_operator")
        cls.manager = new_test_user(cls.env, login="trade_test_manager", groups="trade_core.group_trade_manager")
        cls.viewer = new_test_user(cls.env, login="trade_test_viewer", groups="trade_core.group_trade_viewer")
        cls.outsider = new_test_user(cls.env, login="trade_test_outsider", groups="base.group_user")

    def _import_values(self, quantity=10.0, price=100.0):
        return {
            "customer_id": self.customer.id, "supplier_id": self.supplier.id,
            "warehouse_id": self.warehouse.id,
            "origin_port_id": self.origin_port.id, "destination_port_id": self.destination_port.id,
            "line_ids": [fields.Command.create({
                "product_id": self.first_product.id, "quantity": quantity,
                "unit_purchase_price": price,
            })],
        }

    def _create_import(self, quantity=10.0, price=100.0):
        return self.env["trade.import"].with_user(self.operator).create(self._import_values(quantity, price))

    def _start_import(self, operation):
        operation.with_user(self.operator).action_submit()
        operation.with_user(self.manager).action_validate()
        operation.with_user(self.manager).action_start_transit()
        return operation

    def _receive(self, picking, quantities=None):
        picking = picking.with_user(self.operator)
        picking.action_assign()
        for move in picking.move_ids.filtered(lambda record: record.state not in ("done", "cancel")):
            move.quantity = (quantities or {}).get(move.product_id.id, move.product_uom_qty)
            move.picked = True
        # Skip only the interactive backorder question, not stock sanity checks.
        picking.with_context(skip_backorder=True).button_validate()
        self.assertEqual(picking.state, "done")

    def _complete_import(self, operation):
        self._start_import(operation)
        for picking in operation.picking_ids.filtered(lambda record: record.state not in ("done", "cancel")):
            self._receive(picking)
        self.assertEqual(operation.state, "completed")
        return operation
