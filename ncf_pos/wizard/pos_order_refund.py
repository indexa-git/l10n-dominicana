# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class PosOrderRefund(models.TransientModel):
    _name = "pos.order.refund"

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
            raise exceptions.UserError("No devolver una orden negativa!")

        qty_allow_refund = sum([l.qty_allow_refund for l in order.lines])
        if qty_allow_refund == 0:
            raise exceptions.UserError(_('Esta factura ya fue devuelta!'))

        if self.env.user.allow_refund and self.env.user.pos_security_pin == self.pos_security_pin:
            refund = True

        if refund:
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

            order.state = "wating_refund_money"
            context.update({"nc": "refund_money"})
            if can_refund_cash:
                res = {
                    'name': _('Payment'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.make.payment',
                    'view_id': False,
                    'target': 'new',
                    'views': False,
                    'type': 'ir.actions.act_window',
                    'context': context,
                }

                return res
            else:
                raise exceptions.UserError("Usted no tiene permitido devolver dinero.")
