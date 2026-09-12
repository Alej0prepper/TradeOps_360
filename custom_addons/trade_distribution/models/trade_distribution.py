from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TradeDistribution(models.Model):
    _name = "trade.distribution"
    _description = "Trade Distribution"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(required=True, default="New")
    sale_order_id = fields.Many2one("sale.order", required=True, ondelete="restrict")
    picking_id = fields.Many2one("stock.picking", string="Delivery", ondelete="restrict")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    expected_quantity = fields.Float(required=True)
    delivered_quantity = fields.Float(compute="_compute_delivery_quantities", string="Delivered", store=True)
    pending_quantity = fields.Float(compute="_compute_delivery_quantities", string="Pending", store=True)
    incident_ids = fields.One2many("trade.delivery.incident", "distribution_id", string="Incidents")

    @api.depends("expected_quantity", "picking_id", "picking_id.move_line_ids")
    def _compute_delivery_quantities(self):
        for distribution in self:
            delivered = 0.0
            if distribution.picking_id:
                for line in distribution.picking_id.move_line_ids:
                    # Odoo 17 uses ``quantity``; ``qty_done`` is retained for
                    # compatibility with older Inventory data models.
                    delivered += line.quantity if hasattr(line, "quantity") else getattr(line, "qty_done", 0.0)
            distribution.delivered_quantity = delivered
            distribution.pending_quantity = max(distribution.expected_quantity - delivered, 0.0)

    @api.constrains("expected_quantity")
    def _check_expected_quantity(self):
        for distribution in self:
            if distribution.expected_quantity <= 0:
                raise ValidationError("Expected quantity must be greater than zero.")

    def report_incident(self, incident_type, description, incident_date=False):
        self.ensure_one()
        if not incident_type:
            raise ValidationError("Incident type is required.")
        if not description or not description.strip():
            raise ValidationError("Incident description is required.")
        incident = self.env["trade.delivery.incident"].create({
            "distribution_id": self.id, "incident_type": incident_type,
            "description": description, "incident_date": incident_date or fields.Datetime.now(),
        })
        self.message_post(
            body="Delivery incident reported: %s."
            % dict(incident._fields["incident_type"].selection).get(
                incident.incident_type
            )
        )
        return incident

    def action_report_incident(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "trade.report.delivery.incident.wizard",
                "view_mode": "form", "target": "new", "context": {"default_distribution_id": self.id}}
