from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestTradeCore(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(cls.env, login="catalog_manager", groups="trade_core.group_trade_manager")
        cls.operator = new_test_user(cls.env, login="catalog_operator", groups="trade_core.group_trade_operator")
        cls.viewer = new_test_user(cls.env, login="catalog_viewer", groups="trade_core.group_trade_viewer")

    def test_catalog_is_readable_but_only_responsible_can_maintain_it(self):
        port = self.env["trade.port"].with_user(self.manager).create({"name": "Catalog port", "code": " cat "})
        self.assertEqual(port.code, "CAT")
        self.assertEqual(port.with_user(self.viewer).name, "Catalog port")
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            port.with_user(self.operator).write({"code": "OTHER"})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env["trade.port"].with_user(self.viewer).create({"name": "No", "code": "NO"})
        port.write({"active": False})
        self.assertFalse(port.active)

    def test_port_codes_are_normalized_and_database_unique(self):
        self.env["trade.port"].create({"name": "Port", "code": "UNIQUE"})
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.env["trade.port"].create({"name": "Duplicate", "code": " unique "})

    def test_port_names_and_codes_cannot_be_blank(self):
        for name, code in [(" ", "EMPTY"), ("A port", " ")]:
            with self.subTest(name=name, code=code):
                with self.assertRaises(ValidationError), self.env.cr.savepoint():
                    self.env["trade.port"].create({"name": name, "code": code})

    def test_contacts_are_extended_without_duplicate_customer_models(self):
        contact = self.env["res.partner"].create({"name": "Shared contact", "trade_code": "EXAMPLE"})
        self.assertEqual(contact.trade_code, "EXAMPLE")
        self.assertNotIn("trade.customer", self.env.registry.models)
        self.assertNotIn("trade.product", self.env.registry.models)
