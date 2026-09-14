from odoo import fields, models

from ..models.trade_delivery_incident import INCIDENT_TYPES


class ReportDeliveryIncidentWizard(models.TransientModel):
    _name = "trade.report.delivery.incident.wizard"
    _description = "Report Delivery Incident"
    _check_company_auto = True

    distribution_id = fields.Many2one("trade.distribution", required=True, check_company=True)
    company_id = fields.Many2one(related="distribution_id.company_id", store=True, readonly=True)
    incident_type = fields.Selection(INCIDENT_TYPES, required=True)
    description = fields.Text(required=True)
    incident_date = fields.Datetime(default=fields.Datetime.now, required=True)
    responsible_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)

    def action_confirm(self):
        self.ensure_one()
        self.check_access_rights("read")
        self.check_access_rule("read")
        self.distribution_id._report_incident(
            self.incident_type, self.description, self.incident_date, self.responsible_id.id,
        )
        return {"type": "ir.actions.act_window_close"}
