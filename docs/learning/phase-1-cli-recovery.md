# Phase 1 recovery: the CLI wrapper is part of the product

## Observed failure

Run 34721618730 on fa71777 installed the modules and ran 45 Odoo tests without failures. Its browser smoke check passed. The documented Compose setup then failed with `odoo server: error: unrecognized parameters: 'shell'`. This is not the earlier missing-script failure and not 58 executed business tests.

## Cause and change

`scripts/odoo-entrypoint.py` always constructed `odoo -c <runtime-config> ...`. With `shell` supplied by `scripts/dev.sh`, the first option selected the default server command before Odoo could dispatch the shell command. The wrapper now supplies the private configuration through `ODOO_RC` and preserves every CLI argument. Temporary configuration files are created uniquely with mode 0600 and are removed if process execution fails. Credentials stay out of command arguments.

## Verification

`python3 -m unittest discover -s scripts/tests -v` executes 9 independent wrapper tests, including shell dispatch, implicit and explicit server commands, configuration content, file permissions, missing configuration and failed execution. These are not Odoo model tests. GitHub Actions runs them before installation and retains their log.

The real integration check remains `bash scripts/ci-compose.sh`: initialize Odoo, provision a local administrator, create the fictional acceptance scenario, back up the database and filestore, restore to a new database and verify business records and an attachment digest. A passing wrapper test alone is not evidence of successful recovery.

Reference: Odoo 17 CLI documentation, configuration (`ODOO_RC`) and `shell`: https://www.odoo.com/documentation/17.0/developer/reference/cli.html
