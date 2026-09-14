"""Synthetic fixtures test the evidence checker, not the Odoo application."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("evidence", Path(__file__).resolve().parents[1] / "validate_evidence.py")
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)


class TestEvidenceGate(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        source = self.root / "custom_addons/trade_example/tests"
        source.mkdir(parents=True)
        (source / "test_example.py").write_text("class TestExample:\n    def test_rule(self): pass\n")
        self.log = self.root / "install.log"
        self.log.write_text("odoo.addons.trade_example.tests.test_example: Starting TestExample.test_rule ...\n0 failed, 0 error(s) of 1 tests\n")
        (self.root / "runtime.txt").write_text("pinned-image\n" + "a" * 40 + "\n")
        target = self.root / "data/evidence"
        target.mkdir(parents=True)
        for name in ("concurrency", "verified-tradeops_ci", "verified-tradeops_ci_restore", "legacy-upgrade", "ui-smoke", "compose-restore"):
            (target / (name + ".json")).write_text(json.dumps({"verified": True}))
        documents = [("import", "trade.import"), ("presale", "trade.presale"), ("sale", "sale.order"),
                     ("distribution", "trade.distribution"), ("incident", "trade.delivery.incident"),
                     ("reconciliation", "trade.reconciliation")]
        manifest = {label + "_id": index for index, (label, _) in enumerate(documents, 1)}
        forms = [{"model": model, "id": manifest[label + "_id"], "visible": True,
                  "fresh_page": True, "record_identity_verified": True,
                  "checked_field": "description" if label == "incident" else "name",
                  "expected_value": label, "observed_value": label} for label, model in documents]
        (target / "acceptance-manifest.json").write_text(json.dumps(manifest))
        (target / "ui-smoke.json").write_text(json.dumps({
            "verified": True, "forms": forms, "consultation_identity_verified": True,
        }))
        environment = patch.dict(os.environ, {"GITHUB_SHA": "a" * 40})
        environment.start()
        self.addCleanup(environment.stop)

    def validate(self, full=False):
        return evidence.validate(self.root, repository=self.root, full=full)

    def test_complete_evidence_identifies_source_and_tests(self):
        result = self.validate(full=True)
        self.assertEqual(result["expected_model_tests"], 1)
        self.assertEqual(result["missing_model_tests"], 0)
        self.assertEqual(result["source_revision"], "a" * 40)
        self.assertTrue(result["full_automated_gate"])

    def test_green_total_without_expected_test_execution_is_rejected(self):
        self.log.write_text("0 failed, 0 error(s) of 99 tests\n")
        with self.assertRaisesRegex(AssertionError, "test_rule"):
            self.validate()

    def test_failure_or_missing_summary_is_rejected(self):
        original = self.log.read_text()
        for text in ("No summary", original.replace("0 failed", "1 failed")):
            with self.subTest(text=text):
                self.log.write_text(text)
                with self.assertRaises(AssertionError):
                    self.validate()

    def test_another_revision_is_rejected(self):
        with patch.dict(os.environ, {"GITHUB_SHA": "b" * 40}):
            with self.assertRaisesRegex(AssertionError, "another source revision"):
                self.validate()

    def test_missing_or_unverified_acceptance_is_rejected(self):
        path = self.root / "data/evidence/compose-restore.json"
        path.write_text('{"verified": false}')
        with self.assertRaisesRegex(AssertionError, "compose-restore"):
            self.validate(full=True)
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.validate(full=True)

    def test_visible_form_without_identity_proof_is_rejected(self):
        path = self.root / "data/evidence/ui-smoke.json"
        original = json.loads(path.read_text())
        for change in ({"record_identity_verified": False}, {"observed_value": "previous document"}):
            with self.subTest(change=change):
                data = json.loads(json.dumps(original))
                data["forms"][0].update(change)
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(AssertionError, "record identity"):
                    self.validate(full=True)

    def test_wrong_or_missing_browser_document_is_rejected(self):
        path = self.root / "data/evidence/ui-smoke.json"
        data = json.loads(path.read_text())
        data["forms"][0]["id"] = 999
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(AssertionError, "expected documents"):
            self.validate(full=True)
        data["forms"].pop()
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(AssertionError, "expected documents"):
            self.validate(full=True)
