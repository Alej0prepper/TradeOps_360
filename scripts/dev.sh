#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
command="${1:-help}"
database="${2:-tradeops_dev}"
modules=trade_core,trade_import,trade_presale,trade_distribution,trade_reconciliation
if [[ ! "$database" =~ ^tradeops_[A-Za-z0-9_]+$ ]]; then
    echo 'Use a dedicated tradeops_* development database.' >&2; exit 2
fi
case "$command" in
  init)
    docker compose up -d db
    docker compose run --rm odoo -d "$database" -i "$modules" --without-demo=all --stop-after-init --no-http
    docker compose run --rm -T odoo shell -d "$database" --no-http < scripts/bootstrap_admin.py
    ;;
  test)
    database="${2:-tradeops_test}"
    docker compose up -d db
    docker compose run --rm odoo -d "$database" -i "$modules" --without-demo=all --test-enable \
      --test-tags /trade_core,/trade_import,/trade_presale,/trade_distribution,/trade_reconciliation \
      --stop-after-init --no-http --log-level=test
    ;;
  upgrade)
    docker compose stop odoo
    docker compose run --rm odoo -d "$database" -u "$modules" --without-demo=all --stop-after-init --no-http
    echo 'Inspect upgrade logs and run smoke tests before starting the web service.'
    ;;
  up) docker compose up -d ;;
  stop) docker compose stop ;;
  logs) docker compose logs --tail=200 -f odoo ;;
  demo)
    database="${2:-tradeops_demo}"
    [[ "$database" == *_demo ]] || { echo 'Demo seeding requires a *_demo database.' >&2; exit 2; }
    : "${TRADEOPS_DEMO_PASSWORD:?Set a temporary demo-user password in your shell}"
    docker compose run --rm -T -e TRADEOPS_ALLOW_DEMO=1 -e TRADEOPS_DEMO_PASSWORD -e TRADEOPS_CHECK=seed \
      odoo shell -d "$database" --no-http < scripts/acceptance.py
    ;;
  backup)
    destination="${3:-backups/$(date -u +%Y%m%dT%H%M%SZ)-$database}"
    [[ ! -e "$destination" ]] || { echo 'Backup destination already exists.' >&2; exit 2; }
    mkdir -p "$destination"; chmod 700 "$destination"
    docker compose stop odoo
    docker compose exec -T db pg_dump -U odoo -d "$database" -Fc > "$destination/database.dump"
    docker compose run --rm -T --no-deps --entrypoint tar odoo \
      -C /var/lib/odoo -czf - "filestore/$database" > "$destination/filestore.tar.gz"
    printf '%s\n' "$database" > "$destination/database-name.txt"
    git rev-parse HEAD > "$destination/code-revision.txt"
    cp compose.yaml "$destination/compose.yaml"
    (cd "$destination" && sha256sum database.dump filestore.tar.gz > SHA256SUMS)
    echo "Backup created at $destination. The web service remains stopped."
    ;;
  restore)
    source_dir="${3:?Pass the backup directory as the third argument}"
    old_database="$(cat "$source_dir/database-name.txt")"
    [[ "$old_database" =~ ^tradeops_[A-Za-z0-9_]+$ ]] || { echo 'Invalid backup database name.' >&2; exit 2; }
    [[ "$database" != "$old_database" ]] || { echo 'Restore only to a NEW database name.' >&2; exit 2; }
    (cd "$source_dir" && sha256sum --check SHA256SUMS)
    python3 - "$source_dir/filestore.tar.gz" "$old_database" <<'PY'
import sys, tarfile
from pathlib import PurePosixPath
with tarfile.open(sys.argv[1]) as archive:
    prefix = ('filestore', sys.argv[2])
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts or tuple(path.parts[:2]) != prefix or member.issym() or member.islnk():
            raise SystemExit('Unsafe or unexpected filestore archive member.')
PY
    docker compose up -d db
    docker compose exec -T db createdb -U odoo "$database"
    docker compose exec -T db pg_restore -U odoo -d "$database" --no-owner --exit-on-error < "$source_dir/database.dump"
    docker compose run --rm -T --no-deps --entrypoint tar odoo --no-same-owner \
      -C /var/lib/odoo --transform="s#filestore/$old_database#filestore/$database#" \
      -xzf - < "$source_dir/filestore.tar.gz"
    echo "Restored $database. Match code-revision.txt and verify before exposing the database."
    ;;
  *) printf '%s\n' 'Usage: bash scripts/dev.sh {init|test|upgrade|up|stop|logs|demo|backup|restore} [tradeops_database] [backup_directory]' ;;
esac
