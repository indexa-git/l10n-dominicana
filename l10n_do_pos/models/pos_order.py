import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    l10n_latam_document_number = fields.Char(
        string="Fiscal Number",
    )
    l10n_latam_document_type_id = fields.Many2one(
        comodel_name="l10n_latam.document.type",
        string="Document Type",
    )
    l10n_latam_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Fiscal Sequence",
        copy=False,
    )
    l10n_do_ncf_expiration_date = fields.Date(
        string="NCF expiration date",
    )
    l10n_latam_use_documents = fields.Boolean()
    state = fields.Selection(
        selection_add=[
            ("is_l10n_do_return_order", "Credit note"),
        ],
    )
    l10n_do_origin_ncf = fields.Char(
        string="Modified NCF",
    )
    l10n_do_is_return_order = fields.Boolean(
        string="Return order",
        copy=False,
    )
    l10n_do_return_order_id = fields.Many2one(
        "pos.order",
        string="Modifies",
        readonly=True,
        copy=False,
    )
    l10n_do_return_status = fields.Selection(
        selection=[
            ("-", "Not returned"),
            ("fully_returned", "Fully returned"),
            ("partially_returned", "Partially Returned"),
            ("non_returnable", "Non Returnable"),
        ],
        default="-",
        copy=False,
        string="Return status",
    )
    l10n_do_payment_credit_note_ids = fields.One2many(
        "pos.order.payment.credit.note",
        "pos_order_id",
        string="Credit Note payments",
    )
    l10n_latam_country_code = fields.Char(
        related="company_id.country_id.code",
        help="Technical field used to hide/show fields regarding the localization",
    )

    @api.model
    def _order_fields(self, ui_order):
        """
        Prepare the dict of values to create the new pos order.
        """
        res = super(PosOrder, self)._order_fields(ui_order)
        if ui_order.get("l10n_latam_sequence_id", False) and ui_order["to_invoice"]:
            res.update(
                {
                    "l10n_latam_sequence_id": ui_order["l10n_latam_sequence_id"],
                    "l10n_latam_document_number": ui_order[
                        "l10n_latam_document_number"
                    ],
                    "l10n_latam_document_type_id": ui_order[
                        "l10n_latam_document_type_id"
                    ],
                    "l10n_latam_use_documents": True,
                    "l10n_do_origin_ncf": ui_order["l10n_do_origin_ncf"],
                    "l10n_do_return_status": ui_order["l10n_do_return_status"],
                    "l10n_do_is_return_order": ui_order["l10n_do_is_return_order"],
                    "l10n_do_return_order_id": ui_order["l10n_do_return_order_id"],
                    "l10n_do_ncf_expiration_date": ui_order[
                        "l10n_do_ncf_expiration_date"
                    ],
                }
            )

            for line in ui_order["lines"]:
                line_dic = line[2]
                original_line = self.env["pos.order.line"].browse(
                    line_dic.get("l10n_do_original_line_id", False)
                )
                original_line.l10n_do_line_qty_returned += abs(line_dic.get("qty", 0))

        return res

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        if res["payment_method_id"] == 10001:
            res.update(
                {
                    "name": ui_paymentline.get("note"),
                }
            )
        return res

    def add_payment(self, data):
        self.ensure_one()
        if data["payment_method_id"] == 10001:
            # TODO: CHECK WTF l10n_latam_document_number cant filter
            # TODO: AGREGAR SOLO EL MONTO DEL PAGO EN LA FACTURA, ACTUALMENTE SE AGREGA COMO "PAGO" LA NOTA DE CREDITO
            # EL PROBLEMA ES QUE SI LA NOTA DE CREDITO NO ES IGUAL AL PAGO HACE UNA DEVOLUCION POR LO TANTO EL "PAGO"
            # CON NOTA DE CREDITO QUEDA POR ENSIMA DE LA ORDEN (ESTO ES SOLO UN PROBLEMA VISUAL QUE PUEDE CONFUDNIR AL
            # USUARIO)
            account_move_credit_note = (
                self.env["pos.order"]
                .search([("l10n_latam_document_number", "=", data["name"])])
                .account_move
            )
            self.env["pos.order.payment.credit.note"].create(
                {
                    "amount": data["amount"],
                    "account_move_id": account_move_credit_note.id,
                    "pos_order_id": data["pos_order_id"],
                    "name": data["name"],
                }
            )
            self.amount_paid = sum(self.payment_ids.mapped("amount")) + sum(
                self.l10n_do_payment_credit_note_ids.mapped("amount")
            )

        elif not self.l10n_do_is_return_order:
            super(PosOrder, self).add_payment(data)
            self.amount_paid = sum(self.payment_ids.mapped("amount")) + sum(
                self.l10n_do_payment_credit_note_ids.mapped("amount")
            )

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        super(PosOrder, self)._process_payment_lines(
            pos_order, order, pos_session, draft
        )

        order.amount_paid = sum(order.payment_ids.mapped("amount")) + sum(
            order.l10n_do_payment_credit_note_ids.mapped("amount")
        )

        if sum(order.payment_ids.mapped("amount")) < 0:
            order.payment_ids.unlink()

    def _prepare_invoice_vals(self):
        invoice_vals = super(PosOrder, self)._prepare_invoice_vals()
        documents = self.config_id.invoice_journal_id.l10n_latam_use_documents

        if documents and self.to_invoice:
            invoice_vals["l10n_latam_sequence_id"] = self.l10n_latam_sequence_id.id
            invoice_vals["l10n_latam_document_number"] = self.l10n_latam_document_number
            invoice_vals[
                "l10n_latam_document_type_id"
            ] = self.l10n_latam_document_type_id.id

            invoice_vals["ncf_expiration_date"] = self.l10n_do_ncf_expiration_date
            invoice_vals["l10n_do_origin_ncf"] = self.l10n_do_origin_ncf

            # a POS sale invoice NCF is always an internal sequence
            invoice_vals["is_l10n_do_internal_sequence"] = True

            if self.l10n_do_is_return_order:
                invoice_vals["type"] = "out_refund"

        return invoice_vals

    @api.model
    def _process_order(self, order, draft, existing_order):
        if order["data"].get("to_invoice_backend", False):
            order["data"]["to_invoice"] = True
            order["to_invoice"] = True
            if not order["data"]["partner_id"]:
                pos_config = (
                    self.env["pos.session"]
                    .search([("id", "=", order["data"]["pos_session_id"])])
                    .config_id
                )
                if not pos_config.l10n_do_default_partner_id:
                    raise UserError(
                        _("This point of sale does not have a default customer.")
                    )
                order["data"]["partner_id"] = pos_config.l10n_do_default_partner_id.id

        return super(PosOrder, self)._process_order(order, draft, existing_order)

    @api.model
    def order_search_from_ui(self, day_limit=0, config_id=0, session_id=0):
        invoice_domain = [("type", "=", "out_invoice")]
        pos_order_domain = []

        if day_limit:
            today = fields.Date.from_string(fields.Date.context_today(self))
            limit = today - timedelta(days=day_limit)
            invoice_domain.append(("invoice_date", ">=", limit))

        if config_id:
            pos_order_domain.append(("config_id", "=", config_id))

        if session_id:
            pos_order_domain.append(("session_id", "=", session_id))

        invoice_ids = self.env["account.move"].search(invoice_domain)
        pos_order_domain.append(("account_move", "in", invoice_ids.ids))

        order_ids = self.search(pos_order_domain)
        order_list = []
        order_lines_list = []
        for order in order_ids:
            order_json = {
                "id": order.id,
                "name": order.name,
                "date_order": order.date_order,
                "partner_id": [order.partner_id.id, order.partner_id.name],
                "pos_reference": order.pos_reference,
                "account_move": [
                    order.account_move.id,
                    order.account_move.l10n_latam_document_number,
                ],
                "amount_total": order.amount_total,
                "l10n_latam_document_number": order.account_move.l10n_latam_document_number,
                "lines": [line.id for line in order.lines],
                "payment_ids": [payment_id.id for payment_id in order.payment_ids],
                "l10n_do_is_return_order": order.l10n_do_is_return_order,
            }
            if not order.l10n_do_is_return_order:
                order_json["l10n_do_return_status"] = order.l10n_do_return_status
            else:
                order.l10n_do_return_order_id.l10n_do_return_status = (
                    order.l10n_do_return_status
                )
                order_json["l10n_do_return_order_id"] = order.l10n_do_return_order_id.id
                order_json[
                    "l10n_do_return_status"
                ] = order.l10n_do_return_order_id.l10n_do_return_status

            for line in order.lines:
                order_lines_json = {
                    "order_id": [order.id, order.name],
                    "id": line.id,
                    "discount": line.discount,
                    "price_subtotal": line.price_subtotal,
                    "price_subtotal_incl": line.price_subtotal_incl,
                    "qty": line.qty,
                    "price_unit": line.price_unit,
                    "product_id": [line.product_id.id, line.product_id.name],
                    "l10n_do_line_qty_returned": line.l10n_do_line_qty_returned,
                }
                order_lines_list.append(order_lines_json)
            order_list.append(order_json)
        return {"orders": order_list, "orderlines": order_lines_list}

    def _is_pos_order_paid(self):
        if self.filtered(
            lambda order: order.l10n_latam_use_documents
            and order.l10n_do_is_return_order
        ):
            return True
        return super(PosOrder, self)._is_pos_order_paid()

    def action_pos_order_invoice(self):
        res = super(PosOrder, self).action_pos_order_invoice()
        for order in self:
            if order.l10n_do_is_return_order:
                order.sudo().write({"state": "is_l10n_do_return_order"})

            # Reconcile Credit Notes
            invoice_rec_line = order.account_move.line_ids.filtered(
                lambda l: l.debit > 0 and l.account_id.user_type_id.type == "receivable"
            )
            for credit_note in order.l10n_do_payment_credit_note_ids:
                credit_note_rec_line = credit_note.account_move_id.line_ids.filtered(
                    lambda l: l.account_id.id == invoice_rec_line.account_id.id
                )
                to_reconcile = invoice_rec_line | credit_note_rec_line
                to_reconcile.sudo().auto_reconcile_lines()
        return res

    @api.model
    def credit_note_info_from_ui(self, ncf):
        # TODO: CHECK WTF l10n_latam_document_number cant filter
        out_refund_invoice = (
            self.env["pos.order"]
            .search(
                [
                    ("l10n_latam_document_number", "=", ncf),
                    ("l10n_do_is_return_order", "=", True),
                ]
            )
            .account_move
        )
        return {
            "id": out_refund_invoice.id,
            "residual": out_refund_invoice.amount_residual,
            "partner_id": out_refund_invoice.partner_id.id,
        }

    def _get_amount_receivable(self):
        if self.state == "is_l10n_do_return_order":
            return 0
        return super(PosOrder, self)._get_amount_receivable()


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    l10n_do_line_qty_returned = fields.Integer(  # TODO: not Float values?
        string="Return line",
        default=0,
    )
    l10n_do_original_line_id = fields.Many2one(
        comodel_name="pos.order.line",
        string="Original line",
    )

    @api.model
    def _order_line_fields(self, line, session_id=None):
        fields_return = super(PosOrderLine, self)._order_line_fields(line, session_id)
        fields_return[2].update(
            {
                "l10n_do_line_qty_returned": line[2].get(
                    "l10n_do_line_qty_returned", ""
                ),
                "l10n_do_original_line_id": line[2].get("l10n_do_original_line_id", ""),
            }
        )
        return fields_return


class PosOrderPaymentCreditNote(models.Model):
    _name = "pos.order.payment.credit.note"
    _rec_name = "name"
    _description = "POS Credit Notes"

    name = fields.Char()
    amount = fields.Monetary()
    account_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Credit note",
        required=False,
    )
    currency_id = fields.Many2one(
        related="account_move_id.currency_id",
    )
    pos_order_id = fields.Many2one(
        comodel_name="pos.order",
        string="order",
        required=False,
    )
