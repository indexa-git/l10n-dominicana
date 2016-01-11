# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class PosOrderRefund(models.TransientModel):
    _name = "pos.order.refund"

    manager = fields.Char("Clave", required=True)

    @api.multi
    def can_refund(self):
        refund = False
        current_session_id = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self._uid)])
        if not current_session_id:
            raise exceptions.UserError(_('To return product(s), you need to open a session that will be used to register the refund.'))

        order_lines = self.env["pos.order.line"].search([('order_id','=',self._context["active_id"])])
        qty_allow_refund = sum([l.qty_allow_refund for l in order_lines])
        if qty_allow_refund == 0:
            raise exceptions.UserError(_('Esta factura ya fue devuelta!'))

        managers_config = self.env["pos.manager"].search([('users','=',self._uid)])
        for rec in managers_config:
            if rec.can_cancel and self.env.user.pos_security_pin == self.manager:
                refund = True
                break

        if refund:

            return self.env["pos.order"].browse(self._context["active_id"]).refund()
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
        return [('id','in',domain_ids)]

    def _default_amount(self):
        active_id =  self._context.get("active_id",False)
        if active_id:
            order = self.env["pos.order"].browse(active_id)
            return order.amount_total - order.amount_paid
        return False

    refund_money = fields.Boolean("Devolver dinero o reversar pago", default=False)
    journal_id = fields.Many2one("account.journal", string="Formas de pago", default=_default_journal, domain=_get_payment_domain)
    amount = fields.Float('Monto', digits=(16, 2), default=_default_amount)
    payment_name = fields.Char('Referencias')
    manager_pwd = fields.Char("Clave del supervisor")

    @api.model
    def create_refund_invoice(self):
        context = dict(self._context)
        order = self.env["pos.order"].browse(self._context["active_id"])
        invoice_id = order.origin.invoice_id.id
        context.update({'type': 'out_invoice',
                        'active_id': invoice_id,
                        'active_ids': [invoice_id],
                        'search_disable_custom_filters': True,
                        'journal_type': 'sale',
                        'active_model': 'account.invoice',
                        "default_description": order.origin.invoice_id.name
                        })

        refund_inovice = self.env["account.invoice.refund"].with_context(context).create({})
        refund = refund_inovice.invoice_refund()
        refund_invoice_id = self.env["account.invoice"].browse(max(refund["domain"][1][2]))
        refund_invoice_id.write({"invoice_line_ids": [(5, False, False)]})
        inv_line_ref = self.env['account.invoice.line']
        for line in order.lines:
            inv_line = {
                'invoice_id': refund_invoice_id.id,
                'product_id': line.product_id.id,
                'quantity': line.qty*-1,
                'qty_allow_refund': line.qty_allow_refund,
                'account_analytic_id': order._prepare_analytic_account(line),
            }

            invoice_line = inv_line_ref.new(inv_line)
            invoice_line._onchange_product_id()
            invoice_line.invoice_line_tax_ids = [tax.id for tax in invoice_line.invoice_line_tax_ids if
                                                 tax.company_id.id == self.env.user.company_id.id]
            fiscal_position_id = line.order_id.fiscal_position_id
            if fiscal_position_id:
                invoice_line.invoice_line_tax_ids = fiscal_position_id.map_tax(invoice_line.invoice_line_tax_ids)
            invoice_line.invoice_line_tax_ids = [tax.id for tax in invoice_line.invoice_line_tax_ids]
            inv_line = invoice_line._convert_to_write(invoice_line._cache)
            inv_line.update(price_unit=line.price_unit, discount=line.discount)
            inv_line_ref.create(inv_line)


        refund_invoice_id.compute_taxes()
        refund_invoice_id.signal_workflow("invoice_open")

        order.invoice_id = refund_invoice_id.id
        order.create_picking()
        order.state = "refund"
        for line in order.lines:
            self.env["pos.order.line"].browse(line.refund_line_ref.id).write({"qty_allow_refund": line.qty_allow_refund-(line.qty*-1)})



    @api.multi
    def apply_credit_note(self):
        if not self.refund_money:
            context = dict(self._context)
            context.update({"nc": "no_money"})
            self.with_context(context).create_refund_invoice()

            return {'type': 'ir.actions.act_window_close'}
        else:
            pass




