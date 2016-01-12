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
        credit = 0.0

        sql = """
        SELECT   "pos_order"."id",
         "account_invoice"."date_invoice",
         "account_invoice"."number",
         "account_invoice"."residual",
         "account_invoice"."type"
        FROM     "account_invoice"
                  INNER JOIN "pos_order"  ON "account_invoice"."partner_id" = "pos_order"."partner_id"
        WHERE    ( "residual" > 0.00 ) AND ( "account_invoice"."type" = 'out_refund' ) AND ("pos_order"."id" = %(active_id)s)
        """
        self.env.cr.execute(sql, dict(active_id=self._context.get("active_id")))
        res = self.env.cr.fetchall()

        if res:
            credit = sum([r[3] for r in res])
        return credit

    def _default_amount(self):
        order_obj = self.env['pos.order']
        active_id = self._context and self._context.get('active_id', False)
        if active_id:
            order = order_obj.browse(active_id)
            return order.amount_total - order.amount_paid - self._get_credit()
        return False

    journal_id = fields.Many2one("account.journal", string="Formas de pago", default=_default_journal,
                                 domain=_get_payment_domain)
    credit = fields.Float(string=u"Crédito disponible", readonly=True, digits=(16, 2), default=_get_credit)
    amount = fields.Float('Amount', digits=(16, 2), required=True, default=_default_amount)

    @api.multi
    def check(self):

        context = self._context or {}
        order_obj = self.env['pos.order']
        active_id = context and context.get('active_id', False)

        order = order_obj.browse(active_id)

        if self.credit >= self.amount:
            credit = order.amount_total
        else:
            credit = self.credit

        if credit:
            order.credit = credit

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

