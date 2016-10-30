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
from odoo import models, fields, api, exceptions
from odoo.tools.translate import _


class PosOrderRefund(models.TransientModel):
    _name = "pos.order.refund"

    cancel_refund_info = fields.Many2many("order.info.tags")
    pos_security_pin = fields.Char("Clave", required=True)

    @api.multi
    def can_refund(self):
        refund = False
        current_session_id = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self._uid)])
        if not current_session_id:
            raise exceptions.UserError(
                _('To return product(s), you need to open a session that will be used to register the refund.'))

        order = self.env["pos.order"].browse(self._context["active_id"])

        if order.amount_total < 0:
            raise exceptions.UserError(u"No puede devolver una devolución!")

        if not order.allow_refund():
            raise exceptions.UserError(_('Esta factura ya fue devuelta!'))

        draft_refund = order.search(
            [('origin', '=', order.id), ('state', 'in', ('draft_refund_money', 'draft_refund'))])
        if draft_refund:
            raise exceptions.UserError('Tiene una devolucion en borrador para esta orden.')

        if self.env.user.allow_refund and self.env.user.pos_security_pin == self.pos_security_pin:
            refund = True


        if refund:
            order.cancel_refund_info = [r.id for r in self.cancel_refund_info]
            return order.refund()
        else:
            raise exceptions.UserError("Usted no tiene permitido hacer devoluciones.")


class PosOrderCreditNote(models.TransientModel):
    _name = "pos.order.credit.note"

    def _default_journal(self):
        current_session_id = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self._uid)])

        for journal in current_session_id.journal_ids:
            if journal.type == "cash":
                return journal.id
        return False

    def _get_payment_domain(self):
        current_session_id = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self._uid)])
        domain_ids = [r.id for r in current_session_id.journal_ids]
        return [('id', 'in', domain_ids)]

    def _default_amount(self):
        active_id = self._context.get("active_id", False)
        if active_id:
            order = self.env["pos.order"].browse(active_id)
            return order.amount_total - order.amount_paid
        return False

    refund_money = fields.Boolean("Devolver dinero o reversar pago", default=False)
    journal_id = fields.Many2one("account.journal", string="Formas de pago", default=_default_journal,
                                 domain=_get_payment_domain)
    amount = fields.Float('Monto', digits=(16, 2), default=_default_amount)
    payment_name = fields.Char('Referencias')
    pos_security_pin = fields.Char("Clave del supervisor")

    @api.multi
    def apply_credit_note(self):
        context = dict(self._context)
        context.update({"nc": "no_money"})
        order = self.env["pos.order"].browse(self._context["active_id"])

        if not self.refund_money:
            order.state = "refund"
            order.with_context(context).create_refund_invoice()
            return {'type': 'ir.actions.act_window_close'}
        else:
            can_refund_cash = False

            if self.env.user.allow_cash_refund and self.env.user.pos_security_pin == self.pos_security_pin:
                can_refund_cash = True

            order.state = "draft_refund_money"
            context.update({"nc": "refund_money"})
            if can_refund_cash:
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

                return res
            else:
                raise exceptions.UserError("Usted no tiene permitido devolver dinero.")
