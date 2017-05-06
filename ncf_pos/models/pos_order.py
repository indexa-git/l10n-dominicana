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
import time

from odoo import models, fields, api, tools, exceptions, _
from odoo.tools import float_is_zero

from odoo.tools.safe_eval import safe_eval
import simplejson as json

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def get_pos_session_concile_type(self):
        IrConfigParam = self.env['ir.config_parameter']
        return safe_eval(IrConfigParam.get_param('ncf_pos.pos_session_concile_type', 'ticket'))

    def get_pos_session_picking_on_cron(self):
        IrConfigParam = self.env['ir.config_parameter']
        return safe_eval(IrConfigParam.get_param('ncf_pos.pos_session_picking_on_cron', 'False'))

    is_return_order = fields.Boolean(string='Devolver orden', copy=False)
    return_order_id = fields.Many2one('pos.order', u'Orden de devolución de', readonly=True, copy=False)
    return_status = fields.Selection(
        [('-', 'Sin Devoluciones'), ('Fully-Returned', 'Totalmente devuelto'),
         ('Partially-Returned', 'Devuelto parcialmente'),
         ('Non-Returnable', 'No retornable')], default='-', copy=False, string=u'Estado de devolución')
    invoice_number = fields.Char(related="invoice_id.number")
    is_service_order = fields.Boolean("Ordenes que no generan picking")

    @api.model
    def create_from_ui(self, orders):
        for order in orders:
            order.update({"to_invoice": True})
        order_ids = super(PosOrder, self).create_from_ui(orders)
        order_objs = self.env['pos.order'].browse(order_ids)
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

    @api.multi
    def action_pos_order_paid(self):
        if not self.get_pos_session_picking_on_cron():
            return super(PosOrder, self).action_pos_order_paid()
        else:
            if not self.test_paid():
                raise exceptions.UserError(_("Order is not paid."))
            self.write({'state': 'paid'})
            return True

    def _prepare_invoice(self):
        res = super(PosOrder, self)._prepare_invoice()
        if self.is_return_order:
            res.update({"type": "out_refund"})
        return res

    @api.model
    def get_fiscal_data(self, name):
        res = {"fiscal_type": "none", "fiscal_type_name": u"PRE-CUENTA"}

        order_state = False
        order_id = False

        while not order_state == 'invoiced':
            time.sleep(1)
            order_id = self.search([('pos_reference', '=', name)])
            if order_id:
                order_state = order_id.state
            self._cr.commit()

        if order_id:
            res.update({"ncf": order_id.invoice_id.number, "id": order_id.id, "rnc": order_id.partner_id.vat,
                        "name": order_id.partner_id.name})
            if order_id.is_return_order:
                res.update({"fiscal_type_name": u"NOTA DE CRÉDITO"})

                reference_ncf = order_id.return_order_id.invoice_id.number
                reference_ncf_type = reference_ncf[9:11]
                if reference_ncf_type in ("01", "14"):
                    res.update({"fiscal_type": "fiscal_note"})
                elif reference_ncf_type == "02":
                    res.update({"fiscal_type": "final_note"})
                elif reference_ncf_type == "15":
                    res.update({"fiscal_type": "special_note"})
                res.update({"origin": reference_ncf})

            elif order_id.invoice_id.sale_fiscal_type == "fiscal":
                res.update({"fiscal_type": "fiscal", "fiscal_type_name": "FACTURA CON VALOR FISCAL", "origin": False})
            elif order_id.invoice_id.sale_fiscal_type == "final":
                res.update({"fiscal_type": "final", "fiscal_type_name": "FACTURA PARA CONSUMIDOR FINAL", "origin": False})
            elif order_id.invoice_id.sale_fiscal_type == "gov":
                res.update({"fiscal_type": "fiscal", "fiscal_type_name": "FACTURA GUBERNAMENTAL", "origin": False})
            elif order_id.invoice_id.sale_fiscal_type == "special":
                res.update({"fiscal_type": "special", "fiscal_type_name": "FACTURA PARA REGIMENES ESPECIALES", "origin": False})

        return res

    @api.model
    def _order_fields(self, ui_order):
        fields_return = super(PosOrder, self)._order_fields(ui_order)
        fields_return.update({
            'is_return_order': ui_order.get('is_return_order') or False,
            'return_order_id': ui_order.get('return_order_id') or False,
            'return_status': ui_order.get('return_status') or False,
            'note': ui_order.get('order_note', '')
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
                        raise exceptions.UserError(_(
                            u"No se encontró ninguna declaración de efectivo para esta sesión. No se puede registrar el efectivo devuelto."))
                cash_journal_id = cash_journal[0].id
            order.add_payment({
                'amount': -pos_order['amount_return'],
                'payment_date': fields.Datetime.now(),
                'payment_name': _('return'),
                'journal': cash_journal_id,
            })
        return order

    @api.multi
    def action_pos_order_invoice(self):
        for rec in self:
            if not rec.partner_id:
                rec.partner_id = rec.config_id.default_partner_id.id
        return super(PosOrder, self).action_pos_order_invoice()

    # def _reconcile_payments(self):
    #
    #     for order in self:
    #         aml = order.account_move.line_ids
    #         for line in order.statement_ids.mapped('journal_entry_ids'):
    #             aml |= line.line_ids
    #             # aml = aml.filtered(lambda r: not r.reconciled and r.account_id.internal_type == 'receivable' and r.partner_id == self.partner_id)
    #         aml = aml.filtered(lambda r: not r.reconciled and r.account_id.internal_type == 'receivable')
    #
    #         try:
    #             aml.reconcile()
    #         except:
    #             # There might be unexpected situations where the automatic reconciliation won't
    #             # work. We don't want the user to be blocked because of this, since the automatic
    #             # reconciliation is introduced for convenience, not for mandatory accounting
    #             # reasons.
    #
    #             continue

    def pos_picking_generate_cron(self, limit=20):

        orders_list_for_picking = []
        orders_count = self.search_count([('picking_id', '=', False), ('state', '=', 'invoiced'),('is_service_order','=',False)])
        orders = self.search([('picking_id', '=', False), ('state', '=', 'invoiced'),('is_service_order','=',False)], limit=limit)
        _logger.info("========== INICIO del cron para generarcion de los conduces del POS, conduces pendientes {} ==========".format(orders_count))
        for order in orders:
            is_not_service_order = [line for line in order.lines if line.product_id.product_tmpl_id.type != "service"]
            if is_not_service_order:
                orders_list_for_picking.append(order.id)
            else:
                order.is_service_order = True

        orders = self.browse(orders_list_for_picking)

        for order in orders:
            _logger.info("************ Procesando POS ORDER {} ************").format(order.id)
            order.create_picking()
        _logger.info("========== FIN del cron para generarcion de los conduces del POS ==========")

        return True





    @api.model
    def order_search_from_ui(self, input_txt):
        invoice_ids = self.env["account.invoice"].search([('number','like',"%{}%".format(input_txt))], limit=100)
        print invoice_ids
        print invoice_ids.ids
        order_ids = self.search([('invoice_id','in',invoice_ids.ids)])
        print order_ids

        order_list = []
        order_lines_list = []
        for order in order_ids:
            order_json = {
                "amount_total": order.amount_total,
                "date_order": order.date_order,
                "id": order.id,
                "invoice_id": [order.invoice_id.id,order.invoice_id.number],
                "is_return_order": order.is_return_order,
                "name": order.name,
                "pos_reference": order.pos_reference,
                "return_order_id": order.return_order_id.id,
                "return_status": order.return_status,
                "partner_id": [order.partner_id.id, order.partner_id.name],
                "lines": [line.id for line in order.lines],
                "statement_ids": [statement_id.id for statement_id in order.statement_ids],
            }
            order_list.append(order_json)
            for line in order.lines:
                order_lines_json = {
                    "discount": line.discount,
                    "id": line.id,
                    "line_qty_returned": line.line_qty_returned,
                    "price_subtotal": line.price_subtotal,
                    "price_subtotal_incl": line.price_subtotal_incl,
                    "qty": line.qty,
                    "price_unit": line.price_unit,
                    "order_id": [order.id, order.name],
                    "product_id": [line.product_id.id, line.product_id.name],
                }
                order_lines_list.append(order_lines_json)
        return {"wk_order": order_list, "wk_order_lines": order_lines_list}





class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    line_qty_returned = fields.Integer(u'Línea devuelta', default=0)
    original_line_id = fields.Many2one('pos.order.line', u"Línea original")
    order_line_note = fields.Text('Extra Comments')

    @api.model
    def _order_line_fields(self, line):
        fields_return = super(PosOrderLine, self)._order_line_fields(line)
        fields_return[2].update({'line_qty_returned': line[2].get('line_qty_returned', '')})
        fields_return[2].update({'original_line_id': line[2].get('original_line_id', '')})
        fields_return[2].update({'order_line_note': line[2].get('order_line_note', '')})
        return fields_return
