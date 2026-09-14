"""Explicit SQL used only before/after schema upgrades, never normal operations.

The pre-upgrade database and filestore remain the recovery source. Ambiguous
historical relationships abort the upgrade rather than inventing provenance.
"""
import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)
DOCUMENT_TABLES = ("trade_import", "trade_presale", "trade_distribution", "trade_reconciliation")


def table_exists(cr, table):
    cr.execute("SELECT to_regclass(%s)", (table,))
    return bool(cr.fetchone()[0])


def assert_empty(cr, query, message):
    cr.execute(query)
    rows = cr.fetchmany(10)
    if rows:
        raise RuntimeError(message + ". First affected records: " + repr(rows))


def prepare_core(cr):
    for table in ("trade_import", "trade_reconciliation"):
        if table_exists(cr, table):
            assert_empty(cr, SQL(
                "SELECT t.id FROM %s t JOIN res_company c ON c.id=t.company_id WHERE t.currency_id<>c.currency_id",
                SQL.identifier(table),
            ), "Phase 1 cannot silently relabel foreign-currency historical amounts; review currency migration first")
    if table_exists(cr, "trade_port"):
        assert_empty(cr, "SELECT id FROM trade_port WHERE trim(coalesce(code,''))='' OR trim(coalesce(name,''))=''",
                     "Fix blank port names/codes before upgrading")
        assert_empty(cr, "SELECT upper(trim(code)), array_agg(id) FROM trade_port GROUP BY upper(trim(code)) HAVING count(*)>1",
                     "Resolve normalized port-code collisions before upgrading")
        cr.execute("UPDATE trade_port SET code=upper(trim(code))")
    for table in DOCUMENT_TABLES:
        if not table_exists(cr, table):
            continue
        cr.execute(SQL("ALTER TABLE %s ADD COLUMN IF NOT EXISTS legacy_original_reference varchar", SQL.identifier(table)))
        cr.execute(SQL("ALTER TABLE %s ADD COLUMN IF NOT EXISTS legacy_payload jsonb", SQL.identifier(table)))
        cr.execute(SQL("ALTER TABLE %s ADD COLUMN IF NOT EXISTS legacy_review_required boolean DEFAULT false", SQL.identifier(table)))
        cr.execute(SQL(
            "UPDATE %s t SET legacy_original_reference=name, "
            "legacy_payload=to_jsonb(t)-'legacy_payload', legacy_review_required=true "
            "WHERE legacy_payload IS NULL", SQL.identifier(table),
        ))
        cr.execute(SQL(
            "WITH refs AS (SELECT id,name,row_number() OVER(PARTITION BY company_id,name ORDER BY id) AS n FROM %s) "
            "UPDATE %s t SET name=%s || t.id::text FROM refs r WHERE t.id=r.id "
            "AND (r.n>1 OR trim(coalesce(r.name,''))='' OR r.name='New')",
            SQL.identifier(table), SQL.identifier(table), "LEGACY-" + table.replace("trade_", "").upper() + "-",
        ))
        assert_empty(cr, SQL("SELECT company_id,name FROM %s GROUP BY company_id,name HAVING count(*)>1", SQL.identifier(table)),
                     "Resolve historical reference collisions before upgrading")
        _logger.warning("Historical %s records retained with review flags and immutable source snapshots", table)


def prepare_presales(cr):
    if not table_exists(cr, "trade_presale_line"):
        return
    cr.execute("ALTER TABLE trade_presale_line ADD COLUMN IF NOT EXISTS import_line_id integer")
    assert_empty(cr, """
        SELECT p.id, count(i.id) FROM trade_presale_line p
        JOIN trade_presale h ON h.id=p.presale_id
        LEFT JOIN trade_import_line i ON i.import_id=h.import_id AND i.product_id=p.product_id
        WHERE p.import_line_id IS NULL GROUP BY p.id HAVING count(i.id)<>1
    """, "Presale products need exactly one historical import source; map ambiguous or missing sources before upgrading")
    cr.execute("""
        UPDATE trade_presale_line p SET import_line_id=i.id
        FROM trade_presale h, trade_import_line i
        WHERE p.presale_id=h.id AND i.import_id=h.import_id AND i.product_id=p.product_id
        AND p.import_line_id IS NULL
    """)
    cr.execute("ALTER TABLE sale_order ADD COLUMN IF NOT EXISTS trade_presale_id integer")
    cr.execute("ALTER TABLE sale_order_line ADD COLUMN IF NOT EXISTS trade_presale_line_id integer")
    assert_empty(cr, "SELECT sale_order_id,array_agg(id) FROM trade_presale WHERE sale_order_id IS NOT NULL GROUP BY sale_order_id HAVING count(*)>1",
                 "One historical quotation is linked to multiple presales")
    cr.execute("UPDATE sale_order s SET trade_presale_id=p.id FROM trade_presale p WHERE p.sale_order_id=s.id AND s.trade_presale_id IS NULL")
    assert_empty(cr, """
        SELECT s.id,count(p.id) FROM sale_order_line s
        JOIN sale_order h ON h.id=s.order_id
        LEFT JOIN trade_presale_line p ON p.presale_id=h.trade_presale_id AND p.product_id=s.product_id
        WHERE h.trade_presale_id IS NOT NULL AND s.display_type IS NULL
        GROUP BY s.id HAVING count(p.id)<>1
    """, "Historical quotation lines require unambiguous presale product provenance")
    assert_empty(cr, """
        SELECT p.id,count(s.id) FROM trade_presale_line p
        JOIN trade_presale h ON h.id=p.presale_id
        JOIN sale_order_line s ON s.order_id=h.sale_order_id AND s.product_id=p.product_id AND s.display_type IS NULL
        GROUP BY p.id HAVING count(s.id)>1
    """, "Multiple historical sale lines refer to a single presale line")
    cr.execute("""
        UPDATE sale_order_line s SET trade_presale_line_id=p.id
        FROM sale_order h, trade_presale_line p
        WHERE s.order_id=h.id AND p.presale_id=h.trade_presale_id AND p.product_id=s.product_id
        AND s.display_type IS NULL AND s.trade_presale_line_id IS NULL
    """)
    cr.execute("ALTER TABLE trade_presale ADD COLUMN IF NOT EXISTS pricelist_id integer")
    cr.execute("UPDATE trade_presale p SET pricelist_id=s.pricelist_id FROM sale_order s WHERE p.sale_order_id=s.id AND p.pricelist_id IS NULL")


def prepare_distributions(cr):
    if table_exists(cr, "trade_distribution"):
        assert_empty(cr, "SELECT sale_order_id,array_agg(id) FROM trade_distribution GROUP BY sale_order_id HAVING count(*)>1",
                     "Review multiple historical distributions for one sale before enforcing one distribution per sale")


def snapshot_legacy_reconciliations(cr):
    # These values are explicitly snapshots AT MIGRATION, not fabricated records
    # of what someone originally approved. The header keeps its review flag.
    cr.execute("""
        UPDATE trade_reconciliation_line l SET snapshot_amount=s.price_subtotal,
            snapshot_quantity=s.product_uom_qty,snapshot_unit_price=s.price_unit,
            snapshot_sale_reference=o.name,snapshot_product_name=p.default_code,
            snapshot_uom_name=u.name->>'en_US'
        FROM sale_order_line s JOIN sale_order o ON o.id=s.order_id
        JOIN product_product p ON p.id=s.product_id JOIN uom_uom u ON u.id=s.product_uom
        WHERE l.sale_line_id=s.id AND l.reconciliation_id IN
            (SELECT id FROM trade_reconciliation WHERE legacy_review_required=true AND state='confirmed')
    """)
    cr.execute("""
        UPDATE trade_reconciliation_line l SET amount=l.snapshot_amount
        FROM trade_reconciliation h WHERE h.id=l.reconciliation_id
        AND h.state='confirmed' AND h.legacy_review_required=true
    """)
