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

    name = fields.Char(string="Name")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        required=True,
        default=lambda self: self.env.user.company_id)
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Entry Sequence',
        required=True,
        copy=False)
    sequence = fields.Integer(help='Used to order Journals in the dashboard view', default=10)
