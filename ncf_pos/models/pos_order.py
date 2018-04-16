from odoo import models, fields, api, exceptions, _
from odoo.tools import float_is_zero


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_return_order = fields.Boolean(string='Devolver Orden', copy=False)
    return_order_id = fields.Many2one('pos.order', 'Devolver Orden de', readonly=True, copy=False)
    return_status = fields.Selection([('-', 'No Devuelta'), ('Fully-Returned', 'Totalmente Devuelta'),
                                      ('Partially-Returned', 'Parcialmente Devuelta'),
                                      ('Non-Returnable', 'No Retornable')], default='-', copy=False,
                                     string=u'Estatus de Devolución')
    ncf = fields.Char("NCF")

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

                for line in order["data"]["lines"]:
                    line[2]["qty"] = abs(line[2]["qty"]) * -1

                for statement in order["data"]["statement_ids"]:
                    statement[2]["amount"] = abs(statement[2]["amount"]) * -1

        return orders

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a pos order.
        """
        import pdb; pdb.set_trace()
        inv = super(PosOrder, self)._prepare_invoice()
        if self.ncf:
            inv.update({
                'move_name': self.ncf
            })
        return inv

    @api.model
    def create_from_ui(self, orders):
        orders = self.check_refund_order_from_ui(orders)
        res = super(PosOrder, self).create_from_ui(orders)
        return res

    @api.model
    def _process_order(self, pos_order):

        if pos_order.get('is_return_order', False):
            pos_order['amount_paid'] = 0
            for line in pos_order['lines']:
                line_dict = line[2]
                line_dict['qty'] = abs(line_dict['qty'])
                if line_dict.get('original_line_id', False):
                    original_line = self.env['pos.order.line'].browse(line_dict["original_line_id"])
                    original_line.line_qty_returned += abs(line_dict.get('qty', 0))
            for statement in pos_order['statement_ids']:
                statement_dict = statement[2]
                statement_dict['amount'] = statement_dict['amount'] * -1
            pos_order['amount_tax'] = pos_order['amount_tax'] * -1
            pos_order['amount_return'] = 0
            pos_order['amount_total'] = pos_order['amount_total'] * -1

        return super(PosOrder, self)._process_order(pos_order)

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
    def get_next_ncf(self, sale_fiscal_type, invoice_journal_id, is_return_order):
        journal_id = self.env["account.journal"].browse(invoice_journal_id)
        if not is_return_order and journal_id:
            return journal_id.sequence_id.with_context(ir_sequence_date=fields.Date.today(),
                                                       sale_fiscal_type=sale_fiscal_type).next_by_id()
        elif is_return_order and journal_id:
            return journal_id.sequence_id.with_context(ir_sequence_date=fields.Date.today(),
                                                       sale_fiscal_type="credit_note").next_by_id()
        else:
            raise exceptions.ValidationError(_("You have not specified a sales journal"))


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
