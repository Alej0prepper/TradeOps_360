"""Require executed tests and acceptance evidence from the checked-out revision."""
import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def expected_tests(repository: Path) -> set[tuple[str, str, str, str]]:
    expected = set()
    for path in (repository / "custom_addons").glob("*/tests/test_*.py"):
        module = path.parent.parent.name
        for cls in ast.parse(path.read_text()).body:
            if isinstance(cls, ast.ClassDef):
                for method in cls.body:
                    if isinstance(method, ast.FunctionDef) and method.name.startswith("test_"):
                        expected.add((module, path.stem, cls.name, method.name))
    if not expected:
        raise AssertionError("No model tests were discovered in the checked-out source.")
    return expected


def validate(root: Path, repository: Path = ROOT, full: bool = False) -> dict:
    log = (root / "install.log").read_text()
    results = re.findall(r"(\d+) failed, (\d+) error\(s\) of (\d+) tests", log)
    if not results:
        raise AssertionError("Odoo did not publish a test result summary.")
    failed, errors, count = map(int, results[-1])
    expected = expected_tests(repository)
    executed = set(re.findall(
        r"odoo\.addons\.(trade_\w+)\.tests\.(\w+): Starting (\w+)\.(test_\w+) ", log,
    ))
    missing = expected - executed
    if failed or errors or count < len(expected) or missing:
        raise AssertionError(
            f"Incomplete runtime evidence: {failed} failed, {errors} errors, {count} tests; "
            f"missing={sorted(missing)}"
        )
    revision = (root / "runtime.txt").read_text().splitlines()[-1]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise AssertionError("Missing source revision in runtime evidence.")
    if os.environ.get("GITHUB_SHA") and revision != os.environ["GITHUB_SHA"]:
        raise AssertionError("Evidence belongs to another source revision.")
    evidence = root / "data/evidence"
    required = ["concurrency.json", "verified-tradeops_ci.json",
                "verified-tradeops_ci_restore.json", "legacy-upgrade.json"]
    if full:
        required += ["ui-smoke.json", "compose-restore.json"]
    for filename in required:
        result = json.loads((evidence / filename).read_text())
        if result.get("verified") is not True:
            raise AssertionError("Unverified acceptance result: " + filename)
    summary = {"source_revision": revision, "runtime_tests": count,
               "expected_model_tests": len(expected), "missing_model_tests": 0,
               "failed": failed, "errors": errors, "concurrent_conversion": True,
               "upgrade_rehearsal": True, "baseline_upgrade": True,
               "database_and_filestore_restore": True, "full_automated_gate": full}
    if full:
        summary.update(browser_and_pdf=True, compose_install_and_restore=True)
        (evidence / "final-result.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(validate(Path(sys.argv[1]), full="--full" in sys.argv[2:]), sort_keys=True))
