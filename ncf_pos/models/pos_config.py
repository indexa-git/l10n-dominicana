# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2017 Raúl Ovalle <rovalle@guavana.com>
# © 2018 Jorge Hernández <jhernandez@gruponeotec.com>
# © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>

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
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

from odoo import models, fields, api, exceptions, _


class PosConfig(models.Model):
    _inherit = "pos.config"

    default_partner_id = fields.Many2one("res.partner",
                                         help=u"Este cliente se usará por defecto como cliente de consumo para las facturas de consumo o final en el POS")
    print_pdf = fields.Boolean("Imprimir PDF", default=False)
    order_loading_options = fields.Selection(
        [("current_session", u"Cargar Órdenes de la Sesión actual"),
         ("n_days", u"Cargar Órdenes de los Últimos 'n' Días")],
        default='current_session', string="Opciones de Carga")
    number_of_days = fields.Integer(
        string=u'Cantidad de Días Anteriores', default=10)
    order_search_criteria = fields.Many2many('pos.search_criteria', string=u"Criterios de Búsqueda")
    ncf_control = fields.Boolean(related="invoice_journal_id.ncf_control")
    seller_and_cashier_ticket = fields.Boolean("Seller and Cashier on Ticket")

    @api.onchange("module_account")
    def onchange_module_account(self):
        default_partner = self.env.ref("ncf_pos.default_partner_on_pos", raise_if_not_found=False)
        if self.module_account and default_partner:
            self.default_partner_id = default_partner.id
        else:
            self.default_partner_id = False

    @api.constrains('number_of_days')
    def number_of_days_validation(self):
        if self.order_loading_options == 'n_days' and (not self.number_of_days or self.number_of_days < 0):
            raise exceptions.ValidationError(_(
                u"Favor proveer un valor válido para el campo 'Cantidad de Días Anteriores'!!!"))
