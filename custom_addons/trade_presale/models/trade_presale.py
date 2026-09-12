from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class TradePresale(models.Model):
    _name = "trade.presale"
    _description = "Trade Presale"
    _inherit = ["trade.document.mixin", "mail.thread"]
    _order = "id desc"
    _trade_managed_fields = ("sale_order_id", "is_overcommitted", "legacy_review_required")

    import_id = fields.Many2one("trade.import", required=True, check_company=True, ondelete="restrict", index=True)
    customer_id = fields.Many2one("res.partner", required=True, check_company=True, ondelete="restrict")
    pricelist_id = fields.Many2one(
        "product.pricelist", check_company=True, ondelete="restrict",
        default=lambda self: self.env["product.pricelist"].search([
            ("currency_id", "=", self.env.company.currency_id.id),
            ("company_id", "in", [False, self.env.company.id]),
        ], limit=1),
    )
    state = fields.Selection([
        ("draft", "Draft"), ("confirmed", "Confirmed"),
        ("converted", "Converted"), ("cancelled", "Cancelled"),
    ], required=True, default="draft", readonly=True, copy=False, tracking=True, index=True)
    line_ids = fields.One2many("trade.presale.line", "presale_id", string="Products", copy=True)
    sale_order_id = fields.Many2one("sale.order", readonly=True, copy=False, check_company=True, ondelete="restrict")
    allowed_product_ids = fields.Many2many("product.product", compute="_compute_allowed_products")
    is_overcommitted = fields.Boolean(compute="_compute_overcommitted")
    legacy_review_required = fields.Boolean(readonly=True, copy=False)

    @api.depends("import_id.line_ids.product_id")
    def _compute_allowed_products(self):
        for record in self:
            record.allowed_product_ids = record.import_id.line_ids.product_id

    @api.depends("line_ids.import_line_id.overcommitted")
    def _compute_overcommitted(self):
        for record in self:
            record.is_overcommitted = any(record.line_ids.import_line_id.mapped("overcommitted"))

    @api.constrains("import_id", "line_ids", "pricelist_id", "company_id")
    def _trade_check_invariants(self):
        for record in self:
            if record.import_id.company_id != record.company_id:
                raise ValidationError(_("The import and presale must belong to the same company."))
            if record.pricelist_id and record.pricelist_id.currency_id != record.currency_id:
                raise ValidationError(_("The pricelist must use the company currency."))
            record.line_ids._check_source()
        return True

    def _check_ready(self):
        self._trade_check_invariants()
        if self.legacy_review_required or self.import_id.legacy_review_required:
            raise UserError(_("Resolve the legacy review before continuing."))
        if not self.line_ids or not self.pricelist_id:
            raise UserError(_("Product lines and a company-currency pricelist are required."))
        if self.import_id.state not in ("validated", "in_transit", "receiving", "partially_received", "completed"):
            raise UserError(_("The import must be validated and not cancelled."))
        if any(not line.product_id.active for line in self.line_ids):
            raise UserError(_("A presale cannot be confirmed with archived products."))

    def action_confirm(self):
        self.ensure_one()
        self._trade_require_role()
        self._trade_lock()
        self._trade_check_state("draft")
        self._check_ready()
        self._trade_internal_write({"state": "confirmed"})
        if self.is_overcommitted:
            self.message_post(body=_("Warning: commercial commitments exceed this import's expected quantity. This is not a stock reservation."))
        return True

    def action_cancel(self):
        self._trade_require_role()
        self._trade_lock()
        self._trade_check_state("draft", "confirmed")
        if self.mapped("sale_order_id"):
            raise UserError(_("Cancel the quotation through Odoo Sales; retain its presale provenance."))
        self._trade_internal_write({"state": "cancelled"})
        return True

    def action_return_to_draft(self):
        self._trade_require_role("manager")
        self._trade_lock()
        self._trade_check_state("confirmed")
        if self.mapped("sale_order_id"):
            raise UserError(_("A converted commercial commitment cannot be reset."))
        self._trade_internal_write({"state": "draft"})
        return True

    def _convert_to_sale(self):
        self.ensure_one()
        self._trade_require_role()
        self._trade_lock()
        if self.state == "converted" and self.sale_order_id:
            return self.sale_order_id
        self._trade_check_state("confirmed")
        self._check_ready()
        if self.import_id.state != "completed":
            raise UserError(_("The import must be fully received before creating the quotation."))
        Sale = self.env["sale.order"].with_company(self.company_id)
        order = Sale.search([("trade_presale_id", "=", self.id)], limit=1)
        if not order:
            order = Sale.create({
                "partner_id": self.customer_id.id, "company_id": self.company_id.id,
                "pricelist_id": self.pricelist_id.id, "warehouse_id": self.import_id.warehouse_id.id,
                "origin": self.name, "trade_presale_id": self.id,
                "order_line": [fields.Command.create({
                    "product_id": line.product_id.id, "product_uom_qty": line.quantity,
                    "product_uom": line.uom_id.id, "price_unit": line.unit_price,
                    "trade_presale_line_id": line.id,
                }) for line in self.line_ids],
            })
        self._trade_internal_write({"sale_order_id": order.id, "state": "converted"})
        self.message_post(body=_("Presale converted to quotation %s.", order.name))
        return order

    def action_convert_to_sale(self):
        order = self._convert_to_sale()
        return {"type": "ir.actions.act_window", "res_model": "sale.order",
                "res_id": order.id, "view_mode": "form", "target": "current"}

    def action_open_sale(self):
        self.ensure_one()
        self.check_access_rights("read")
        self.check_access_rule("read")
        if not self.sale_order_id:
            raise UserError(_("No quotation has been generated yet."))
        return {"type": "ir.actions.act_window", "res_model": "sale.order",
                "res_id": self.sale_order_id.id, "view_mode": "form"}
