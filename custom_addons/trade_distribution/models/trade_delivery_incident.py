from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TradeDeliveryIncident(models.Model):
    _name = "trade.delivery.incident"
    _description = "Delivery Incident"
    _order = "incident_date desc, id desc"

    distribution_id = fields.Many2one("trade.distribution", required=True, ondelete="cascade")
    incident_type = fields.Selection([
        ("vehicle_failure", "Vehicle Failure"), ("customer_rejection", "Customer Rejection"),
        ("damaged_goods", "Damaged Goods"), ("documentation", "Documentation Problem"), ("other", "Other")
    ], required=True)
    description = fields.Text(required=True)
    incident_date = fields.Datetime(default=fields.Datetime.now, required=True)

    @api.constrains("description")
    def _check_description(self):
        for incident in self:
            if not incident.description or not incident.description.strip():
                raise ValidationError("Incident description is required.")
