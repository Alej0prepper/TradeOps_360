"""Two independent transactions converting the same committed CI presale.

Run after acceptance.py in a disposable database. This is intentionally not a
TransactionCase simulation: each worker opens and commits its own real cursor.
"""
import concurrent.futures
import json
import os
import threading
from pathlib import Path

from psycopg2.errors import DeadlockDetected, SerializationFailure
from odoo import api

if not env.cr.dbname.startswith("tradeops_ci"):
    raise RuntimeError("Concurrency rehearsal is restricted to disposable CI databases.")
output = Path(os.environ.get("TRADEOPS_EVIDENCE_DIR", "/var/lib/odoo/evidence"))
manifest = json.loads((output / "acceptance-manifest.json").read_text())
registry = env.registry
barrier = threading.Barrier(2, timeout=30)


def convert(worker):
    retries = 0
    for attempt in range(4):
        try:
            with registry.cursor() as cr:
                cr.execute("SET LOCAL lock_timeout = '15s'")
                cr.execute("SET LOCAL statement_timeout = '45s'")
                session = api.Environment(cr, manifest["operator_id"], {
                    "allowed_company_ids": [manifest["company_id"]],
                })
                presale = session["trade.presale"].browse(manifest["concurrent_presale_id"])
                initial_state = presale.state
                if attempt == 0:
                    if initial_state != "confirmed":
                        raise AssertionError("Both first attempts must observe the confirmed presale.")
                    barrier.wait()
                action = presale.action_convert_to_sale()
                cr.commit()
                return {"worker": worker, "sale_id": action["res_id"], "retries": retries}
        except (SerializationFailure, DeadlockDetected):
            # Retry the complete request with a fresh transaction/snapshot.
            retries += 1
    raise AssertionError("Conversion exceeded the retry budget.")


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(convert, worker) for worker in (1, 2)]
    results = [future.result(timeout=90) for future in futures]
if results[0]["sale_id"] != results[1]["sale_id"]:
    raise AssertionError("Concurrent conversion created different quotations.")
with registry.cursor() as cr:
    fresh = api.Environment(cr, manifest["operator_id"], {
        "allowed_company_ids": [manifest["company_id"]],
    })
    presale = fresh["trade.presale"].browse(manifest["concurrent_presale_id"])
    orders = fresh["sale.order"].search([("trade_presale_id", "=", presale.id)])
    if len(orders) != 1 or presale.sale_order_id != orders or presale.state != "converted":
        raise AssertionError("Concurrent conversion left inconsistent provenance.")
result = {"workers": results, "separate_transactions": True, "quotation_count": 1, "verified": True}
(output / "concurrency.json").write_text(json.dumps(result, indent=2) + "\n")
print("TRADEOPS_CONCURRENCY_VERIFIED", json.dumps(result, sort_keys=True))
