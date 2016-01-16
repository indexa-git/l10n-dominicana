# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api

import time
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

    def _get_credit(self):
        order_obj = self.env['pos.order']
        active_id = self._context and self._context.get('active_id', False)
        if active_id:
            order = order_obj.browse(active_id)
            if order.credit:
                return 0.00

        res = self.env["pos.order"].browse(self._context.get("active_id"))._get_partner_unreconcile("<")
        return sum([r[1] for r in res])*-1 or 0.0

    def _default_amount(self):
        order_obj = self.env['pos.order']
        active_id = self._context and self._context.get('active_id', False)
        if active_id:
            order = order_obj.browse(active_id)
            return order.amount_total - order.amount_paid

        return False

    journal_id = fields.Many2one("account.journal", string="Formas de pago", default=_default_journal,
                                 domain=_get_payment_domain)
    credit = fields.Float(string=u"Crédito disponible", readonly=True, digits=(16, 2), default=_get_credit)
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

