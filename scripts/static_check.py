"""Dependency-free syntax, manifest and ACL structural checks (not runtime tests)."""
import ast
import csv
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
python_count = xml_count = test_count = 0
for path in (root / "custom_addons").rglob("*.py"):
    module = ast.parse(path.read_text(), filename=str(path))
    python_count += 1
    test_count += sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_") for node in ast.walk(module))
for path in (root / "custom_addons").rglob("*.xml"):
    ET.parse(path)
    xml_count += 1
for path in (root / "custom_addons").glob("*/__manifest__.py"):
    manifest = ast.literal_eval(path.read_text())
    if not manifest["version"].startswith("17.0."):
        raise AssertionError("Unexpected Odoo version: " + str(path))
    for key in ("data", "demo"):
        for relative in manifest.get(key, []):
            if not (path.parent / relative).is_file():
                raise AssertionError("Missing manifest file: " + relative)
    access = path.parent / "security/ir.model.access.csv"
    for row in csv.DictReader(access.open()):
        if not row["group_id:id"]:
            raise AssertionError("Ungrouped ACL: " + row["id"])
        for key in ("perm_read", "perm_write", "perm_create", "perm_unlink"):
            if row[key] not in ("0", "1"):
                raise AssertionError("Invalid ACL permission: " + row["id"])
for path in (root / "scripts").glob("*.py"):
    ast.parse(path.read_text(), filename=str(path))
print(f"Static validation: {python_count} Python files, {xml_count} XML files, {test_count} test methods.")
print("Static checks do not replace installing and testing the modules in Odoo.")
