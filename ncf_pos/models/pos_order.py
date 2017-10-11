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
                        "origin_invoice_ids": [(4, self.return_order_id.invoice_id.id, _)],
                        "origin": self.return_order_id.move_name
                        })
        res.update({"move_name": self.move_name})
        if self.fiscal_nif:
            res.update({"fiscal_nif": self.fiscal_nif})

        res.update({'shop_id':self.config_id.shop_id})

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

            order_id.action_pos_order_invoice()
            res.update({"id": order_id.id,
                        "rnc": order_id.partner_id.vat,
                        "name": order_id.partner_id.name,
                        "ncf": order_id.invoice_id.number,
                        "fiscal_type": order_id.partner_id.sale_fiscal_type,
                        "origin": False
                        })
            order_id.move_name = order_id.invoice_id.number

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
            else:
                fiscal_type_names = {
                    'fiscal': "FACTURA CON VALOR FISCAL",
                    'final': "FACTURA PARA CONSUMIDOR FINAL",
                    'gov': "FACTURA GUBERNAMENTAL",
                    'special': u"FACTURA PARA REGÍMENES ESPECIALES",
                }
                res.update({"fiscal_type_name": fiscal_type_names.get(order_id.partner_id.sale_fiscal_type)})

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
