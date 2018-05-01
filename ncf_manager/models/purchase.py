# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>
# © 2017-2018 Neotecnology Cyber City SRL. (http://neotec.do/)
#             Yasmany Castillo <yasmany003@gmail.com>

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
from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        if self.partner_id:
            result = self.env['res.partner'].validate_rnc_cedula(
                self.partner_id.name)
            if result:
                self.partner_id.write({
                    'name': result.get('name'),
                    'vat': result.get('vat'),
                    'is_company': result.get('is_company', False),
                    'sale_fiscal_type': result.get('sale_fiscal_type'),
                })
                self.partner_id.id = self.partner_id.id
        res = super(PurchaseOrder, self).onchange_partner_id()
        return res
