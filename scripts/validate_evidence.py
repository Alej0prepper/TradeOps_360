"""Fail CI when a successful exit did not actually produce required evidence."""
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
log = (root / "install.log").read_text()
results = re.findall(r"(\d+) failed, (\d+) error\(s\) of (\d+) tests", log)
if not results:
    raise AssertionError("Odoo did not publish a test result summary.")
failed, errors, count = map(int, results[-1])
if failed or errors or count < 39:
    raise AssertionError(f"Insufficient runtime evidence: {failed} failed, {errors} errors, {count} tests.")
evidence = root / "data/evidence"
required = (
    "concurrency.json", "verified-tradeops_ci.json",
    "verified-tradeops_ci_restore.json", "legacy-upgrade.json",
)
for filename in required:
    result = json.loads((evidence / filename).read_text())
    if result.get("verified") is not True:
        raise AssertionError("Unverified acceptance result: " + filename)
print(json.dumps({"runtime_tests": count, "failed": failed, "errors": errors,
                  "concurrent_conversion": True, "upgrade_rehearsal": True,
                  "baseline_upgrade": True, "database_and_filestore_restore": True}, sort_keys=True))
