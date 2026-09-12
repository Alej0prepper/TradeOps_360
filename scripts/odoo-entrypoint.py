#!/usr/bin/env python3
"""Build a mode-0600 runtime config without logging credentials."""
import configparser
import os
import sys

password = os.environ.get("PASSWORD", "")
master = os.environ.get("ODOO_MASTER_PASSWORD", "")
if not password or not master:
    raise SystemExit("Set separate database and Odoo master passwords before starting.")
config = configparser.ConfigParser(interpolation=None)
if not config.read("/etc/tradeops/odoo.conf.example"):
    raise SystemExit("Missing mounted Odoo configuration template.")
config["options"].update({
    "db_host": os.environ.get("HOST", "db"),
    "db_user": os.environ.get("USER", "odoo"),
    "db_password": password,
    "admin_passwd": master,
})
path = "/tmp/tradeops-runtime.conf"
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as stream:
    config.write(stream)
os.execvp("odoo", ["odoo", "-c", path, *sys.argv[1:]])
