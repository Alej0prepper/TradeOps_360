from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class TradeImport(models.Model):
    _name = "trade.import"
    _description = "Trade Import"
    _inherit = ["trade.document.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _trade_managed_fields = (
        "purchase_order_ids", "legacy_review_required", "purchase_total",
        "expense_total", "landed_total", "line_count", "total_quantity",
    )

    import_date = fields.Date(required=True, default=fields.Date.context_today)
    reference = fields.Char(string="External Reference")
    customer_id = fields.Many2one("res.partner", required=True, check_company=True, ondelete="restrict")
    financier_id = fields.Many2one("res.partner", check_company=True, ondelete="restrict")
    supplier_id = fields.Many2one(
        "res.partner", check_company=True, ondelete="restrict",
        domain=[("supplier_rank", ">", 0)],
    )
    warehouse_id = fields.Many2one("stock.warehouse", check_company=True, ondelete="restrict")
    origin_port_id = fields.Many2one("trade.port", required=True, ondelete="restrict")
    destination_port_id = fields.Many2one("trade.port", required=True, ondelete="restrict")
    line_ids = fields.One2many("trade.import.line", "import_id", string="Products", copy=True)
    expense_ids = fields.One2many("trade.import.expense", "import_id", string="Expenses", copy=True)
    line_count = fields.Integer(compute="_compute_import_totals", store=True)
    total_quantity = fields.Float(compute="_compute_import_totals", store=True)
    purchase_total = fields.Monetary(compute="_compute_cost_totals", store=True)
    expense_total = fields.Monetary(compute="_compute_cost_totals", store=True)
    landed_total = fields.Monetary(string="Operational Total Cost", compute="_compute_cost_totals", store=True)
    purchase_order_ids = fields.One2many("purchase.order", "trade_import_id", copy=False, readonly=True)
    picking_ids = fields.Many2many("stock.picking", compute="_compute_pickings")
    legacy_review_required = fields.Boolean(readonly=True, copy=False)
    state = fields.Selection([
        ("draft", "Draft"), ("document_review", "Document Review"),
        ("validated", "Validated"), ("in_transit", "In Transit"),
        ("receiving", "Receiving"), ("partially_received", "Partially Received"),
        ("completed", "Completed"), ("cancelled", "Cancelled"),
    ], required=True, default="draft", copy=False, readonly=True, tracking=True, index=True)
    notes = fields.Text()

    @api.depends("line_ids.quantity")
    def _compute_import_totals(self):
        for record in self:
            record.line_count = len(record.line_ids)
            record.total_quantity = sum(record.line_ids.mapped("quantity"))

    @api.depends("line_ids.purchase_subtotal", "expense_ids.amount", "currency_id")
    def _compute_cost_totals(self):
        for record in self:
            currency = record.currency_id or record.company_id.currency_id
            record.purchase_total = currency.round(sum(record.line_ids.mapped("purchase_subtotal")))
            record.expense_total = currency.round(sum(record.expense_ids.mapped("amount")))
            record.landed_total = record.purchase_total + record.expense_total

    @api.depends("purchase_order_ids.picking_ids")
    def _compute_pickings(self):
        for record in self:
            record.picking_ids = record.purchase_order_ids.picking_ids

    @api.constrains("origin_port_id", "destination_port_id")
    def _check_ports(self):
        if any(record.origin_port_id == record.destination_port_id for record in self):
            raise ValidationError(_("Origin and destination ports must be different."))

    @api.onchange("origin_port_id", "destination_port_id")
    def _onchange_ports(self):
        if self.origin_port_id and self.origin_port_id == self.destination_port_id:
            return {"warning": {"title": _("Check the ports"), "message": _("Origin and destination are the same.")}}

    @api.constrains("line_ids", "expense_ids")
    def _trade_check_invariants(self):
        for record in self:
            if record.expense_total and record.purchase_total <= 0:
                raise ValidationError(_("Import expenses require a positive purchase-value allocation basis."))
        return True

    def _check_ready_for_review(self):
        for record in self:
            if record.legacy_review_required:
                raise UserError(_("Review this migrated operation before continuing."))
            if not record.supplier_id or not record.warehouse_id or not record.line_ids:
                raise UserError(_("A supplier, destination warehouse and product lines are required."))
            if not record.supplier_id.active or not record.supplier_id.supplier_rank:
                raise UserError(_("Select an active supplier."))
            if not record.origin_port_id.active or not record.destination_port_id.active:
                raise UserError(_("Select active ports."))
            if any(not line.product_id.active or line.product_id.type != "product" for line in record.line_ids):
                raise UserError(_("Phase 1 imports require active storable products."))
            record._check_company()
            record.line_ids._check_company()
            record._trade_check_invariants()

    def action_submit(self):
        self.ensure_one()
        self._trade_require_role()
        self._trade_lock()
        self._trade_check_state("draft")
        self._check_ready_for_review()
        self._trade_internal_write({"state": "document_review"})
        return True

    def action_return_to_draft(self):
        self.ensure_one()
        self._trade_require_role("manager")
        self._trade_lock()
        self._trade_check_state("document_review")
        if self.purchase_order_ids:
            raise UserError(_("A linked purchase prevents returning to draft."))
        self._trade_internal_write({"state": "draft"})
        return True

    def action_validate(self):
        self.ensure_one()
        self._trade_require_role("manager")
        self._trade_lock()
        self._trade_check_state("document_review")
        self._check_ready_for_review()
        if self.purchase_order_ids:
            raise UserError(_("This import already has its purchase document."))
        order = self.env["purchase.order"].with_company(self.company_id).create({
            "partner_id": self.supplier_id.id, "company_id": self.company_id.id,
            "currency_id": self.currency_id.id, "picking_type_id": self.warehouse_id.in_type_id.id,
            "origin": self.name, "trade_import_id": self.id,
            "order_line": [fields.Command.create({
                "name": line.product_id.display_name, "product_id": line.product_id.id,
                "product_qty": line.quantity, "product_uom": line.uom_id.id,
                "price_unit": line.unit_purchase_price, "date_planned": fields.Datetime.now(),
                "trade_import_line_id": line.id,
            }) for line in self.line_ids],
        })
        self._trade_internal_write({"state": "validated"})
        self.message_post(body=_("Import validated; purchase %s created.", order.name))
        return self.action_open_purchase()

    def action_start_transit(self):
        self.ensure_one()
        self._trade_require_role("manager")
        self._trade_lock()
        self._trade_check_state("validated")
        order = self.purchase_order_ids
        if len(order) != 1:
            raise UserError(_("Exactly one linked purchase is required."))
        if order.state in ("draft", "sent"):
            order.button_confirm()
        if order.state == "to approve":
            order.button_approve()
        if order.state not in ("purchase", "done"):
            raise UserError(_("The purchase must be confirmed."))
        self._trade_internal_write({"state": "in_transit"})
        if any(line.received_quantity for line in self.line_ids):
            self._sync_receipt_state()
        return True

    def action_receive(self):
        self.ensure_one()
        self._trade_require_role()
        self._trade_lock()
        self._trade_check_state("in_transit", "receiving", "partially_received")
        if self.state == "in_transit":
            self._trade_internal_write({"state": "receiving"})
        return self.action_open_receipts()

    def _sync_receipt_state(self):
        for record in self.sorted("id"):
            record._trade_lock()
            if record.state not in ("in_transit", "receiving", "partially_received", "completed"):
                continue
            complete = bool(record.line_ids) and all(
                float_compare(line.received_quantity, line.quantity, precision_rounding=line.uom_id.rounding) >= 0
                for line in record.line_ids
            )
            received = any(line.received_quantity > 0 for line in record.line_ids)
            state = "completed" if complete else "partially_received" if received else "receiving"
            if state != record.state:
                record._trade_internal_write({"state": state})

    def action_refresh_receipts(self):
        self._trade_require_role()
        self._sync_receipt_state()
        return True

    def action_cancel(self):
        self.ensure_one()
        self._trade_require_role("manager")
        self._trade_lock()
        self._trade_check_state("draft", "document_review", "validated", "in_transit", "receiving")
        if self.picking_ids.move_ids.filtered(lambda move: move.state == "done"):
            raise UserError(_("Received goods require standard returns, not import cancellation."))
        self._trade_internal_write({"state": "cancelled"})
        self.purchase_order_ids.filtered(lambda order: order.state != "cancel").button_cancel()
        return True

    def action_review_legacy(self):
        self.ensure_one()
        self._trade_require_role("manager")
        self._trade_lock()
        if not self.legacy_review_required or self.purchase_order_ids:
            raise UserError(_("Only an unlinked legacy operation can be returned for review."))
        self._trade_internal_write({"state": "draft", "legacy_review_required": False})
        self.message_post(body=_("Legacy operation returned to draft for explicit functional review."))
        return True

    def action_open_purchase(self):
        self.ensure_one()
        self.check_access_rights("read")
        self.check_access_rule("read")
        return {"type": "ir.actions.act_window", "res_model": "purchase.order", "view_mode": "tree,form",
                "domain": [("id", "in", self.purchase_order_ids.ids)]}

    def action_open_receipts(self):
        self.ensure_one()
        self.check_access_rights("read")
        self.check_access_rule("read")
        return {"type": "ir.actions.act_window", "res_model": "stock.picking", "view_mode": "tree,form",
                "domain": [("id", "in", self.picking_ids.ids)]}
