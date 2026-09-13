"""Company isolation includes operational children, not just import headers."""
from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.addons.trade_presale.tests.common import TradePresaleCase


@tagged("post_install", "-at_install")
class TestDistributionCompanyIsolation(TradePresaleCase):
    def test_distribution_children_and_incidents_are_isolated(self):
        sale = self._create_sale()
        distribution = self.env["trade.distribution"].with_user(self.operator).create({"sale_order_id": sale.id})
        distribution.action_start()
        incident = distribution._report_incident("other", "Company-private incident")
        other = self.env["res.company"].create({"name": "Isolated distribution company"})
        manager_b = self.outsider.copy({
            "login": "distribution_manager_b", "company_id": other.id,
            "company_ids": [fields.Command.set(other.ids)],
            "groups_id": [fields.Command.set(self.env.ref("trade_core.group_trade_manager").ids)],
        })
        for record in (distribution, distribution.line_ids, incident):
            with self.subTest(model=record._name):
                scoped = record.with_user(manager_b).with_context(allowed_company_ids=other.ids)
                self.assertFalse(scoped.search([("id", "in", record.ids)]))
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    scoped.read(["company_id"])
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            distribution.with_user(manager_b).action_report_incident()
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            incident.with_user(self.operator).write({"responsible_id": manager_b.id})
        self.assertEqual(incident.responsible_id, self.operator)
        self.assertEqual(distribution.line_ids.delivered_quantity, 0)
