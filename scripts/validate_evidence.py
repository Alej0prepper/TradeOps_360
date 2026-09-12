"""A successful command exit is insufficient without the expected evidence."""
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
full = "--full" in sys.argv[2:]
results = re.findall(r"(\d+) failed, (\d+) error\(s\) of (\d+) tests", (root / "install.log").read_text())
if not results:
    raise AssertionError("Odoo did not publish a test result summary.")
failed, errors, count = map(int, results[-1])
if failed or errors or count < 45:
    raise AssertionError(f"Insufficient runtime evidence: {failed} failed, {errors} errors, {count} tests.")
evidence = root / "data/evidence"
required = ["concurrency.json", "verified-tradeops_ci.json", "verified-tradeops_ci_restore.json", "legacy-upgrade.json"]
if full:
    required += ["ui-smoke.json", "compose-restore.json"]
for filename in required:
    result = json.loads((evidence / filename).read_text())
    if result.get("verified") is not True:
        raise AssertionError("Unverified acceptance result: " + filename)
summary = {"runtime_tests": count, "failed": failed, "errors": errors,
           "concurrent_conversion": True, "upgrade_rehearsal": True,
           "baseline_upgrade": True, "database_and_filestore_restore": True,
           "full_automated_gate": full}
if full:
    summary.update(browser_and_pdf=True, compose_install_and_restore=True)
    (evidence / "final-result.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, sort_keys=True))
