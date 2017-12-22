# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd.
#    (<https://webkul.com/>)
#
##########################################################################
from odoo.tools.translate import _
import logging
from odoo.tools import float_is_zero
from odoo import api, fields, models
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    not_returnable = fields.Boolean('No Retornable')


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_return_order = fields.Boolean(string='Devolver Orden', copy=False)
    return_order_id = fields.Many2one(
        'pos.order', 'Devolver Orden de', readonly=True, copy=False)
    return_status = fields.Selection(
        [('-', 'No Devuelta'),
         ('Fully-Returned', 'Totalmente Devuelta'),
         ('Partially-Returned', 'Parcialmente Devuelta'),
         ('Non-Returnable', 'No Retornable')],
        default='-', copy=False, string=u'Estatus de Devolución')

    @api.model
    def _process_order(self, pos_order):
        prec_acc = self.env['decimal.precision'].precision_get('Account')
        pos_session = self.env['pos.session'].browse(
            pos_order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            pos_order['pos_session_id'] = self._get_valid_session(pos_order).id
        if pos_order.get('is_return_order', False):
            pos_order['amount_paid'] = 0
            for line in pos_order['lines']:
                line_dict = line[2]
                line_dict['qty'] = line_dict['qty'] * -1
                original_line = self.env['pos.order.line'].browse(
                    line_dict.get('original_line_id', False))
                original_line.line_qty_returned += abs(line_dict.get('qty', 0))
            for statement in pos_order['statement_ids']:
                statement_dict = statement[2]
                statement_dict['amount'] = statement_dict['amount'] * -1
            pos_order['amount_tax'] = pos_order['amount_tax'] * -1
            pos_order['amount_return'] = 0
            pos_order['amount_total'] = pos_order['amount_total'] * -1

        order = self.create(self._order_fields(pos_order))
        journal_ids = set()
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'],
                                 precision_digits=prec_acc):
                order.add_payment(self._payment_fields(payments[2]))
            journal_ids.add(payments[2]['journal_id'])

        if pos_session.sequence_number <= pos_order['sequence_number']:
            pos_session.write(
                {'sequence_number': pos_order['sequence_number'] + 1})
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
                    # an amount higher than total amount of the order and gets
                    # cash back
                    cash_journal = [
                        statement.journal_id for statement in pos_session.statement_ids if statement.journal_id.type == 'cash']
                    if not cash_journal:
                        raise UserError(
                            _("No cash statement found for this session. Unable to record returned cash."))
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
        Invoice = self.env['account.invoice']
        for order in self:
            if not order.is_return_order:
                super(PosOrder, order).action_pos_order_invoice()
            else:
                local_context = dict(
                    self.env.context, force_company=order.company_id.id,
                    company_id=order.company_id.id)
                if order.invoice_id:
                    Invoice += order.invoice_id
                    continue

                if not order.partner_id:
                    raise UserError(
                        _('Please provide a partner for the sale.'))

                invoice = Invoice.new(order._prepare_invoice())
                invoice._onchange_partner_id()
                invoice.fiscal_position_id = order.fiscal_position_id

                inv = invoice._convert_to_write(
                    {name: invoice[name] for name in invoice._cache})
                new_invoice = Invoice.with_context(
                    local_context).sudo().create(inv)
                message = _(
                    "This invoice has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
                new_invoice.message_post(body=message)
                order.write(
                    {'invoice_id': new_invoice.id, 'state': 'invoiced'})
                Invoice += new_invoice

                for line in order.lines:
                    line.qty = abs(line.qty)
                    self.with_context(local_context)._action_create_invoice_line(line, new_invoice.id)
                    line.qty = -1 * line.qty

                new_invoice.with_context(local_context).sudo().compute_taxes()
                order.sudo().write({'state': 'invoiced'})

            if not Invoice:
                return {}

            return {
                'name': _('Customer Invoice'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('account.invoice_form').id,
                'res_model': 'account.invoice',
                'context': "{'type':'out_refund'}",
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'res_id': Invoice and Invoice.ids[0] or False,
            }

    @api.model
    def _order_fields(self, ui_order):
        fields_return = super(PosOrder, self)._order_fields(ui_order)
        fields_return.update({
            'is_return_order': ui_order.get('is_return_order') or False,
            'return_order_id': ui_order.get('return_order_id') or False,
            'return_status': ui_order.get('return_status') or False,
        })
        return fields_return


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'
    line_qty_returned = fields.Integer(u'Línea Devuelta', default=0)
    original_line_id = fields.Many2one('pos.order.line', u"Línea Original")

    @api.model
    def _order_line_fields(self, line, session_id=None):
        fields_return = super(
            PosOrderLine, self)._order_line_fields(line, session_id)
        fields_return[2].update(
            {'line_qty_returned': line[2].get('line_qty_returned', '')})
        fields_return[2].update(
            {'original_line_id': line[2].get('original_line_id', '')})
        return fields_return
