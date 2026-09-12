from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import SQL


class TradeDocumentMixin(models.AbstractModel):
    _name = "trade.document.mixin"
    _description = "TradeOps document invariants"
    _check_company_auto = True
    _trade_editable_states = ("draft",)
    _trade_managed_fields = ()

    name = fields.Char(required=True, default="New", copy=False, readonly=True, index=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
        readonly=True, index=True,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, readonly=True,
    )

    _sql_constraints = [
        ("reference_company_unique", "unique(company_id, name)",
         "The reference must be unique within its company."),
    ]

    def _trade_require_role(self, role="operator"):
        if not self.env.su and not self.env.user.has_group("trade_core.group_trade_" + role):
            raise AccessError(_("You do not have the required TradeOps role."))

    def _trade_lock(self):
        self.check_access_rights("write")
        self.check_access_rule("write")
        if self:
            self.flush_recordset()
            # Lock an existing aggregate, after checking access. This SQL never
            # changes business data or replaces ORM validation and tracking.
            self.env.cr.execute(SQL(
                "SELECT id FROM %s WHERE id IN %s ORDER BY id FOR UPDATE",
                SQL.identifier(self._table), tuple(self.ids),
            ))
            self.invalidate_recordset()

    def _trade_check_state(self, *states):
        if any(record.state not in states for record in self):
            raise UserError(_("This operation is not allowed in the current state."))

    def _trade_internal_write(self, values):
        # Private server-side method: no client-controlled context bypass.
        # Business actions check their role and transition before calling it.
        return super(TradeDocumentMixin, self).write(values)

    @api.model_create_multi
    def create(self, vals_list):
        self._trade_require_role()
        prepared = []
        for original in vals_list:
            vals = dict(original)
            if vals.get("state", "draft") != "draft":
                raise ValidationError(_("New documents must start in draft."))
            if any(vals.get(key) for key in self._trade_managed_fields):
                raise ValidationError(_("Generated document links cannot be supplied manually."))
            company = self.env["res.company"].browse(vals.get("company_id") or self.env.company.id)
            if not self.env.su and company not in self.env.companies:
                raise AccessError(_("Select an allowed company before creating this document."))
            if vals.get("currency_id") and vals["currency_id"] != company.currency_id.id:
                raise ValidationError(_("Phase 1 uses the company currency."))
            vals.pop("currency_id", None)
            vals.update(company_id=company.id, state="draft")
            vals["name"] = self.env["ir.sequence"].with_company(company).next_by_code(self._name)
            if not vals["name"]:
                raise UserError(_("The TradeOps reference sequence is not configured."))
            prepared.append(vals)
        return super().create(prepared)

    def write(self, vals):
        self._trade_require_role()
        self._trade_lock()
        protected = {"state", "name", "company_id", "currency_id", *self._trade_managed_fields}
        if protected.intersection(vals):
            raise UserError(_("Use business actions to change state or generated references."))
        business_fields = [key for key in vals if not key.startswith(("message_", "activity_"))]
        if business_fields:
            self._trade_check_state(*self._trade_editable_states)
        return super().write(vals)

    def unlink(self):
        self._trade_require_role()
        self._trade_lock()
        self._trade_check_state("draft")
        return super().unlink()

    def _trade_check_invariants(self):
        """Called after a direct child mutation, including edits outside forms."""
        return True

    def _trade_open(self):
        self.ensure_one()
        self.check_access_rights("read")
        self.check_access_rule("read")
        return {"type": "ir.actions.act_window", "res_model": self._name,
                "res_id": self.id, "view_mode": "form", "target": "current"}


class TradeChildMixin(models.AbstractModel):
    _name = "trade.child.mixin"
    _description = "TradeOps child invariants"
    _check_company_auto = True
    _trade_parent_field = None
    _trade_parent_states = None
    _trade_managed_fields = ()

    def _trade_guard_parents(self, parents):
        parents._trade_require_role()
        parents._trade_lock()
        parents._trade_check_state(*(self._trade_parent_states or parents._trade_editable_states))

    @api.model_create_multi
    def create(self, vals_list):
        field = self._trade_parent_field
        parents = self.env[self._fields[field].comodel_name].browse(
            [vals[field] for vals in vals_list if vals.get(field)]
        )
        self._trade_guard_parents(parents)
        if any(any(vals.get(key) for key in self._trade_managed_fields) for vals in vals_list):
            raise ValidationError(_("Generated child fields cannot be supplied manually."))
        records = super().create(vals_list)
        records.mapped(field)._trade_check_invariants()
        return records

    def write(self, vals):
        field = self._trade_parent_field
        parents = self.mapped(field)
        if vals.get(field):
            parents |= self.env[self._fields[field].comodel_name].browse(vals[field])
        self._trade_guard_parents(parents)
        if {"company_id", "currency_id", *self._trade_managed_fields}.intersection(vals):
            raise UserError(_("Derived child fields cannot be changed manually."))
        result = super().write(vals)
        parents._trade_check_invariants()
        return result

    def unlink(self):
        parents = self.mapped(self._trade_parent_field)
        self._trade_guard_parents(parents)
        result = super().unlink()
        parents._trade_check_invariants()
        return result

    def _trade_internal_write(self, vals):
        return super(TradeChildMixin, self).write(vals)
