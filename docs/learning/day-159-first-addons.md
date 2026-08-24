# Day 159 — First addon skeletons

## What changed

TradeOps 360 now contains the installable `trade_core` and `trade_import`
addons. Each has a manifest and Python package initialization.

## Why

The project needs a shared foundation and a separate boundary for import
operations before it starts adding business models.

## Odoo concepts learned

- `__manifest__.py` identifies an addon and declares its metadata and
  dependencies.
- Root `__init__.py` loads the addon Python packages.
- `depends` defines the installation order and available Odoo capabilities.
- `-i` installs a module; `-u` upgrades it after a change.

## Resulting behavior

Odoo can discover two dependency-linked TradeOps addons once
`custom_addons/` is included in `addons_path`. Installing `trade_import`
resolves `trade_core` first. No TradeOps business records, views, security, or
data are introduced in this milestone.
