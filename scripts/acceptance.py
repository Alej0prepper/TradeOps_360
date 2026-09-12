"""Run with `odoo shell --no-http -d tradeops_ci < scripts/acceptance.py`.

Synthetic acceptance data only. This is an executable rehearsal, not a module
hook. Its explicit commit publishes fixtures for the separate concurrency and
restore processes; application business methods never commit manually.
"""
import base64
import hashlib
import json
import os
from pathlib import Path

from odoo import api, fields
from odoo.exceptions import AccessError, UserError

MODE = os.environ.get("TRADEOPS_CHECK", "seed")
OUTPUT = Path(os.environ.get("TRADEOPS_EVIDENCE_DIR", "/var/lib/odoo/evidence"))
OUTPUT.mkdir(parents=True, exist_ok=True)
DB = env.cr.dbname
if not (DB.startswith("tradeops_ci") or (DB.endswith("_demo") and os.environ.get("TRADEOPS_ALLOW_DEMO") == "1")):
    raise RuntimeError("Acceptance scripts require a disposable tradeops_ci* or explicitly authorized *_demo database.")


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def user(login, group, company):
    values = {
        "name": login.replace("_", " ").title(), "login": login,
        "company_id": company.id, "company_ids": [fields.Command.set(company.ids)],
        "groups_id": [fields.Command.set(env.ref(group).ids)],
    }
    if os.environ.get("TRADEOPS_DEMO_PASSWORD"):
        values["password"] = os.environ["TRADEOPS_DEMO_PASSWORD"]
    return env["res.users"].with_context(no_reset_password=True).create(values)


def finish_picking(picking, operator, quantities=None):
    picking = picking.with_user(operator)
    picking.action_assign()
    for move in picking.move_ids.filtered(lambda item: item.state not in ("done", "cancel")):
        move.quantity = (quantities or {}).get(move.product_id.id, move.product_uom_qty)
        move.picked = True
        if move.quantity and move.product_id.tracking == "lot":
            lot_name = "PHASE1-" + str(move.product_id.id)
            lot = env["stock.lot"].with_user(operator).search([
                ("name", "=", lot_name), ("product_id", "=", move.product_id.id),
                ("company_id", "=", picking.company_id.id),
            ], limit=1)
            for line in move.move_line_ids:
                if not line.lot_id:
                    if lot:
                        line.lot_id = lot
                    else:
                        line.lot_name = lot_name
    result = picking.with_context(skip_backorder=True).button_validate()
    check(picking.state == "done", "Standard stock validation did not finish: %r" % result)
    return picking


def return_quantity(picking, product, quantity, operator):
    wizard = env["stock.return.picking"].with_user(operator).create({"picking_id": picking.id})
    for line in wizard.product_return_moves:
        line.quantity = quantity if line.product_id == product else 0
    action = wizard.create_returns()
    returned = env["stock.picking"].browse(action["res_id"])
    returned.with_user(operator).move_ids.write({"to_refund": True})
    return finish_picking(returned, operator)


def make_import(customer, supplier, warehouse, ports, product, operator, quantity=2):
    return env["trade.import"].with_user(operator).create({
        "customer_id": customer.id, "supplier_id": supplier.id,
        "warehouse_id": warehouse.id, "origin_port_id": ports[0].id,
        "destination_port_id": ports[1].id,
        "line_ids": [fields.Command.create({"product_id": product.id, "quantity": quantity, "unit_purchase_price": 10})],
    })


def start_import(operation, operator, manager):
    operation.with_user(operator).action_submit()
    operation.with_user(manager).action_validate()
    operation.with_user(manager).action_start_transit()


def presale(operation, customer, pricelist, quantities, operator):
    return env["trade.presale"].with_user(operator).create({
        "import_id": operation.id, "customer_id": customer.id, "pricelist_id": pricelist.id,
        "line_ids": [fields.Command.create({
            "import_line_id": line.id,
            "quantity": quantities.get(line.product_id.id, line.quantity),
            "unit_price": line.unit_purchase_price * 1.25,
        }) for line in operation.line_ids],
    })


def seed():
    check(not env["res.users"].search([("login", "=", "phase1_operator")]), "Fixtures already exist; use verify or a fresh database.")
    company = env.company
    second_company = env["res.company"].create({"name": "Phase 1 Company B"})
    operator = user("phase1_operator", "trade_core.group_trade_operator", company)
    manager = user("phase1_responsible", "trade_core.group_trade_manager", company)
    viewer = user("phase1_viewer", "trade_core.group_trade_viewer", company)
    other = user("phase1_company_b", "trade_core.group_trade_operator", second_company)
    outsider = user("phase1_outsider", "base.group_user", company)
    customer = env["res.partner"].create({"name": "Phase 1 Customer", "trade_code": "DEMO-C"})
    supplier = env["res.partner"].create({"name": "Phase 1 Supplier", "supplier_rank": 1, "trade_code": "DEMO-S"})
    ports = env["trade.port"].with_user(manager).create([
        {"name": "Demonstration Origin", "code": "DEMO-ORI"},
        {"name": "Demonstration Destination", "code": "DEMO-DST"},
    ])
    warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
    check(bool(warehouse), "Configure a company warehouse before the demonstration.")
    products = env["product.product"].create([
        {"name": "Phase 1 Product A", "detailed_type": "product"},
        {"name": "Phase 1 Product B (lot)", "detailed_type": "product", "tracking": "lot"},
    ])
    product_a, product_b = products
    pricelist = env["product.pricelist"].create({
        "name": "Phase 1 Company Currency", "company_id": company.id, "currency_id": company.currency_id.id,
    })
    operation = make_import(customer, supplier, warehouse, ports, product_a, operator, 10)
    operation.line_ids.unit_purchase_price = 100
    operation.write({
        "line_ids": [fields.Command.create({"product_id": product_b.id, "quantity": 2, "unit_purchase_price": 300})],
        "expense_ids": [fields.Command.create({"expense_type": "freight", "amount": 160})],
    })
    check(operation.landed_total == 1760, "Operational total must include allocated expenses.")
    start_import(operation, operator, manager)
    commitment = presale(operation, customer, pricelist, {}, operator)
    commitment.action_confirm()
    extra = presale(operation, customer, pricelist, {product_a.id: 1, product_b.id: 1}, operator)
    extra.action_confirm()
    check(extra.is_overcommitted, "Overcommitment must be visible, not silently ignored.")
    extra.action_cancel()
    for forbidden in (viewer, other, outsider):
        with env.cr.savepoint():
            try:
                operation.with_user(forbidden).action_validate()
            except AccessError:
                pass
            else:
                raise AssertionError("Unauthorized user executed an approval.")
    for forbidden in (other, outsider):
        with env.cr.savepoint():
            try:
                operation.with_user(forbidden).read(["name"])
            except AccessError:
                pass
            else:
                raise AssertionError("Company or role isolation failed.")
    finish_picking(operation.picking_ids, operator, {product_a.id: 6, product_b.id: 1})
    check(operation.state == "partially_received", "First receipt must remain partial.")
    pending_receipt = operation.picking_ids.filtered(lambda item: item.state not in ("done", "cancel"))
    finish_picking(pending_receipt, operator)
    check(operation.state == "completed", "Import must close from actual stock receipts.")
    quotation_action = commitment.action_convert_to_sale()
    check(commitment.action_convert_to_sale()["res_id"] == quotation_action["res_id"], "Repeated conversion created another quotation.")
    order = commitment.sale_order_id
    order.with_user(operator).action_confirm()
    distribution = env["trade.distribution"].with_user(operator).create({"sale_order_id": order.id})
    distribution.action_start()
    first_delivery = order.picking_ids
    first_delivery.with_user(operator).action_assign()
    check(all(line.delivered_quantity == 0 for line in distribution.line_ids), "Reservations were counted as delivered.")
    finish_picking(first_delivery, operator, {product_a.id: 6, product_b.id: 1})
    incident_action = distribution.action_report_incident()
    wizard = env[incident_action["res_model"]].with_user(operator).with_context(incident_action["context"]).create({
        "incident_type": "documentation", "description": "Customer requested a corrected delivery reference.",
    })
    wizard.action_confirm()
    pending_delivery = order.picking_ids.filtered(lambda item: item.state not in ("done", "cancel"))
    finish_picking(pending_delivery, operator)
    incident = distribution.incident_ids
    incident.with_user(manager).write({"resolution": "Reference corrected and accepted by the customer."})
    incident.with_user(manager).action_resolve()
    distribution.with_user(manager).action_close()
    returned = return_quantity(first_delivery, product_a, 2, operator)
    check(distribution.state == "active", "A customer return must reopen pending distribution.")
    check(distribution.line_ids.filtered(lambda line: line.product_id == product_a).delivered_quantity == 8, "Customer return did not reduce net delivery.")
    return_quantity(returned, product_a, 2, operator)
    check(all(line.pending_quantity == 0 for line in distribution.line_ids), "Re-delivery did not restore fulfilled quantities.")
    distribution.with_user(manager).action_close()
    reconciliation = env["trade.reconciliation"].with_user(operator).create({
        "supplier_id": supplier.id,
        "line_ids": [fields.Command.create({"sale_line_id": line.id}) for line in order.order_line],
    })
    reconciliation.with_user(manager).action_reconcile()
    check(reconciliation.total_amount == 2000, "Commercial statement must sum sales subtotals.")
    adjustment_action = reconciliation.with_user(manager).action_add_adjustment()
    correction = env[adjustment_action["res_model"]].with_user(manager).with_context(adjustment_action["context"]).create({
        "amount": -50, "reason": "Explicit demonstration correction; not a supplier payment.",
    })
    correction.action_apply()
    correction.action_apply()
    check(reconciliation.total_amount == 2000 and reconciliation.net_total == 1950, "A correction changed the frozen statement or was applied twice.")
    payload = b"TradeOps phase-one database and filestore restoration evidence.\n"
    attachment = env["ir.attachment"].with_user(operator).create({
        "name": "phase-1-evidence.txt", "res_model": "trade.import", "res_id": operation.id,
        "datas": base64.b64encode(payload), "mimetype": "text/plain",
    })
    concurrent_import = make_import(customer, supplier, warehouse, ports, product_a, operator)
    start_import(concurrent_import, operator, manager)
    finish_picking(concurrent_import.picking_ids, operator)
    concurrent_presale = presale(concurrent_import, customer, pricelist, {}, operator)
    concurrent_presale.action_confirm()
    report = env.ref("trade_import.action_report_trade_import").with_user(operator)
    html, _kind = report._render_qweb_html(report.report_name, operation.ids)
    (OUTPUT / "import-summary.html").write_bytes(html)
    manifest = {
        "schema": 1, "company_id": company.id, "second_company_id": second_company.id,
        "operator_id": operator.id, "manager_id": manager.id, "viewer_id": viewer.id,
        "other_user_id": other.id, "outsider_id": outsider.id,
        "import_id": operation.id, "import_name": operation.name,
        "presale_id": commitment.id, "sale_id": order.id, "distribution_id": distribution.id,
        "incident_id": incident.id, "reconciliation_id": reconciliation.id,
        "attachment_id": attachment.id, "attachment_sha256": hashlib.sha256(payload).hexdigest(),
        "concurrent_presale_id": concurrent_presale.id,
        "expected_operational_total": 1760, "expected_commercial_total": 2000,
        "expected_adjusted_total": 1950,
    }
    env.cr.commit()
    (OUTPUT / "acceptance-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("TRADEOPS_ACCEPTANCE_SEEDED", json.dumps(manifest, sort_keys=True))


def verify():
    manifest = json.loads((OUTPUT / "acceptance-manifest.json").read_text())
    operation = env["trade.import"].browse(manifest["import_id"])
    commitment = env["trade.presale"].browse(manifest["presale_id"])
    distribution = env["trade.distribution"].browse(manifest["distribution_id"])
    statement = env["trade.reconciliation"].browse(manifest["reconciliation_id"])
    attachment = env["ir.attachment"].browse(manifest["attachment_id"])
    check(operation.name == manifest["import_name"] and operation.state == "completed", "Import identity/state changed.")
    check(operation.landed_total == manifest["expected_operational_total"], "Operational costs changed.")
    check(all(line.received_quantity >= line.quantity for line in operation.line_ids), "Receipt history is incomplete.")
    check(commitment.state == "converted" and commitment.sale_order_id.id == manifest["sale_id"], "Quotation provenance changed.")
    check(distribution.state == "closed" and all(line.pending_quantity == 0 for line in distribution.line_ids), "Delivery/return history changed.")
    check(env["trade.delivery.incident"].browse(manifest["incident_id"]).state == "resolved", "Incident resolution changed.")
    check(statement.total_amount == manifest["expected_commercial_total"], "Frozen commercial total changed.")
    check(statement.net_total == manifest["expected_adjusted_total"] and len(statement.adjustment_ids) == 1, "Correction history changed.")
    check(hashlib.sha256(base64.b64decode(attachment.datas)).hexdigest() == manifest["attachment_sha256"], "Filestore attachment checksum changed.")
    check(bool(attachment.store_fname), "Acceptance must cover a filestore-backed attachment.")
    result = {"database": DB, "verified": True, "import": operation.name, "attachment_sha256": manifest["attachment_sha256"]}
    (OUTPUT / ("verified-" + DB + ".json")).write_text(json.dumps(result, indent=2) + "\n")
    print("TRADEOPS_ACCEPTANCE_VERIFIED", json.dumps(result, sort_keys=True))


if MODE == "seed":
    seed()
elif MODE == "verify":
    verify()
else:
    raise RuntimeError("Unsupported acceptance mode: " + MODE)
