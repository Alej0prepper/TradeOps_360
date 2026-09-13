"""Fast wrapper regression tests; the Compose rehearsal also runs real Odoo."""
import configparser
import importlib.util
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "odoo-entrypoint.py"
SPEC = importlib.util.spec_from_file_location("tradeops_entrypoint", PATH)
entrypoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entrypoint)


class TestRuntimeConfig(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.template = self.root / "template.conf"
        self.template.write_text("[options]\naddons_path = /mnt/extra-addons\n", encoding="utf-8")
        self.environ = {"PASSWORD": "db%secret", "ODOO_MASTER_PASSWORD": "master%secret"}

    def write(self):
        return Path(entrypoint.write_runtime_config(self.environ, str(self.template), str(self.root)))

    def test_secrets_and_template_options_round_trip(self):
        self.environ.update(HOST="postgres", USER="tradeops")
        result = configparser.ConfigParser(interpolation=None)
        result.read(self.write())
        self.assertEqual(result["options"]["db_password"], "db%secret")
        self.assertEqual(result["options"]["admin_passwd"], "master%secret")
        self.assertEqual(result["options"]["db_host"], "postgres")
        self.assertEqual(result["options"]["db_user"], "tradeops")
        self.assertEqual(result["options"]["addons_path"], "/mnt/extra-addons")

    def test_runtime_files_are_private_and_unique(self):
        first, second = self.write(), self.write()
        self.assertNotEqual(first, second)
        for path in (first, second):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_missing_either_secret_is_rejected_before_file_creation(self):
        for name in ("PASSWORD", "ODOO_MASTER_PASSWORD"):
            with self.subTest(name=name):
                original = self.environ.pop(name)
                with self.assertRaises(SystemExit):
                    self.write()
                self.environ[name] = original
        self.assertEqual(list(self.root.glob("tradeops-runtime-*")), [])

    def test_missing_or_invalid_template_is_rejected(self):
        self.template.unlink()
        with self.assertRaises(SystemExit):
            self.write()
        self.template.write_text("[other]\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.write()

    def test_default_database_host_and_user(self):
        result = configparser.ConfigParser(interpolation=None)
        result.read(self.write())
        self.assertEqual(result["options"]["db_host"], "db")
        self.assertEqual(result["options"]["db_user"], "odoo")


class TestCommandDispatch(unittest.TestCase):
    def assert_command(self, arguments):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(entrypoint, "write_runtime_config", return_value="/tmp/private.conf"), \
             patch.object(entrypoint.os, "execvp") as execute:
            entrypoint.main(arguments)
            execute.assert_called_once_with("odoo", ["odoo", *arguments])
            self.assertEqual(os.environ["ODOO_RC"], "/tmp/private.conf")

    def test_shell_remains_the_first_argument(self):
        self.assert_command(["shell", "-d", "tradeops_demo", "--no-http"])

    def test_implicit_and_explicit_server_commands_are_preserved(self):
        for arguments in ([], ["-d", "tradeops_dev"], ["server", "-d", "tradeops_dev"]):
            with self.subTest(arguments=arguments):
                self.assert_command(arguments)

    def test_help_and_other_commands_are_not_rewritten(self):
        for arguments in (["--help"], ["shell", "--help"], ["scaffold", "example", "/tmp"]):
            with self.subTest(arguments=arguments):
                self.assert_command(arguments)

    def test_failed_exec_removes_the_secret_file(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(entrypoint, "write_runtime_config", return_value="/tmp/private.conf"), \
             patch.object(entrypoint.os, "execvp", side_effect=FileNotFoundError), \
             patch.object(entrypoint.os, "unlink") as unlink:
            with self.assertRaises(FileNotFoundError):
                entrypoint.main(["shell"])
            unlink.assert_called_once_with("/tmp/private.conf")


if __name__ == "__main__":
    unittest.main()
