"""Verify company rules through the entire commercial document chain."""
from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.addons.trade_presale.tests.common import TradePresaleCase


@tagged("post_install", "-at_install")
class TestCommercialCompanyIsolation(TradePresaleCase):
    def test_commercial_documents_children_and_adjustments_are_isolated(self):
        operation = self._create_import()
        expense = self.env["trade.import.expense"].with_user(self.operator).create({
            "import_id": operation.id, "expense_type": "freight", "amount": 10,
        })
        self._complete_import(operation)
        presale = self._create_presale(operation)
        presale.with_user(self.operator).action_confirm()
        presale.with_user(self.operator).action_convert_to_sale()
        sale = presale.sale_order_id
        sale.with_user(self.operator).action_confirm()
        statement = self.env["trade.reconciliation"].with_user(self.operator).create({
            "supplier_id": self.supplier.id,
            "line_ids": [fields.Command.create({"sale_line_id": sale.order_line.id})],
        })
        statement.with_user(self.manager).action_reconcile()
        adjustment = self.env["trade.reconciliation.adjustment"].with_user(self.manager).create({
            "reconciliation_id": statement.id, "amount": -5, "reason": "Explicit test correction",
        })
        other = self.env["res.company"].create({"name": "Isolated commercial company"})
        manager_b = self.outsider.copy({
            "login": "commercial_manager_b", "company_id": other.id,
            "company_ids": [fields.Command.set(other.ids)],
            "groups_id": [fields.Command.set(self.env.ref("trade_core.group_trade_manager").ids)],
        })
        records = (operation, operation.line_ids, expense, presale, presale.line_ids,
                   statement, statement.line_ids, adjustment)
        for record in records:
            with self.subTest(model=record._name):
                scoped = record.with_user(manager_b).with_context(allowed_company_ids=other.ids)
                self.assertFalse(scoped.search([("id", "in", record.ids)]))
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    scoped.read(["company_id"])
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            statement.with_user(manager_b).action_add_adjustment()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            presale.with_user(manager_b).action_convert_to_sale()
        # Being allowed in both companies must not ignore the selected company scope.
        manager_b.write({"company_ids": [fields.Command.set((self.company | other).ids)]})
        scoped = statement.with_user(manager_b)
        self.assertFalse(scoped.with_context(allowed_company_ids=other.ids).search([("id", "=", statement.id)]))
        self.assertEqual(scoped.with_context(allowed_company_ids=self.company.ids).search([("id", "=", statement.id)]).id, statement.id)
