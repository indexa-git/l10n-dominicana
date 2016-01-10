# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013-2015 Marcos Organizador de Negocios SRL http://marcos.do
#    Write by Eneldo Serrata (eneldo@marcos.do)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields
from openerp.tools.translate import _
from openerp import netsvc, tools
import time

class pos_manager(models.Model):
    _name = "pos.manager"

    name = fields.Char('Name', size=124)
    max_disc = fields.Float('Maximo descuento en (%)', default=0)
    change_price = fields.Boolean("Puede cambiar el precio", default=False)
    refund = fields.Boolean("Puede hacer devoluciones", default=False)
    cash_refund = fields.Boolean("Puede devolver dinero de la caja", default=False)
    can_cancel = fields.Boolean("Pueden cancelar ordenes nuevas")
    users = fields.Many2many('res.users', 'pos_discount_users', 'discount_id', 'user_id', string='Add Users')


