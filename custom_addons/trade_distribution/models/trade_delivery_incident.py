from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


INCIDENT_TYPES = [
    ("vehicle_failure", "Vehicle Failure"), ("customer_rejection", "Customer Rejection"),
    ("damaged_goods", "Damaged Goods"), ("documentation", "Documentation Problem"), ("other", "Other"),
]


class TradeDeliveryIncident(models.Model):
    _name = "trade.delivery.incident"
    _description = "Delivery Incident"
    _inherit = "trade.child.mixin"
    _order = "incident_date desc, id desc"
    _rec_name = "description"
    _trade_parent_field = "distribution_id"
    _trade_parent_states = ("active",)
    _trade_managed_fields = ("resolved_at", "resolved_by_id")

    distribution_id = fields.Many2one("trade.distribution", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="distribution_id.company_id", store=True, readonly=True, index=True)
    incident_type = fields.Selection(INCIDENT_TYPES, required=True)
    description = fields.Text(required=True)
    incident_date = fields.Datetime(default=fields.Datetime.now, required=True)
    responsible_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user, ondelete="restrict")
    state = fields.Selection([("open", "Open"), ("resolved", "Resolved")], required=True, default="open", readonly=True, copy=False)
    resolution = fields.Text()
    resolved_at = fields.Datetime(readonly=True, copy=False)
    resolved_by_id = fields.Many2one("res.users", readonly=True, copy=False, ondelete="restrict")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("state", "open") != "open" or vals.get("resolution"):
                raise ValidationError(_("New incidents must start open, without a resolution."))
        return super().create([dict(vals, state="open") for vals in vals_list])

    @api.constrains("description", "responsible_id", "distribution_id")
    def _check_description_and_responsible(self):
        for incident in self:
            if not incident.description or not incident.description.strip():
                raise ValidationError(_("Incident description is required."))
            if (not incident.responsible_id.active or incident.responsible_id.share
                    or incident.company_id not in incident.responsible_id.company_ids):
                raise ValidationError(_("The responsible user must be active and allowed in this company."))

    def write(self, vals):
        if any(incident.state != "open" for incident in self):
            raise UserError(_("Resolved incidents are retained as immutable evidence."))
        if "state" in vals or "distribution_id" in vals:
            raise UserError(_("Use the resolution action; incident provenance cannot be changed."))
        if "resolution" in vals:
            self.mapped("distribution_id")._trade_require_role("manager")
        return super().write(vals)

    def action_resolve(self):
        parents = self.mapped("distribution_id")
        parents._trade_require_role("manager")
        parents._trade_lock()
        parents._trade_check_state("active")
        for incident in self:
            incident.check_access_rights("write")
            incident.check_access_rule("write")
            if incident.state != "open" or not incident.resolution or not incident.resolution.strip():
                raise UserError(_("An open incident requires a written resolution."))
        self._trade_internal_write({"state": "resolved", "resolved_at": fields.Datetime.now(), "resolved_by_id": self.env.user.id})
        for incident in self:
            incident.distribution_id.message_post(body=_("Incident resolved: %s. Resolution: %s", incident.description, incident.resolution))
        return True

    def unlink(self):
        raise UserError(_("Retain incidents and record a resolution instead of deleting evidence."))
