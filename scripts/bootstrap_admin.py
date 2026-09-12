"""Explicit local bootstrap/reset, invoked only by dev.sh init on a dedicated DB."""
import os

if not env.cr.dbname.startswith("tradeops_"):
    raise RuntimeError("Use a dedicated TradeOps development database.")
password = os.environ.get("TRADEOPS_ADMIN_PASSWORD", "")
if len(password) < 12:
    raise RuntimeError("Set TRADEOPS_ADMIN_PASSWORD to a unique value of at least 12 characters.")
admin = env.ref("base.user_admin")
admin.write({"login": "admin", "password": password,
             "email": os.environ.get("TRADEOPS_ADMIN_EMAIL", "admin@example.test")})
env.cr.commit()
print("Local administrator configured. No credentials were printed.")
