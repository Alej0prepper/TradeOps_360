#!/usr/bin/env python3
"""Configure Odoo without changing CLI subcommands or exposing credentials."""
import configparser
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence


def write_runtime_config(
    environ: Mapping[str, str],
    template: str = "/etc/tradeops/odoo.conf.example",
    directory: str = "/tmp",
) -> str:
    password = environ.get("PASSWORD", "")
    master = environ.get("ODOO_MASTER_PASSWORD", "")
    if not password or not master:
        raise SystemExit("Set separate database and Odoo master passwords before starting.")
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(template) or not config.has_section("options"):
        raise SystemExit("Missing mounted Odoo configuration template or [options] section.")
    config["options"].update({
        "db_host": environ.get("HOST", "db"),
        "db_user": environ.get("USER", "odoo"),
        "db_password": password,
        "admin_passwd": master,
    })
    # mkstemp creates a new private file, rather than truncating a predictable path.
    fd, path = tempfile.mkstemp(prefix="tradeops-runtime-", suffix=".conf", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            config.write(stream)
    except BaseException:
        os.unlink(path)
        raise
    return path


def main(argv: Sequence[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    path = write_runtime_config(os.environ)
    # Odoo dispatches on its first argument. Prepending -c turns `shell` into
    # an invalid server argument. ODOO_RC keeps shell/server/help unchanged.
    os.environ["ODOO_RC"] = path
    try:
        os.execvp("odoo", ["odoo", *args])
    except OSError:
        os.unlink(path)
        raise


if __name__ == "__main__":
    main()
