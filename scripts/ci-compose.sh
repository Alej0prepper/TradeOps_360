#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
export POSTGRES_PASSWORD="$(openssl rand -hex 24)"
export ODOO_MASTER_PASSWORD="$(openssl rand -hex 24)"
export TRADEOPS_ADMIN_PASSWORD="$(openssl rand -hex 24)"
export TRADEOPS_ADMIN_EMAIL=admin@example.test
export ODOO_DB=tradeops_demo
: "${TRADEOPS_DEMO_PASSWORD:?Set a disposable demonstration password}"
trap 'docker compose stop >/dev/null 2>&1 || true' EXIT
docker compose config --quiet
bash scripts/dev.sh init tradeops_demo 2>&1 | tee .ci/compose-install.log
bash scripts/dev.sh demo tradeops_demo 2>&1 | tee .ci/compose-demo.log
bash scripts/dev.sh backup tradeops_demo .ci/compose-backup 2>&1 | tee .ci/compose-backup.log
bash scripts/dev.sh restore tradeops_ci_compose_restore .ci/compose-backup 2>&1 | tee .ci/compose-restore.log
docker compose run --rm -T -e TRADEOPS_CHECK=verify odoo shell \
    -d tradeops_ci_compose_restore --no-http < scripts/acceptance.py 2>&1 | tee .ci/compose-verify.log
docker compose run --rm -T --no-deps --entrypoint cat odoo \
    /var/lib/odoo/evidence/verified-tradeops_ci_compose_restore.json \
    > .ci/data/evidence/compose-restore.json
