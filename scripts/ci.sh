#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
: "${ODOO_IMAGE:?Set the pinned Odoo image}"
: "${POSTGRES_IMAGE:?Set the pinned PostgreSQL image}"
export PGPASSWORD="${PGPASSWORD:-ci-only-password}"
HOST="${PGHOST:-127.0.0.1}"
USER_NAME="${PGUSER:-odoo}"
MODULES=trade_core,trade_import,trade_presale,trade_distribution,trade_reconciliation
TAGS=/trade_core,/trade_import,/trade_presale,/trade_distribution,/trade_reconciliation
BASELINE=b72cf69f3cea360a9593869dda707bcbfd52df29
mkdir -p .ci/data/evidence .ci/backup/filestore .ci/legacy-source

odoo_run() {
    docker run --rm -i --network host --user "$(id -u):$(id -g)" \
        --entrypoint /usr/bin/odoo -e USER=odoo -e LOGNAME=odoo \
        -e TRADEOPS_CHECK="${TRADEOPS_CHECK:-seed}" \
        -e TRADEOPS_DEMO_PASSWORD \
        -v "$PWD:/mnt/tradeops:ro" -v "$PWD/.ci/data:/var/lib/odoo" \
        "$ODOO_IMAGE" "$@"
}
pg_run() {
    local command="$1"; shift
    docker run --rm --network host --user "$(id -u):$(id -g)" \
        --entrypoint "$command" -e PGPASSWORD \
        -v "$PWD/.ci/backup:/backup" "$POSTGRES_IMAGE" \
        -h "$HOST" -U "$USER_NAME" "$@"
}
CONNECTION=(--db_host="$HOST" --db_user="$USER_NAME" --db_password="$PGPASSWORD")
COMMON=("${CONNECTION[@]}" --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/tradeops/custom_addons)

python3 scripts/static_check.py | tee .ci/static.log
docker pull "$ODOO_IMAGE"
docker image inspect "$ODOO_IMAGE" --format '{{json .RepoDigests}}' > .ci/runtime.txt
git rev-parse HEAD >> .ci/runtime.txt
odoo_run "${COMMON[@]}" -d tradeops_ci -i "$MODULES" --without-demo=all \
    --test-enable --test-tags "$TAGS" --stop-after-init --log-level=test 2>&1 | tee .ci/install.log
TRADEOPS_CHECK=seed odoo_run shell "${COMMON[@]}" -d tradeops_ci --no-http \
    < scripts/acceptance.py 2>&1 | tee .ci/acceptance.log
odoo_run shell "${COMMON[@]}" -d tradeops_ci --no-http \
    < scripts/concurrency.py 2>&1 | tee .ci/concurrency.log
TRADEOPS_CHECK=verify odoo_run shell "${COMMON[@]}" -d tradeops_ci --no-http \
    < scripts/acceptance.py 2>&1 | tee .ci/before-upgrade.log

# Consistent synthetic backup: no application process is writing in parallel.
pg_run pg_dump -d tradeops_ci --format=custom --no-owner --file=/backup/database.dump
cp -a .ci/data/filestore/tradeops_ci .ci/backup/filestore/
git rev-parse HEAD > .ci/backup/code-revision.txt
odoo_run "${COMMON[@]}" -d tradeops_ci -u "$MODULES" --without-demo=all \
    --stop-after-init 2>&1 | tee .ci/upgrade.log
TRADEOPS_CHECK=verify odoo_run shell "${COMMON[@]}" -d tradeops_ci --no-http \
    < scripts/acceptance.py 2>&1 | tee .ci/after-upgrade.log
pg_run createdb tradeops_ci_restore
pg_run pg_restore -d tradeops_ci_restore --no-owner --exit-on-error /backup/database.dump
cp -a .ci/backup/filestore/tradeops_ci .ci/data/filestore/tradeops_ci_restore
TRADEOPS_CHECK=verify odoo_run shell "${COMMON[@]}" -d tradeops_ci_restore --no-http \
    < scripts/acceptance.py 2>&1 | tee .ci/restore.log

# Upgrade the actual previous repository revision, not just the current schema.
git fetch --no-tags --depth=1 origin "$BASELINE"
git archive "$BASELINE" | tar -x -C .ci/legacy-source
odoo_run "${CONNECTION[@]}" \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/tradeops/.ci/legacy-source/custom_addons \
    -d tradeops_ci_legacy -i "$MODULES" --without-demo=all --stop-after-init \
    2>&1 | tee .ci/legacy-install.log
TRADEOPS_CHECK=legacy_seed odoo_run shell "${CONNECTION[@]}" \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/tradeops/.ci/legacy-source/custom_addons \
    -d tradeops_ci_legacy --no-http < scripts/migration_fixture.py 2>&1 | tee .ci/legacy-seed.log
odoo_run "${COMMON[@]}" -d tradeops_ci_legacy -u "$MODULES" --without-demo=all \
    --stop-after-init 2>&1 | tee .ci/legacy-upgrade.log
TRADEOPS_CHECK=legacy_verify odoo_run shell "${COMMON[@]}" -d tradeops_ci_legacy --no-http \
    < scripts/migration_fixture.py 2>&1 | tee .ci/legacy-verify.log
python3 scripts/validate_evidence.py .ci | tee .ci/result.log
