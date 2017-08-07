# -*- coding: utf-8 -*-
###############################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL.
#  (<https://marcos.do/>) 
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it,
# unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without
# copying any source code or material from the Software. You may distribute
# those modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the
# Softwar or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

import logging
import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    move_name = fields.Char(size=19)
    fiscal_nif = fields.Char()
    invoice_number = fields.Char(related="invoice_id.number")
    is_service_order = fields.Boolean("Ordenes que no generan picking")

    def _prepare_invoice(self):
        res = super(PosOrder, self)._prepare_invoice()
        if self.is_return_order:
            res.update({"type": "out_refund",
                        "origin_invoice_ids": [(4, self.return_order_id.invoice_id.id, _)]})
        res.update({"move_name": self.move_name})
        if self.fiscal_nif:
            res.update({"fiscal_nif": self.fiscal_nif})

        return res

    @api.model
    def get_fiscal_data(self, name):
        res = {"fiscal_type": "none", "fiscal_type_name": u"PRE-CUENTA"}

        order_id = False
        timeout = time.time() + 60 * 0.5  # 5 minutes from now
        while not order_id:
            time.sleep(1)
            if time.time() > timeout:
                break
            self._cr.commit()
            order_id = self.search([('pos_reference', '=', name)])

        if order_id:
            shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
            res.update({"id": order_id.id,
                        "rnc": order_id.partner_id.vat,
                        "name": order_id.partner_id.name})

            if order_id.is_return_order:
                res.update({"fiscal_type_name": u"NOTA DE CRÉDITO"})

                reference_ncf = order_id.return_order_id.invoice_id.number
                reference_ncf_type = reference_ncf[9:11]

                if reference_ncf_type in ("01", "14"):
                    res.update({"fiscal_type": "fiscal_note"})
                elif reference_ncf_type == "02":
                    res.update({"fiscal_type": "final_note"})
                elif reference_ncf_type == "15":
                    res.update({"fiscal_type": "special_note"})
                res.update({"origin": reference_ncf})
                sequence = shop_user_config.nc_sequence_id

            elif order_id.partner_id.sale_fiscal_type == "fiscal":
                res.update({"fiscal_type": "fiscal",
                            "fiscal_type_name": "FACTURA CON VALOR FISCAL",
                            "origin": False})
                sequence = shop_user_config.fiscal_sequence_id

            elif order_id.partner_id.sale_fiscal_type == "final":
                res.update({"fiscal_type": "final",
                           "fiscal_type_name": "FACTURA PARA CONSUMIDOR FINAL",
                            "origin": False})
                sequence = shop_user_config.final_sequence_id

            elif order_id.partner_id.sale_fiscal_type == "gov":
                res.update({"fiscal_type": "fiscal",
                            "fiscal_type_name": "FACTURA GUBERNAMENTAL",
                            "origin": False})
                sequence = shop_user_config.gov_sequence_id

            elif order_id.partner_id.sale_fiscal_type == "special":
                res.update({"fiscal_type": "special",
                           "fiscal_type_name": u"FACTURA PARA REGÍMENES ESPECIALES",
                            "origin": False})
                sequence = shop_user_config.special_sequence_id
            if sequence:
                order_id.move_name = sequence.with_context(ir_sequence_date=fields.Date.today()).next_by_id()
                res.update({"ncf": order_id.move_name})
            order_id.action_pos_order_invoice()
            return res
        else:
            return False

    @api.multi
    def action_pos_order_invoice(self):
        for pos_order in self:
            if not pos_order.partner_id:
                pos_order.partner_id = pos_order.config_id.default_partner_id.id

        for rec in self:
            if not rec.invoice_id:
                super(PosOrder, rec).action_pos_order_invoice()
                rec.invoice_id.sudo().action_invoice_open()
                rec.account_move = rec.invoice_id.move_id

    @api.multi
    def action_pos_order_paid(self):
        if not self.test_paid() and not self.is_return_order:
            raise UserError(_("Order is not paid."))
        self.write({'state': 'paid'})
        return self.create_picking()

    @api.model
    def order_search_from_ui(self, input_txt):
        invoice_ids = self.env["account.invoice"].search(
                    [('number', 'like', "%{}%".format(input_txt))],
                    limit=100)
        print invoice_ids
        print invoice_ids.ids
        order_ids = self.search([('invoice_id', 'in', invoice_ids.ids)])
        print order_ids

        order_list = []
        order_lines_list = []
        for order in order_ids:
            order_json = {
                "amount_total": order.amount_total,
                "date_order": order.date_order,
                "id": order.id,
                "invoice_id": [order.invoice_id.id, order.invoice_id.number],
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
