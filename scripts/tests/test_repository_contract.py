"""Repository-level checks catch broken runbooks before starting Odoo."""
from pathlib import Path
import re
import subprocess
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


class TestRepositoryContract(unittest.TestCase):
    def test_shell_scripts_parse(self):
        for path in sorted((ROOT / "scripts").glob("*.sh")):
            with self.subTest(script=path.name):
                subprocess.run(["bash", "-n", str(path)], check=True, capture_output=True, text=True)

    def test_workflow_and_shell_script_references_exist(self):
        files = list((ROOT / ".github/workflows").glob("*.yml")) + list((ROOT / "scripts").glob("*.sh"))
        for path in files:
            for relative in re.findall(r"(?<![\w/])scripts/[\w./-]+\.(?:py|sh|cjs)", path.read_text()):
                with self.subTest(source=str(path.relative_to(ROOT)), reference=relative):
                    self.assertTrue((ROOT / relative).is_file(), relative)

    def test_relative_documentation_links_resolve(self):
        files = [ROOT / "README.md"] + list((ROOT / "docs").rglob("*.md"))
        for path in files:
            for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", path.read_text()):
                link = urlsplit(target)
                if link.scheme or link.netloc or not link.path:
                    continue
                with self.subTest(document=str(path.relative_to(ROOT)), link=target):
                    self.assertTrue((path.parent / unquote(link.path)).exists(), target)

    def test_five_specs_and_all_objectives_are_documented(self):
        addons = sorted(p.name for p in (ROOT / "custom_addons").iterdir() if (p / "__manifest__.py").is_file())
        self.assertEqual(len(addons), 5)
        for addon in addons:
            text = (ROOT / "docs/modules" / (addon + ".md")).read_text()
            for section in range(14):
                self.assertRegex(text, rf"(?m)^## {section}\. ")
        objectives = (ROOT / "docs/phase-1-objectives.md").read_text()
        self.assertEqual(set(re.findall(r"(?m)^### (F1-\d{2})\.", objectives)),
                         {f"F1-{number:02}" for number in range(1, 23)})

    def test_information_alerts_have_accessible_roles(self):
        for path in (ROOT / "custom_addons").rglob("*.xml"):
            for element in ET.parse(path).iter():
                if "alert" in element.get("class", "").split():
                    with self.subTest(view=str(path.relative_to(ROOT))):
                        self.assertIn(element.get("role"), ("status", "alert", "alertdialog"))
