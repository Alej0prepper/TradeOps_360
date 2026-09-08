from odoo import fields, models


class ReportDeliveryIncidentWizard(models.TransientModel):
    _name = "trade.report.delivery.incident.wizard"
    _description = "Report Delivery Incident"

    distribution_id = fields.Many2one("trade.distribution", required=True)
    incident_type = fields.Selection([
        ("vehicle_failure", "Vehicle Failure"), ("customer_rejection", "Customer Rejection"),
        ("damaged_goods", "Damaged Goods"), ("documentation", "Documentation Problem"), ("other", "Other")
    ], required=True)
    description = fields.Text(required=True)
    incident_date = fields.Datetime(default=fields.Datetime.now, required=True)

    def action_confirm(self):
        self.ensure_one()
        self.distribution_id.report_incident(self.incident_type, self.description, self.incident_date)
        return {"type": "ir.actions.act_window_close"}
