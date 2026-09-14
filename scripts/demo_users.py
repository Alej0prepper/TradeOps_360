"""Synthetic identities for the executable acceptance rehearsal."""
import os
from odoo import fields


def create_user(env, login, group, company):
    values = {
        "name": login.replace("_", " ").title(), "login": login,
        "email": login + "@example.test",
        "company_id": company.id,
        "company_ids": [fields.Command.set(company.ids)],
        "groups_id": [fields.Command.set(env.ref(group).ids)],
    }
    if os.environ.get("TRADEOPS_DEMO_PASSWORD"):
        values["password"] = os.environ["TRADEOPS_DEMO_PASSWORD"]
    return env["res.users"].with_context(no_reset_password=True).create(values)
