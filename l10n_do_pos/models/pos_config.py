# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2017 Raúl Ovalle <rovalle@guavana.com>
# © 2018 Jorge Hernández <jhernandez@gruponeotec.com>
# © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
# © 2018 Raul Ovalle <raulovallet@gmail.com>

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

    default_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string=u"Default partner",
    )
    order_loading_options = fields.Selection(
        selection=[
            ("current_session", u"Cargar Órdenes de la Sesión actual"),
            ("n_days", u"Cargar Órdenes de los Últimos 'n' Días")
        ],
        default='current_session',
        string="Opciones de Carga",
    )
    number_of_days = fields.Integer(
        string=u'Cantidad de Días Anteriores',
        default=10,
    )
    l10n_latam_use_documents = fields.Boolean(
        related="invoice_journal_id.l10n_latam_use_documents",
    )
    credit_notes_number_of_days = fields.Integer(
        string=u'Cantidad de Días Anteriores',
        default=10,
    )

    # TODO: search criteria
    # order_search_criteria = fields.Many2many(
    #     comodel_name='pos.search_criteria',
    #     string=u"Criterios de Búsqueda",
    # )

    @api.constrains('number_of_days')
    def number_of_days_validation(self):
        if self.order_loading_options == 'n_days' and (
                not self.number_of_days or self.number_of_days < 0):
            raise exceptions.ValidationError(_(
                u"Favor proveer un valor válido para el campo"
                "'Cantidad de Días Anteriores'!!!"))
