# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2017 Raúl Ovalle <rovalle@guavana.com>
# © 2018 Jorge Hernández <jhernandez@gruponeotec.com>
# © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
# © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
# © 2019-2020 Raul Ovalle <raulovallet@gmail.com>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    l10n_latam_document_number = fields.Char(
        string="Número de documento",
    )
    l10n_latam_document_type_id = fields.Many2one(
        comodel_name='l10n_latam.document.type',
        string="Document Type",
    )
    l10n_latam_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string="Fiscal Sequence",
        copy=False,
    )
    ncf_expiration_date = fields.Date(
        string="NCF expiration date",
    )
    l10n_latam_use_documents = fields.Boolean()

    # Credit notes

    state = fields.Selection(
        selection_add=[
            ('is_return_order', 'Credit note'),
        ],
    )
    l10n_do_origin_ncf = fields.Char(
        string="Modifies",
    )
    is_return_order = fields.Boolean(
        string='Return order',
        copy=False,
    )
    return_order_id = fields.Many2one(
        comodel_name='pos.order',
        string='Afecta',
        readonly=True,
        copy=False,
    )
    return_status = fields.Selection(
        selection=[
            ('-', 'No Devuelta'),
            ('Fully-Returned', 'Totalmente Devuelta'),
            ('Partially-Returned', 'Parcialmente Devuelta'),
            ('Non-Returnable', 'No Retornable')
        ],
        default='-',
        copy=False,
        string='Return status',
    )
    payment_credit_note_ids = fields.One2many(
        comodel_name="pos.order.payment.credit.note",
        inverse_name="pos_order_id",
        string="Credit note payments",
        required=False,
    )

    # is_used_in_order = fields.Boolean(
    #     default=False
    # )

    @api.model
    def _order_fields(self, ui_order):
        """
        Prepare the dict of values to create the new pos order.
        """
        fields = super(PosOrder, self)._order_fields(ui_order)
        # if ui_order.get('fiscal_sequence_id', False):
        if ui_order.get('l10n_latam_sequence_id', False) and ui_order['to_invoice']:
            fields['l10n_latam_sequence_id'] = ui_order['l10n_latam_sequence_id']
            fields['l10n_latam_document_number'] = \
                ui_order['l10n_latam_document_number']
            fields['l10n_latam_document_type_id'] = \
                ui_order['l10n_latam_document_type_id']
            fields['l10n_latam_use_documents'] = True
            fields['l10n_do_origin_ncf'] = ui_order['l10n_do_origin_ncf']
            fields['return_status'] = ui_order['return_status']
            fields['is_return_order'] = ui_order['is_return_order']
            fields['return_order_id'] = ui_order['return_order_id']
            # fields['ncf_expiration_date'] = ui_order['ncf_expiration_date']

            for line in ui_order['lines']:
                line_dic = line[2]
                original_line = self.env['pos.order.line'].browse(
                    line_dic["original_line_id"])
                original_line.line_qty_returned += \
                    abs(line_dic.get('qty', 0))

        return fields

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        fields = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        if fields['payment_method_id'] == 10001:
            fields.update({
                'name': ui_paymentline.get('note'),
            })
        return fields

    def add_payment(self, data):
        self.ensure_one()
        if data['payment_method_id'] == 10001:
            # TODO: CHECK WTF l10n_latam_document_number cant filter
            # TODO: AGREGAR SOLO EL MONTO DEL PAGO EN LA FACTURA, ACTUALMENTE SE AGREGA COMO "PAGO" LA NOTA DE CREDITO
            # EL PROBLEMA ES QUE SI LA NOTA DE CREDITO NO ES IGUAL AL PAGO HACE UNA DEVOLUCION POR LO TANTO EL "PAGO"
            # CON NOTA DE CREDITO QUEDA POR ENSIMA DE LA ORDEN (ESTO ES SOLO UN PROBLEMA VISUAL QUE PUEDE CONFUDNIR AL
            # USUARIO)
            account_move_credit_note = self.env['pos.order'].search([
                ('l10n_latam_document_number', '=', data['name'])]).account_move
            self.env["pos.order.payment.credit.note"].create({
                'amount': data['amount'],
                'account_move_id': account_move_credit_note.id,
                'pos_order_id': data['pos_order_id'],
                'name': data['name'],
            })
            self.amount_paid = sum(
                self.payment_ids.mapped('amount')) + sum(self.payment_credit_note_ids.mapped('amount'))

        elif not self.is_return_order:
            super(PosOrder, self).add_payment(data)
            self.amount_paid = sum(
                self.payment_ids.mapped('amount')) + sum(self.payment_credit_note_ids.mapped('amount'))

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        super(PosOrder, self)._process_payment_lines(pos_order, order, pos_session, draft)

        order.amount_paid = sum(
            order.payment_ids.mapped('amount')) + sum(order.payment_credit_note_ids.mapped('amount'))

        if sum(order.payment_ids.mapped('amount')) < 0:
            order.payment_ids.unlink()

    def _prepare_invoice_vals(self):
        """
        Prepare the dict of values to create the new invoice for a pos order.
        """
        invoice_vals = super(PosOrder, self)._prepare_invoice_vals()
        documents = self.config_id.invoice_journal_id.l10n_latam_use_documents
        if documents and self.to_invoice:
            invoice_vals['l10n_latam_sequence_id'] = self.l10n_latam_sequence_id.id
            invoice_vals['l10n_latam_document_number'] = self.l10n_latam_document_number
            invoice_vals['l10n_latam_document_type_id'] = \
                self.l10n_latam_document_type_id.id

            invoice_vals['l10n_do_origin_ncf'] = self.l10n_do_origin_ncf
            if self.is_return_order:
                invoice_vals['type'] = 'out_refund'

        return invoice_vals

    @api.model
    def _process_order(self, order, draft, existing_order):
        """
        this part is using for eliminate cash return
        :param pos_order:
        :return:
        """
        if order['data']['to_invoice_backend']:
            order['data']['to_invoice'] = True
            order['to_invoice'] = True
            if not order['data']['partner_id']:
                pos_config = self.env['pos.session']\
                    .search([('id', '=', order['data']['pos_session_id'])]).config_id
                if not pos_config.default_partner_id:
                    raise UserError(
                        _('This point of sale not have default customer,'
                          ' please set default customer in config POS'))
                order['data']['partner_id'] = pos_config.default_partner_id.id

        return super(PosOrder, self)._process_order(order, draft, existing_order)

    # Credit notes

    @api.model
    def order_search_from_ui(
            self, day_limit=0, config_id=0, session_id=0):
        invoice_domain = [('type', '=', 'out_invoice')]
        pos_order_domain = []

        if day_limit:
            today = fields.Date.from_string(fields.Date.context_today(self))
            limit = today - timedelta(days=day_limit)
            invoice_domain.append(('invoice_date', '>=', limit))

        if config_id:
            pos_order_domain.append(('config_id', '=', config_id))

        if session_id:
            pos_order_domain.append(('session_id', '=', session_id))

        invoice_ids = self.env["account.move"].search(invoice_domain)
        pos_order_domain.append(('account_move', 'in', invoice_ids.ids))

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
                "account_move": [order.account_move.id, order.account_move.l10n_latam_document_number],
                "amount_total": order.amount_total,
                "l10n_latam_document_number": order.account_move.l10n_latam_document_number,
                "lines": [line.id for line in order.lines],
                "payment_ids": [
                    payment_id.id for payment_id in order.payment_ids
                ],
                "is_return_order": order.is_return_order
            }
            if not order.is_return_order:
                order_json['return_status'] = order.return_status
            else:
                order.return_order_id.return_status = order.return_status
                order_json['return_order_id'] = order.return_order_id.id
                order_json['return_status'] = order.return_order_id.return_status

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
                    "line_qty_returned": line.line_qty_returned
                }
                order_lines_list.append(order_lines_json)
            order_list.append(order_json)
        return {"orders": order_list, "orderlines": order_lines_list}

    def _is_pos_order_paid(self):
        """A Point of Sale is paid when the sum
        @return: True
        """
        for order in self:
            if not order.l10n_latam_use_documents:
                return super(PosOrder, self)._is_pos_order_paid()
            else:
                if order.is_return_order:
                    return True
                else:
                    return super(PosOrder, self)._is_pos_order_paid()

    def action_pos_order_invoice(self):
        res = super(PosOrder, self).action_pos_order_invoice()
        for order in self:
            if order.is_return_order:
                order.sudo().write({'state': 'is_return_order'})

            # Reconcile Credit Notes
            invoice_rec_line = order.account_move.line_ids.filtered(
                lambda l: l.debit > 0
            )
            for credit_note in order.payment_credit_note_ids:
                credit_note_rec_line = credit_note.account_move_id.line_ids.filtered(
                    lambda l: l.account_id.id == invoice_rec_line.account_id.id
                )
                to_reconcile = invoice_rec_line | credit_note_rec_line
                to_reconcile.sudo().auto_reconcile_lines()
        return res

    @api.model
    def credit_note_info_from_ui(self, ncf):
        # TODO: CHECK WTF l10n_latam_document_number cant filter
        out_refund_invoice = self.env["pos.order"].search([
            ('l10n_latam_document_number', '=', ncf),
            ('is_return_order', '=', True),
        ]).account_move
        return {
            "id": out_refund_invoice.id,
            "residual": out_refund_invoice.amount_residual,
            "partner_id": out_refund_invoice.partner_id.id
        }


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    line_qty_returned = fields.Integer(
        string='Return line',
        default=0,
    )
    original_line_id = fields.Many2one(
        comodel_name='pos.order.line',
        string="Original line",
    )

    @api.model
    def _order_line_fields(self, line, session_id=None):
        fields_return = super(
            PosOrderLine, self)._order_line_fields(line, session_id)
        fields_return[2].update({
            'line_qty_returned': line[2].get('line_qty_returned', ''),
            'original_line_id': line[2].get('original_line_id', '')
        })
        return fields_return


class PosOrderPaymentCreditNote(models.Model):
    _name = 'pos.order.payment.credit.note'
    _rec_name = 'name'
    _description = 'This is de paid credit notes'

    name = fields.Char()
    amount = fields.Monetary()
    account_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Credit note",
        required=False,
    )
    currency_id = fields.Many2one(
        related='account_move_id.currency_id',
    )
    pos_order_id = fields.Many2one(
        comodel_name="pos.order",
        string="order",
        required=False,
    )
