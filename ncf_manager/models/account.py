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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    purchase_type = fields.Selection(
        [("normal", "Requiere NCF"),
         ("minor", "Gasto Menor. NCF Generado por el Sistema"),
         ("informal", "Proveedores Informales. NCF Generado por el Sistema"),
         ("exterior", "Pagos al Exterior. NCF Generado por el Sistema"),
         ("import", "Importaciones. NCF Generado por el Sistema"),
         ("others", "Otros. No requiere NCF")],
        string="Tipo de Compra", default="others")

    ncf_remote_validation = fields.Boolean("Validar con DGII", default=False)

    ncf_control = fields.Boolean(related="sequence_id.ncf_control")
    prefix = fields.Char(related="sequence_id.prefix")
    date_range_ids = fields.One2many(related="sequence_id.date_range_ids")

    @api.onchange("ncf_control")
    def onchange_ncf_control(self):

        if self.ncf_control and len(self.sequence_id.date_range_ids) <= 1:
            year = fields.Date.from_string(fields.Date.today()).strftime('%Y')
            date_from = '{}-01-01'.format(year)
            date_to = '{}-12-31'.format(year)

            # this method read Selection values from res.partner sale_fiscal_type fields
            selection = self.env["res.partner"]._fields['sale_fiscal_type'].selection
            for sale_fiscal_type in selection:
                print(sale_fiscal_type)
                self.sequence_id.date_range_ids.sudo().create({
                    'date_from': date_from,
                    'date_to': date_to,
                    'sale_fiscal_type': sale_fiscal_type[0],
                    'sequence_id': self.sequence_id.id,
                })


class AccountTax(models.Model):
    _inherit = 'account.tax'

    purchase_tax_type = fields.Selection(
        [('itbis', 'ITBIS Pagado'),
         ('ritbis', 'ITBIS Retenido'),
         ('isr', 'ISR Retenido'),
         ('rext', 'Remesas al Exterior (Ley  253-12)'),
         ('none', 'No Deducible')],
        default="none", string="Tipo de Impuesto de Compra"
    )
