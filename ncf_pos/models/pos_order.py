from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_return_order = fields.Boolean(string='Devolver Orden', copy=False)
    return_order_id = fields.Many2one('pos.order', 'Devolver Orden de', readonly=True, copy=False)
    return_status = fields.Selection([('-', 'No Devuelta'), ('Fully-Returned', 'Totalmente Devuelta'),
                                      ('Partially-Returned', 'Parcialmente Devuelta'),
                                      ('Non-Returnable', 'No Retornable')], default='-', copy=False,
                                     string='Estatus de Devolución')

    @api.model
    def _process_order(self, pos_order):
        res = super(PosOrder, self)._process_order(pos_order)
        if res.is_return_order:
            res.amount_paid = 0
            for line in res.lines:
                line.qty = abs(line.qty)
                line.line_qty_returned += line.qty
            for statement in res.statement_ids:
                statement.amount = abs(statement.amount)

            res.amount_tax = abs(res.amount_tax)
            res.amount_return = 0
            res.amount_total = abs(res.amount_total)

        return res

    @api.model
    def _order_fields(self, ui_order):
        fields_return = super(PosOrder, self)._order_fields(ui_order)
        fields_return.update({
            'is_return_order': ui_order.get('is_return_order') or False,
            'return_order_id': ui_order.get('return_order_id') or False,
            'return_status': ui_order.get('return_status') or False,
        })
        return fields_return

    def _action_create_invoice_line(self, line=False, invoice_id=False):
        res = super(PosOrder, self)._action_create_invoice_line(line, invoice_id)
        if self.is_return_order:
            res.quantity = abs(line.qty)

        return res

    @api.model
    def order_search_from_ui(self, input_txt):

        invoice_ids = self.env["account.invoice"].search([('number', 'ilike', "%{}%".format(input_txt))], limit=100)
        order_ids = self.search([('invoice_id', 'in', invoice_ids.ids)])
        order_list = []
        for order in order_ids:
            order_json = {
                "amount_total": order.amount_total,
                "date_order": order.date_order,
                "id": order.id,
                "invoice_id": [order.invoice_id.id, order.invoice_id.number],
                "number": order.invoice_id.number,
                "name": order.name,
                "pos_reference": order.pos_reference,
                "partner_id": [order.partner_id.id, order.partner_id.name],
                "lines": [line.id for line in order.lines],
                "statement_ids": [statement_id.id for statement_id in order.statement_ids],
            }
            order_lines_list = []
            for line in order.lines:
                order_lines_json = {
                    "discount": line.discount,
                    "id": line.id,
                    "price_subtotal": line.price_subtotal,
                    "price_subtotal_incl": line.price_subtotal_incl,
                    "qty": line.qty,
                    "price_unit": line.price_unit,
                    "order_id": [order.id, order.name],
                    "product_id": [line.product_id.id, line.product_id.name],
                }
                order_lines_list.append(order_lines_json)
            order_json["lines"] = order_lines_list
            order_list.append(order_json)
        return {"orders": order_list}


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    line_qty_returned = fields.Integer('Línea Devuelta', default=0)
    original_line_id = fields.Many2one('pos.order.line', "Línea Original")

    @api.model
    def _order_line_fields(self, line, session_id=None):
        fields_return = super(PosOrderLine, self)._order_line_fields(line, session_id)

        fields_return[2].update({'line_qty_returned': line[2].get('line_qty_returned', ''),
                                 'original_line_id': line[2].get('original_line_id', '')})

        return fields_return
