# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################

import logging
import psycopg2
import time

from odoo import models, fields, api, tools, exceptions, _
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_return_order = fields.Boolean(string='Return Order', copy=False)
    return_order_id = fields.Many2one('pos.order', 'Return Order Of', readonly=True, copy=False)
    return_status = fields.Selection(
        [('-', 'Nor Returned'), ('Fully-Returned', 'Fully-Returned'), ('Partially-Returned', 'Partially-Returned'),
         ('Non-Returnable', 'Non-Returnable')], default='-', copy=False, string='Return Status')


    @api.model
    def create_from_ui_second_step(self, order_ids):
        # order_ids = super(PosOrder, self).create_from_ui(orders);
        order_objs = self.env['pos.order'].browse(order_ids);
        result = {}
        order_list = []
        order_line_list = []
        statement_list = []
        for order_obj in order_objs:
            vals = {}
            vals['lines'] = []
            if hasattr(order_objs[0], 'return_status'):
                if not order_obj.is_return_order:
                    vals['return_status'] = order_obj.return_status
                    vals['existing'] = False
                    vals['id'] = order_obj.id
                else:
                    order_obj.return_order_id.return_status = order_obj.return_status
                    vals['existing'] = True
                    vals['id'] = order_obj.id
                    vals['original_order_id'] = order_obj.return_order_id.id
                    vals['return_status'] = order_obj.return_order_id.return_status
                    for line in order_obj.lines:
                        line_vals = {}
                        line_vals['id'] = line.original_line_id.id
                        line_vals['line_qty_returned'] = line.original_line_id.line_qty_returned
                        line_vals['existing'] = True
                        order_line_list.append(line_vals)
            vals['statement_ids'] = order_obj.statement_ids.ids
            vals['name'] = order_obj.name
            vals['amount_total'] = order_obj.amount_total
            vals['pos_reference'] = order_obj.pos_reference
            vals['date_order'] = order_obj.date_order
            if order_obj.invoice_id:
                vals['invoice_id'] = order_obj.invoice_id.id
            else:
                vals['invoice_id'] = False
            if order_obj.partner_id:
                vals['partner_id'] = [order_obj.partner_id.id, order_obj.partner_id.name]
            else:
                vals['partner_id'] = False
            if (not hasattr(order_objs[0], 'return_status') or (
                hasattr(order_objs[0], 'return_status') and not order_obj.is_return_order)):
                vals['id'] = order_obj.id
                for line in order_obj.lines:
                    vals['lines'].append(line.id)
                    line_vals = {}
                    # LINE DATAA
                    line_vals['create_date'] = line.create_date
                    line_vals['discount'] = line.discount
                    line_vals['display_name'] = line.display_name
                    line_vals['id'] = line.id
                    line_vals['order_id'] = [line.order_id.id, line.order_id.name]
                    line_vals['price_subtotal'] = line.price_subtotal
                    line_vals['price_subtotal_incl'] = line.price_subtotal_incl
                    line_vals['price_unit'] = line.price_unit
                    line_vals['product_id'] = [line.product_id.id, line.product_id.name]
                    line_vals['qty'] = line.qty
                    line_vals['write_date'] = line.write_date
                    if hasattr(line, 'line_qty_returned'):
                        line_vals['line_qty_returned'] = line.line_qty_returned
                    # LINE DATAA
                    order_line_list.append(line_vals)
                for statement_id in order_obj.statement_ids:
                    statement_vals = {}
                    # STATEMENT DATAA
                    statement_vals['amount'] = statement_id.amount
                    statement_vals['id'] = statement_id.id
                    if statement_id.journal_id:
                        currency = statement_id.journal_id.currency_id or statement_id.journal_id.company_id.currency_id
                        statement_vals['journal_id'] = [statement_id.journal_id.id,
                                                        statement_id.journal_id.name + " (" + currency.name + ")"]
                    else:
                        statement_vals['journal_id'] = False
                    statement_list.append(statement_vals)
            order_list.append(vals)
        result['orders'] = order_list
        result['orderlines'] = order_line_list
        result['statements'] = statement_list
        return result

    @api.model
    def create_from_ui(self, orders):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search([('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]
        order_ids = []

        for tmp_order in orders_to_save:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
                self._match_payment_to_invoice(order)
            pos_order = self._process_order(order)
            order_ids.append(pos_order.id)

            try:
                pos_order.action_pos_order_paid()
            except psycopg2.OperationalError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            if not pos_order.partner_id:
                pos_order.partner_id = pos_order.session_id.config_id.default_partner_id.id
            pos_order.action_pos_order_invoice()
            pos_order.invoice_id.sale_fiscal_type = pos_order.partner_id.sale_fiscal_type
            pos_order.invoice_id.sudo().action_invoice_open()
        return self.create_from_ui_second_step(order_ids)

    @api.model
    def get_fiscal_data(self, name):

        res = {}

        order_state = False
        while not order_state == 'invoiced':
            time.sleep(1)
            order_id = self.search([('pos_reference','=',name)])
            if order_id:
                order_state = order_id.state
            self._cr.commit()

        res.update({"ncf": order_id.invoice_id.number})
        if order_id.invoice_id.sale_fiscal_type == "fiscal":
            res.update({"fiscal_type": "fiscal", "fiscal_type_name": "FACTURA CON VALOR FISCAL"})
        elif order_id.invoice_id.sale_fiscal_type == "final":
            res.update({"fiscal_type": "final", "fiscal_type_name": "FACTURA PARA CONSUMIDOR FINAL"})
        elif order_id.invoice_id.sale_fiscal_type == "gov":
            res.update({"fiscal_type": "fiscal", "fiscal_type_name": "FACTURA GUBERNAMENTAL"})
        elif order_id.invoice_id.sale_fiscal_type == "special":
            res.update({"fiscal_type": "special", "fiscal_type_name": "FACTURA PARA REGIMENES ESPECIALES"})

        return res

    @api.model
    def _order_fields(self, ui_order):
        fields_return = super(PosOrder, self)._order_fields(ui_order)
        fields_return.update({
            'is_return_order': ui_order.get('is_return_order') or False,
            'return_order_id': ui_order.get('return_order_id') or False,
            'return_status': ui_order.get('return_status') or False,
        })
        return fields_return

    @api.model
    def _process_order(self, pos_order):
        prec_acc = self.env['decimal.precision'].precision_get('Account')
        pos_session = self.env['pos.session'].browse(pos_order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            pos_order['pos_session_id'] = self._get_valid_session(pos_order).id
        if pos_order['is_return_order']:
            pos_order['amount_paid'] = 0
            for line in pos_order['lines']:
                line_dict = line[2]
                line_dict['qty'] = line_dict['qty'] * -1
                original_line = self.env['pos.order.line'].browse(line_dict['original_line_id'])
                original_line.line_qty_returned += abs(line_dict['qty'])
            for statement in pos_order['statement_ids']:
                statement_dict = statement[2]
                statement_dict['amount'] = statement_dict['amount'] * -1
            pos_order['amount_tax'] = pos_order['amount_tax'] * -1
            pos_order['amount_return'] = 0
            pos_order['amount_total'] = pos_order['amount_total'] * -1

        order = self.create(self._order_fields(pos_order))
        journal_ids = set()
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
                order.add_payment(self._payment_fields(payments[2]))
            journal_ids.add(payments[2]['journal_id'])

        if pos_session.sequence_number <= pos_order['sequence_number']:
            pos_session.write({'sequence_number': pos_order['sequence_number'] + 1})
            pos_session.refresh()

        if not float_is_zero(pos_order['amount_return'], prec_acc):
            cash_journal_id = pos_session.cash_journal_id.id
            if not cash_journal_id:
                # Select for change one of the cash journals used in this
                # payment
                cash_journal = self.env['account.journal'].search([
                    ('type', '=', 'cash'),
                    ('id', 'in', list(journal_ids)),
                ], limit=1)
                if not cash_journal:
                    # If none, select for change one of the cash journals of the POS
                    # This is used for example when a customer pays by credit card
                    # an amount higher than total amount of the order and gets cash back
                    cash_journal = [statement.journal_id for statement in pos_session.statement_ids if
                                    statement.journal_id.type == 'cash']
                    if not cash_journal:
                        raise exceptions.UserError(_("No cash statement found for this session. Unable to record returned cash."))
                cash_journal_id = cash_journal[0].id
            order.add_payment({
                'amount': -pos_order['amount_return'],
                'payment_date': fields.Datetime.now(),
                'payment_name': _('return'),
                'journal': cash_journal_id,
            })
        return order


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    line_qty_returned = fields.Integer('Line Returned', default=0)
    original_line_id = fields.Many2one('pos.order.line', "Original line")

    @api.model
    def _order_line_fields(self, line):
        fields_return = super(PosOrderLine, self)._order_line_fields(line)
        fields_return[2].update({'line_qty_returned': line[2].get('line_qty_returned', '')})
        fields_return[2].update({'original_line_id': line[2].get('original_line_id', '')})
        return fields_return