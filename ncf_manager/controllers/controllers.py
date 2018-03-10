# -*- coding: utf-8 -*-
from odoo import http
import json
import requests
import re
# from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except(ImportError, IOError) as err:
    _logger.debug(err)


class Odoojs(http.Controller):
    @http.route('/dgii_ws', auth='public')
    def index(self, **kwargs):
        """
        Look for clients in the web service of the DGII
            :param self: 
            :param **kwargs dict :the parameters received
            :param term string : the character of the client or his rnc /
        """
        term = kwargs.get("term", False)
        if term:
            if term.isdigit() and len(term) in [9, 11]:
                result = rnc.check_dgii(term)
            else:
                result = rnc.search_dgii(term, end_at=20, start_at=1)
            if not result is None:
                if not isinstance(result, list):
                    result = [result]

                for d in result:
                    d["name"] = " ".join(
                        re.split("\s+", d["name"], flags=re.UNICODE))  # remove all duplicate white space from the name
                    d["label"] = "{} - {}".format(d["rnc"], d["name"])
                return json.dumps(result)

    @http.route('/orders_ws', auth='public')
    def orders_ws(self, **kwargs):

        """
        Look for pos orders
            :param self:
            :param **kwargs dict :the parameters received
            :param query string : the order ids /
        """
        query = kwargs.get("query", False)
        if query:
            order_objs = http.request.env['pos.order'].search([('id', 'like', query)], limit=20)
            result = {}
            order_list = []
            order_line_list = []

            for order in order_objs:
                vals = {}
                vals['id'] = order.id
                vals['name'] = order.name
                vals['date_order'] = order.date_order
                vals['pos_reference'] = order.pos_reference
                vals['partner_id'] = [order.partner_id.id, order.partner_id.name] if order.partner_id else False
                vals['invoice_id'] = order.invoice_id.id if order.invoice_id else False
                vals['lines'] = []

                for line in order.lines:
                    vals['lines'].append(line.id)
                    line_vals = {}
                    line_vals['id'] = line.id  # line.original_line_id.id
                    # line_vals['line_qty_returned'] = line.original_line_id.line_qty_returned
                    line_vals['existing'] = True
                    order_line_list.append(line_vals)

                order_list.append(vals)

            result['orders'] = order_list
            result['orderlines'] = order_line_list
            print(order_list)
            return json.dumps(result)

    @http.route('/invoices_ws', auth='public')
    def invoices_ws(self, **kwargs):
        """
        Look for pos invoices
            :param self:
            :param **kwargs dict :the parameters received
            :param query string : the invoice ids /
        """
        query = kwargs.get("query", False)
        if query:
            invoice_ids = http.request.env["account.invoice"].search([('number', 'ilike', "%{}%".format(query))],
                                                                     limit=20)
            # order_ids = http.request.search([('invoice_id', 'in', invoice_ids.ids)])

            result = {}
            result['invoices'] = invoice_ids
            # result['orders'] = order_ids
            print(result)
            return result
            # return json.dumps(result)

