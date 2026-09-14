from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class TradeDistribution(models.Model):
    _name = "trade.distribution"
    _description = "Trade Distribution"
    _inherit = ["trade.document.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _trade_managed_fields = (
        "line_ids", "expected_quantity", "delivered_quantity", "pending_quantity",
        "legacy_review_required", "has_uniform_uom", "summary_uom_id",
    )

    sale_order_id = fields.Many2one("sale.order", required=True, check_company=True, ondelete="restrict", index=True)
    picking_id = fields.Many2one("stock.picking", check_company=True, ondelete="restrict", string="Reference Delivery")
    picking_ids = fields.One2many(related="sale_order_id.picking_ids", readonly=True)
    line_ids = fields.One2many("trade.distribution.line", "distribution_id", readonly=True, copy=False)
    incident_ids = fields.One2many("trade.delivery.incident", "distribution_id", readonly=True, copy=False)
    state = fields.Selection([
        ("draft", "Draft"), ("active", "Active"), ("closed", "Closed"), ("cancelled", "Cancelled"),
    ], default="draft", required=True, readonly=True, copy=False, tracking=True, index=True)
    expected_quantity = fields.Float(compute="_compute_totals")
    delivered_quantity = fields.Float(compute="_compute_totals")
    pending_quantity = fields.Float(compute="_compute_totals")
    has_uniform_uom = fields.Boolean(compute="_compute_totals")
    summary_uom_id = fields.Many2one("uom.uom", compute="_compute_totals")
    legacy_review_required = fields.Boolean(readonly=True, copy=False)

    _sql_constraints = [
        ("sale_order_unique", "unique(sale_order_id)", "A sale can have only one distribution."),
    ]

    @api.depends("line_ids.expected_quantity", "line_ids.delivered_quantity", "line_ids.pending_quantity", "line_ids.uom_id")
    def _compute_totals(self):
        for record in self:
            units = record.line_ids.uom_id
            uniform = len(units) == 1
            record.has_uniform_uom = uniform
            record.summary_uom_id = units if uniform else False
            record.expected_quantity = sum(record.line_ids.mapped("expected_quantity")) if uniform else 0
            record.delivered_quantity = sum(record.line_ids.mapped("delivered_quantity")) if uniform else 0
            record.pending_quantity = sum(record.line_ids.mapped("pending_quantity")) if uniform else 0

    @api.constrains("sale_order_id", "picking_id", "company_id")
    def _check_sale(self):
        for record in self:
            if record.sale_order_id.company_id != record.company_id:
                raise ValidationError(_("The distribution and sale must belong to the same company."))
            if record.picking_id and record.picking_id not in record.sale_order_id.picking_ids:
                raise ValidationError(_("The reference delivery must belong to the selected sale."))
            record.line_ids._check_sale_line()

    def action_start(self):
        self.ensure_one()
        self._trade_require_role()
        self._trade_lock()
        self._trade_check_state("draft")
        if self.legacy_review_required:
            raise UserError(_("Review this historical distribution before starting it."))
        if self.sale_order_id.state != "sale" or not self.sale_order_id.trade_presale_id:
            raise UserError(_("Select a confirmed sale generated from a TradeOps presale."))
        sale_lines = self.sale_order_id.order_line.filtered(lambda line: not line.display_type)
        if not sale_lines:
            raise UserError(_("There are no sale products to distribute."))
        existing = self.line_ids.sale_line_id
        self.env["trade.distribution.line"].create([
            {"distribution_id": self.id, "sale_line_id": line.id}
            for line in sale_lines - existing
        ])
        self._trade_internal_write({"state": "active"})
        return True

    def action_close(self):
        self._trade_require_role("manager")
        self._trade_lock()
        self._trade_check_state("active")
        for record in self:
            if not record.line_ids or record.sale_order_id.state != "sale":
                raise UserError(_("A confirmed sale with distribution lines is required."))
            if any(float_compare(line.pending_quantity, 0, precision_rounding=line.uom_id.rounding) > 0 for line in record.line_ids):
                raise UserError(_("Complete the pending deliveries before closing."))
            if record.incident_ids.filtered(lambda incident: incident.state == "open"):
                raise UserError(_("Resolve all open incidents before closing."))
        self._trade_internal_write({"state": "closed"})
        return True

    def action_cancel(self):
        self._trade_require_role("manager")
        self._trade_lock()
        self._trade_check_state("draft", "active")
        if self.mapped("picking_ids.move_ids").filtered(lambda move: move.state == "done"):
            raise UserError(_("Completed physical deliveries require returns, not cancellation."))
        if self.mapped("incident_ids").filtered(lambda incident: incident.state == "open"):
            raise UserError(_("Resolve open incidents before cancellation."))
        self._trade_internal_write({"state": "cancelled"})
        return True

    def _sync_delivery_state(self):
        for record in self:
            record._trade_lock()
            if record.state == "closed" and any(line.pending_quantity > 0 for line in record.line_ids):
                record._trade_internal_write({"state": "active"})
                record.message_post(body=_("Distribution reopened because a return or sale change created pending quantities."))

    def _report_incident(self, incident_type, description, incident_date=False, responsible_id=False):
        self.ensure_one()
        self._trade_require_role()
        self._trade_lock()
        self._trade_check_state("active")
        incident = self.env["trade.delivery.incident"].create({
            "distribution_id": self.id, "incident_type": incident_type,
            "description": description, "incident_date": incident_date or fields.Datetime.now(),
            "responsible_id": responsible_id or self.env.user.id,
        })
        self.message_post(body=_("Delivery incident recorded: %s.", incident.description))
        return incident

    def action_report_incident(self):
        self.ensure_one()
        self._trade_require_role()
        self.check_access_rights("write")
        self.check_access_rule("write")
        self._trade_check_state("active")
        return {"type": "ir.actions.act_window", "res_model": "trade.report.delivery.incident.wizard",
                "view_mode": "form", "target": "new", "context": {"default_distribution_id": self.id}}

    def action_open_deliveries(self):
        self.ensure_one()
        self.check_access_rights("read")
        self.check_access_rule("read")
        return {"type": "ir.actions.act_window", "res_model": "stock.picking", "view_mode": "tree,form",
                "domain": [("id", "in", self.picking_ids.ids)]}

    def copy(self, default=None):
        raise UserError(_("Create a distribution for a different sale; do not duplicate physical operations."))


class TradeDistributionLine(models.Model):
    _name = "trade.distribution.line"
    _description = "Trade Distribution Product"
    _inherit = "trade.child.mixin"
    _trade_parent_field = "distribution_id"
    _trade_managed_fields = ("product_id", "uom_id", "expected_quantity", "delivered_quantity", "pending_quantity")
    _rec_name = "product_id"

    distribution_id = fields.Many2one("trade.distribution", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="distribution_id.company_id", store=True, readonly=True, index=True)
    sale_line_id = fields.Many2one("sale.order.line", required=True, check_company=True, ondelete="restrict", index=True)
    product_id = fields.Many2one(related="sale_line_id.product_id", readonly=True)
    uom_id = fields.Many2one(related="sale_line_id.product_uom", readonly=True)
    expected_quantity = fields.Float(related="sale_line_id.product_uom_qty", readonly=True)
    delivered_quantity = fields.Float(related="sale_line_id.qty_delivered", readonly=True)
    pending_quantity = fields.Float(compute="_compute_pending")

    _sql_constraints = [
        ("sale_line_unique", "unique(sale_line_id)", "A sale line can belong to only one distribution."),
    ]

    @api.depends("expected_quantity", "delivered_quantity")
    def _compute_pending(self):
        for line in self:
            line.pending_quantity = max(line.expected_quantity - line.delivered_quantity, 0)

    @api.constrains("distribution_id", "sale_line_id")
    def _check_sale_line(self):
        for line in self:
            if line.sale_line_id.order_id != line.distribution_id.sale_order_id or line.sale_line_id.display_type:
                raise ValidationError(_("The distribution line must reference a product of its sale."))
