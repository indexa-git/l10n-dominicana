# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_return_order = fields.Boolean(string='Devolver Orden', copy=False)
    return_order_id = fields.Many2one('pos.order', 'Devolver Orden de', readonly=True, copy=False)
    return_status = fields.Selection([('-', 'No Devuelta'), ('Fully-Returned', 'Totalmente Devuelta'),
                                      ('Partially-Returned', 'Parcialmente Devuelta'),
                                      ('Non-Returnable', 'No Retornable')], default='-', copy=False,
                                     string=u'Estatus de Devolución')
    ncf = fields.Char("NCF")
    state = fields.Selection(selection_add=[('is_return_order', 'Nota de crédito')])
    refund_payment_account_move_line_ids = fields.Many2many("account.move.line")
    ncf_invoice_related = fields.Char(related="invoice_id.number", string="NCF")
    sale_fiscal_type = fields.Selection(related="invoice_id.sale_fiscal_type", string="Tipo", readonly=1)

    def check_refund_order_from_ui(self, orders):
        """
        set negative values if order is refund
        :param order:
        :return:
        """

        for order in orders:
            if order.get("data", {}).get("is_return_order", False):
                order["data"]["amount_paid"] = abs(order["data"]["amount_paid"]) * -1
                order["data"]["amount_tax"] = abs(order["data"]["amount_tax"]) * -1
                order["data"]["amount_total"] = abs(order["data"]["amount_total"]) * -1
                order["data"]["amount_paid"] = order["data"]["amount_return"] = 0

                for line in order["data"]["lines"]:
                    line_dict = line[2]
                    line_dict["qty"] = abs(line_dict["qty"]) * -1
                    original_line = self.env['pos.order.line'].browse(line_dict["original_line_id"])
                    original_line.line_qty_returned += abs(line_dict.get('qty', 0))

                order["data"]["statement_ids"] = []
        return orders

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a pos order.
        """
        inv = super(PosOrder, self)._prepare_invoice()
        if self.ncf:
            inv.update({
                'move_name': self.ncf,
                'income_type': '01'
            })
        return inv

    def test_paid(self):
        """A Point of Sale is paid when the sum
        @return: True
        """
        for order in self:
            if order.is_return_order:
                return True
            else:
                super(PosOrder, self).test_paid()

    @api.model
    def create_from_ui(self, orders):
        orders = self.check_refund_order_from_ui(orders)
        res = super(PosOrder, self).create_from_ui(orders)
        return res

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({
            'is_return_order': ui_order.get('is_return_order') or False,
            'return_order_id': ui_order.get('return_order_id') or False,
            'return_status': ui_order.get('return_status') or False,
            'ncf': ui_order['ncf']
        })
        return res

    @api.model
    def order_search_from_ui(self, input_txt):

        invoice_ids = self.env["account.invoice"].search([('number', 'ilike', "%{}%".format(input_txt)),
                                                          ('type', '=', 'out_invoice')], limit=100)
        order_ids = self.search([('invoice_id', 'in', invoice_ids.ids)])
        order_list = []
        order_lines_list = []
        for order in order_ids:
            order_json = {
                "id": order.id,
                "name": order.name,
                "date_order": order.date_order,
                "partner_id": [order.partner_id.id, order.partner_id.name],
                "pos_reference": order.pos_reference,
                "invoice_id": [order.invoice_id.id, order.invoice_id.number],
                "amount_total": order.amount_total,
                "number": order.invoice_id.number,
                "lines": [line.id for line in order.lines],
                "statement_ids": [statement_id.id for statement_id in order.statement_ids],
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
            # order_json["lines"] = order_lines_list
            order_list.append(order_json)
        return {
            "orders": order_list,
            "orderlines": order_lines_list
        }

    @api.model
    def credit_note_info_from_ui(self, ncf):
        invoice_ids = self.env["account.invoice"].search([('number', '=', ncf), ('type', '=', 'out_refund')])
        return {"id": invoice_ids.id, "residual": invoice_ids.residual}

    @api.model
    def get_next_ncf(self, sale_fiscal_type, invoice_journal_id, is_return_order):
        journal_id = self.env["account.journal"].browse(invoice_journal_id)
        if not is_return_order and journal_id:
            return journal_id.sequence_id.with_context(ir_sequence_date=fields.Date.today(),
                                                       sale_fiscal_type=sale_fiscal_type).next_by_id()
        elif is_return_order and journal_id:
            return journal_id.sequence_id.with_context(ir_sequence_date=fields.Date.today(),
                                                       sale_fiscal_type="credit_note").next_by_id()
        else:
            raise ValidationError(_("You have not specified a sales journal"))

    @api.multi
    def action_pos_order_invoice(self):
        res = super(PosOrder, self).action_pos_order_invoice()
        for order in self:
            if order.is_return_order:
                order.sudo().write({'state': 'is_return_order'})
        return res

    def add_payment(self, data):
        statement_id = data.get("statement_id", False)
        if statement_id != 10001:
            return super(PosOrder, self).add_payment(data)
        else:
            payment_name = data.get("payment_name", False)
            if payment_name:
                out_refund_invoice = self.env["account.invoice"].sudo().search([('number', '=', payment_name)])
                if out_refund_invoice:
                    move_line_ids = out_refund_invoice.move_id.line_ids
                    move_line_ids = move_line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type == 'receivable' and r.partner_id == self.partner_id.commercial_partner_id)
                    for move_line_id in move_line_ids:
                        self.write({"refund_payment_account_move_line_ids": [(4, move_line_id.id, _)]})


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    line_qty_returned = fields.Integer(u'Línea Devuelta', default=0)
    original_line_id = fields.Many2one('pos.order.line', u"Línea Original")

    @api.model
    def _order_line_fields(self, line, session_id=None):
        fields_return = super(PosOrderLine, self)._order_line_fields(line, session_id)

        fields_return[2].update({'line_qty_returned': line[2].get('line_qty_returned', ''),
                                 'original_line_id': line[2].get('original_line_id', '')})

        return fields_return
