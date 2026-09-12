# TradeOps release readiness

This checklist complements the automated model tests. It does not replace a
staging environment, database backup, or smoke test.

## Automated module tests

Run the suite against an empty non-production database. Replace
`/path/to/odoo/addons` with the standard addons directory of the Odoo 17
installation.

```bash
./odoo-bin -d tradeops_test \
  --addons-path=/path/to/odoo/addons,custom_addons \
  -i trade_import,trade_presale,trade_distribution,trade_reconciliation \
  --test-enable --stop-after-init
```

The suite protects import cost allocation and constraints, presale conversion
and product eligibility, incident recording, and reconciliation integrity.

## Staging upgrade

1. Restore a representative database and its filestore into staging.
2. Take a new database and filestore backup immediately before the upgrade.
3. Upgrade the addons and inspect the server log for tracebacks or view and
   access-right errors.

```bash
./odoo-bin -c /path/to/odoo.conf -d tradeops_staging \
  -u trade_core,trade_import,trade_presale,trade_distribution,trade_reconciliation \
  --stop-after-init
```

## Smoke test

- Open the TradeOps menus and each updated form.
- Create an import with products and an expense; confirm the landed costs.
- Convert one confirmed presale from a completed import to a quotation.
- Report a distribution incident and verify its Chatter message.
- Confirm a reconciliation and verify that its sale lines cannot be reused.
- Check the server log and the affected records' Chatter history.

## Production deployment

Deploy the tested commit only after the staging upgrade and smoke test pass.
Keep the pre-upgrade code revision, database backup, and filestore backup
together. If the release must be reversed, restore data consistently with the
code revision; reverting Git alone does not undo an Odoo module upgrade.
