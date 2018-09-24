# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>
# © 2017-2018 Neotec SRL. (https://neotec.do/)
#             Yasmany Castillo <yasmany003@gmail.com>


# This file is part of NCF Manager.

# NCF Sale is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Sale is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Sale.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

from odoo import models, fields, api, _


class AccountNcfRegistry(models.Model):
    _name = "account.ncf.registry"
    _description = "NCF Sequences Manager"

    name = fields.Char(string="Name", readonly=True)
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Entry Sequence',
        required=True,
        copy=False)
    company_id = fields.Many2one(related="sequence_id.company_id")
    prefix = fields.Char(related="sequence_id.prefix")
    padding = fields.Integer(related="sequence_id.padding")
    # use_date_range = fields.Boolean(related="sequence_id.use_date_range")
    date_range_ids = fields.One2many(related="sequence_id.date_range_ids")
    special_fiscal_position_id = fields.Many2one(
        "account.fiscal.position",
        string=u"Posición fiscal para regímenes especiales.",
        help=u"Define la posición fiscal por defecto para los clientes que tienen definido el tipo de comprobante fiscal regímenes especiales.")
