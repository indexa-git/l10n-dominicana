# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

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
                        "origin": self.return_order_id.move_name}
                       )
        res.update({"move_name": self.move_name})
        if self.fiscal_nif:
            res.update({"fiscal_nif": self.fiscal_nif})

        res.update({'shop_id': self.config_id.shop_id})

        return res

    @api.model
    def get_fiscal_data(self, name):
        res = {"fiscal_type": "none", "fiscal_type_name": "FACTURA"}

        order_id = False
        timeout = time.time() + 5  # 5 seconds from now
        while not order_id:
            time.sleep(1)
            if time.time() > timeout:
                break
            self._cr.commit()
            order_id = self.search([('pos_reference', '=', name)])

        if order_id:
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
                res.update({"fiscal_type_name": fiscal_type_names.get(
                    order_id.partner_id.sale_fiscal_type)})

            return res
        else:
            return False

    @api.multi
    def action_pos_order_paid(self):
        if not self.test_paid() and not self.is_return_order:
            raise UserError(_("Order is not paid."))
        self.write({'state': 'paid'})
        return self.create_picking()
