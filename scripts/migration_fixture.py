"""Seed the historical baseline, or verify its upgrade without inventing stock."""
import base64
import hashlib
import json
import os
from pathlib import Path

from odoo import fields

if env.cr.dbname != "tradeops_ci_legacy":
    raise RuntimeError("Legacy rehearsal is restricted to tradeops_ci_legacy.")
output = Path("/var/lib/odoo/evidence")
output.mkdir(parents=True, exist_ok=True)
mode = os.environ.get("TRADEOPS_CHECK", "legacy_seed")
if mode == "legacy_seed":
    customer = env["res.partner"].create({"name": "Historical test customer"})
    supplier = env["res.partner"].create({"name": "Historical test supplier", "supplier_rank": 1})
    product = env["product.product"].create({"name": "Historical test product", "detailed_type": "product"})
    ports = env["trade.port"].create([{"name": "Old origin", "code": "old-ori"}, {"name": "Old destination", "code": "old-dst"}])
    values = {"name": "New", "customer_id": customer.id, "origin_port_id": ports[0].id,
              "destination_port_id": ports[1].id,
              "line_ids": [fields.Command.create({"product_id": product.id, "quantity": 2, "unit_purchase_price": 100})]}
    first = env["trade.import"].create(dict(values, state="completed"))
    second = env["trade.import"].create(values)
    presale = env["trade.presale"].create({
        "import_id": first.id, "customer_id": customer.id, "state": "confirmed",
        "line_ids": [fields.Command.create({"product_id": product.id, "quantity": 2, "unit_price": 125})],
    })
    sale = presale.action_convert_to_sale()
    sale.action_confirm()
    distribution = env["trade.distribution"].create({"sale_order_id": sale.id, "expected_quantity": 2})
    statement = env["trade.reconciliation"].create({"supplier_id": supplier.id,
        "line_ids": [fields.Command.create({"sale_line_id": sale.order_line.id})]})
    statement.action_reconcile()
    payload = b"Historical baseline attachment retained during phase-one migration.\n"
    attachment = env["ir.attachment"].create({"name": "historical.txt", "res_model": "trade.import",
        "res_id": first.id, "datas": base64.b64encode(payload), "mimetype": "text/plain"})
    manifest = {"import_ids": [first.id, second.id], "presale_id": presale.id, "sale_id": sale.id,
        "distribution_id": distribution.id, "reconciliation_id": statement.id,
        "commercial_total": statement.total_amount, "attachment_id": attachment.id,
        "attachment_sha256": hashlib.sha256(payload).hexdigest()}
    env.cr.commit()
    (output / "legacy-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("TRADEOPS_LEGACY_SEEDED", json.dumps(manifest, sort_keys=True))
elif mode == "legacy_verify":
    data = json.loads((output / "legacy-manifest.json").read_text())
    imports = env["trade.import"].browse(data["import_ids"])
    assert len(set(imports.mapped("name"))) == 2
    assert all(record.legacy_original_reference == "New" and record.legacy_review_required for record in imports)
    assert imports[0].state == "completed" and not imports[0].purchase_order_ids
    assert imports[0].legacy_payload["state"] == "completed"
    presale = env["trade.presale"].browse(data["presale_id"])
    assert presale.sale_order_id.id == data["sale_id"] and presale.state == "converted"
    assert presale.line_ids.import_line_id == imports[0].line_ids
    assert presale.sale_order_id.trade_presale_id == presale
    assert presale.sale_order_id.order_line.trade_presale_line_id == presale.line_ids
    distribution = env["trade.distribution"].browse(data["distribution_id"])
    assert distribution.legacy_review_required and distribution.legacy_payload["expected_quantity"] == 2
    statement = env["trade.reconciliation"].browse(data["reconciliation_id"])
    assert statement.state == "confirmed" and statement.legacy_review_required
    assert statement.total_amount == data["commercial_total"]
    assert statement.line_ids.snapshot_amount == data["commercial_total"]
    assert not statement.confirmed_at and not statement.confirmed_by_id
    attachment = env["ir.attachment"].browse(data["attachment_id"])
    assert hashlib.sha256(base64.b64decode(attachment.datas)).hexdigest() == data["attachment_sha256"]
    assert not env["stock.move"].search([("state", "=", "done")])
    result = {"verified": True, "historical_records_preserved": True, "review_flags": True,
              "physical_receipts_fabricated": False, "legacy_references": imports.mapped("name")}
    (output / "legacy-upgrade.json").write_text(json.dumps(result, indent=2) + "\n")
    print("TRADEOPS_LEGACY_UPGRADE_VERIFIED", json.dumps(result, sort_keys=True))
else:
    raise RuntimeError("Unsupported migration mode: " + mode)
