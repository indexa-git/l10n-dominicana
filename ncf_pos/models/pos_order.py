from odoo import models, fields, api
class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def order_search_from_ui(self, input_txt):
        
        invoice_ids = self.env["account.invoice"].search([('number', 'ilike', "%{}%".format(input_txt))], limit=100)
        order_ids = self.search([('invoice_id', 'in', invoice_ids.ids)])  
        order_list = []
        order_lines_list = []
        for order in order_ids:
            order_json = {
                "amount_total": order.amount_total,
                "date_order": order.date_order,
                "id": order.id,
                "invoice_id": [order.invoice_id.id, order.invoice_id.number],
                "number": order.invoice_id.number,
                "is_return_order": order.is_return_order,
                "name": order.name,
                "pos_reference": order.pos_reference,
                "return_order_id": order.return_order_id.id,
                "return_status": order.return_status,
                "partner_id": [order.partner_id.id, order.partner_id.name],
                "lines": [line.id for line in order.lines],
                "statement_ids": [statement_id.id for statement_id in order.statement_ids],
            }
            order_list.append(order_json)
            for line in order.lines:
                order_lines_json = {
                    "discount": line.discount,
                    "id": line.id,
                    "line_qty_returned": line.line_qty_returned,
                    "price_subtotal": line.price_subtotal,
                    "price_subtotal_incl": line.price_subtotal_incl,
                    "qty": line.qty,
                    "price_unit": line.price_unit,
                    "order_id": [order.id, order.name],
                    "product_id": [line.product_id.id, line.product_id.name],
                }
                order_lines_list.append(order_lines_json)
        return {"wk_order": order_list, "wk_order_lines": order_lines_list}

