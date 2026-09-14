#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
: "${ODOO_IMAGE:?Set the pinned Odoo image}"
: "${TRADEOPS_DEMO_PASSWORD:?Seed the acceptance users with a disposable password}"
container="tradeops-ui-${GITHUB_RUN_ID:-local}"
cleanup() {
    docker logs "$container" > .ci/ui-server.log 2>&1 || true
    docker rm -f "$container" >/dev/null 2>&1 || true
}
trap cleanup EXIT
docker run -d --name "$container" --network host --user "$(id -u):$(id -g)" \
    --entrypoint /usr/bin/odoo -e USER=odoo -e LOGNAME=odoo \
    -v "$PWD:/mnt/tradeops:ro" -v "$PWD/.ci/data:/var/lib/odoo" \
    "$ODOO_IMAGE" --db_host=127.0.0.1 --db_user=odoo --db_password=ci-only-password \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/tradeops/custom_addons \
    -d tradeops_ci '--db-filter=^tradeops_ci$' --no-database-list \
    --http-interface=127.0.0.1 --http-port=8069 --workers=0 --max-cron-threads=0
for attempt in $(seq 1 60); do
    if curl --fail --silent http://127.0.0.1:8069/web/login >/dev/null; then break; fi
    sleep 1
done
curl --fail --silent http://127.0.0.1:8069/web/login >/dev/null
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.ci/browsers"
npm --prefix .ci/ui install --save-exact --ignore-scripts playwright@1.55.1
.ci/ui/node_modules/.bin/playwright install chromium
NODE_PATH="$PWD/.ci/ui/node_modules" node scripts/ui-smoke.cjs 2>&1 | tee .ci/ui-smoke.log
