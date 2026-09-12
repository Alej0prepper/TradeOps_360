from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestTradeDistribution(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})

    def _create_distribution(self):
        sale_order = self.env["sale.order"].create(
            {"partner_id": self.customer.id}
        )
        return self.env["trade.distribution"].create(
            {
                "name": "DIST-TEST",
                "sale_order_id": sale_order.id,
                "expected_quantity": 1.0,
            }
        )

    def test_reporting_incident_creates_record_and_audit_message(self):
        distribution = self._create_distribution()

        incident = distribution.report_incident(
            "damaged_goods", "Packaging was damaged."
        )

        self.assertEqual(incident.distribution_id, distribution)
        self.assertTrue(
            distribution.message_ids.filtered(
                lambda message: "Damaged Goods" in message.body
            )
        )

    def test_incident_requires_description_without_side_effects(self):
        distribution = self._create_distribution()
        messages_before = distribution.message_ids

        with self.assertRaises(ValidationError):
            distribution.report_incident("other", " ")

        self.assertFalse(distribution.incident_ids)
        self.assertEqual(distribution.message_ids, messages_before)
