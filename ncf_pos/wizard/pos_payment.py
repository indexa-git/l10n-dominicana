# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
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

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def _default_journal(self):
        current_session_id = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self._uid)])

        for journal in current_session_id.journal_ids:
            if journal.type == "cash":
                return journal.id

    def _get_payment_domain(self):
        current_session_id = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self._uid)])
        domain_ids = [r.id for r in current_session_id.journal_ids]
        return [('id', 'in', domain_ids)]

    def get_credit(self, order):
        res = order._get_partner_unreconcile("<")
        credit = sum([r[1] for r in res]) * -1 or 0.0
        amount_payment = order.amount_total - order.amount_paid
        if amount_payment > 0 and amount_payment < credit:
            credit = amount_payment
        return credit

    def _default_credit(self):
        order_obj = self.env['pos.order']
        active_id = self._context and self._context.get('active_id', False)
        credit = 0.0
        if active_id:
            order = order_obj.browse(active_id)
            if not order.credit:
                open_order = order_obj.search([("session_id", "=", order.session_id.id), ("state", "=", "draft"),
                                               ("partner_id", "=", order.partner_id.id), ("credit", ">", 0)])
                if open_order:
                    raise exceptions.UserError(
                        "Ya ha iniciado un proceso de pago con nota de crédito que aun esta sin terminar!")

            credit = self.get_credit(order)

        return credit

    def _default_amount(self):
        order_obj = self.env['pos.order']
        active_id = self._context and self._context.get('active_id', False)
        if active_id:
            order = order_obj.browse(active_id)
            credit = self.get_credit(order)

            return order.amount_total - order.amount_paid - credit + order.credit
        return False

    journal_id = fields.Many2one("account.journal", string="Formas de pago", default=_default_journal,
                                 domain=_get_payment_domain)
    journal_type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase'), ('cash', 'Cash'), ('bank', 'Bank'),
                                     ('general', 'Miscellaneous')], related="journal_id.type", store=False)
    credit = fields.Float(string=u"Crédito", readonly=True, digits=(16, 2), default=_default_credit)
    amount = fields.Float('Amount', digits=(16, 2), required=True, default=_default_amount)

    @api.multi
    def check(self):

        context = dict(self._context) or {}
        order_obj = self.env['pos.order']
        active_id = context and context.get('active_id', False)

        order = order_obj.browse(active_id)

        credit_amount = 0.0
        if order.credit == 0:
            credit_amount = self.credit

        credit = 0.0
        if order.amount_total < 0:
            pass
        elif credit_amount >= order.amount_total:
            credit = order.amount_total
            order.credit_type = "full"
        elif credit_amount < order.amount_total:
            credit = credit_amount
            order.credit_type = "parcial"

        if credit:
            order.credit = credit

        order.refresh()
        amount = order.amount_total - order.amount_paid

        data = self.read()[0]
        data['journal'] = data['journal_id'][0]

        if amount != 0.0:
            order.add_payment(data)

        if order.test_paid():
            order.signal_workflow('paid')
            return {'type': 'ir.actions.act_window_close'}

        return self.launch_payment()

    def launch_payment(self):
        if self.state != "draft_refund_money":
            return {
                'name': _('Payment'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.make.payment',
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
                'context': self._context,
            }
        else:
            return {
                'name': "Devolucion de el pago",
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.make.payment.refund',
                'view_id': False,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
                'context': self._context,
            }


class PosMakePaymentRefund(models.TransientModel):
    _name = "pos.make.payment.refund"

    @api.model
    def default_get(self, fields_list):
        order_obj = self.env["pos.order"]
        order = order_obj.browse(self._context.get("active_id"))
        origin_order_id = order.origin

        old_refund = order_obj.search([('origin', '=', origin_order_id.id), ('state', '=', 'refund_money')])

        payment_in = {}

        if old_refund:
            for payment in old_refund.statement_ids:
                if not payment_in.get(payment.journal_id.id, False):
                    payment_in[payment.journal_id.id] = payment.amount
                else:
                    payment_in[payment.journal_id.id] += payment.amount

        for payment in origin_order_id.statement_ids:
            if not payment_in.get(payment.journal_id.id, False):
                payment_in[payment.journal_id.id] = payment.amount
            else:
                payment_in[payment.journal_id.id] += payment.amount

        lines = []
        for k, v in payment_in.iteritems():
            line = (0, 0, {"refund_id": self.id, "journal_id": k, "amount": v})
            lines.append(line)

        res = {}
        res["refund_order_id"] = order.id
        res["lines"] = lines
        res["total_refund"] = order.amount_total * -1

        return res

    @api.depends("lines")
    def _calc_refund(self):
        amount = 0
        for line in self.lines:
            amount += line.refund

        self.refunded = self.total_refund - amount

    refund_order_id = fields.Many2one("pos.order", string="Orden")
    lines = fields.One2many("pos.make.payment.refund.line", "refund_id", string="Pagos")
    total_refund = fields.Float(u"Monto de la devolución", readonly=True)
    refunded = fields.Float(u"Monto de la devolución", readonly=True, compute=_calc_refund)

    @api.multi
    def refund_payment(self):
        if self.refunded > self.total_refund:
            return False

        for line in self.lines:
            if line.refund == 0:
                continue
            data = {'amount': line.refund*-1,
                    'payment_date': fields.Datetime.now(),
                    'journal': line.journal_id.id}

            self.refund_order_id.add_payment(data)
        self.refund_order_id.signal_workflow('paid')
        return {'type': 'ir.actions.act_window_close'}


class PosMakePaymentRefundLine(models.TransientModel):
    _name = "pos.make.payment.refund.line"

    refund_id = fields.Many2one("pos.make.payment.refund")
    check = fields.Boolean("Aplicar", default=False)
    journal_id = fields.Many2one("account.journal", string="Forma de pago", readonly=True)
    amount = fields.Float("Monto", readonly=True)
    refund = fields.Float("Devolver")

    @api.onchange("refund")
    def onchange_refund(self):
        if self.refund > self.amount:
            self.refund = 0.0
