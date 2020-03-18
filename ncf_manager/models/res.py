# © 2016-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Yasmany Castillo <yasmany003@gmail.com>
# © 2018 José López <jlopez@indexa.do>
# © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
# © 2018 Andrés Rodríguez <andres@iterativo.do>

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

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    @api.depends('sale_fiscal_type')
    def _fiscal_info_required(self):
        for rec in self:
            if rec.sale_fiscal_type in ['fiscal', 'gov', 'special']:
                rec.fiscal_info_required = True
            else:
                rec.fiscal_info_required = False

    sale_fiscal_type = fields.Selection([
        ("final", "Consumo"),
        ("fiscal", u"Crédito Fiscal"),
        ("gov", "Gubernamental"),
        ("special", u"Regímenes Especiales"),
        ("unico", u"Único Ingreso"),
        ("export", u"Exportaciones"),
    ],
        string="Tipo de comprobante",
        compute='_compute_sale_fiscal_type',
        inverse='_inverse_sale_fiscal_type',
        index=True,
        store=True,
    )

    sale_fiscal_type_list = [{
        "id": "final",
        "name": "Consumo",
        "ticket_label": "Consumo",
        "is_default": True
    }, {
        "id": "fiscal",
        "name": "Crédito Fiscal"
    }, {
        "id": "gov",
        "name": "Gubernamental"
    }, {
        "id": "special",
        "name": "Regímenes Especiales"
    }, {
        "id": "unico",
        "name": "Único Ingreso"
    }, {
        "id": "export",
        "name": "Exportaciones"
    }]

    sale_fiscal_type_vat = {
        "rnc": ["fiscal", "gov", "special"],
        "ced": ["final", "fiscal"],
        "other": ["final"],
        "no_vat": ["final", "unico", "export"]
    }

    expense_type = fields.Selection(
        [('01', '01 - Gastos de Personal'),
         ('02', '02 - Gastos por Trabajo, Suministros y Servicios'),
         ('03', '03 - Arrendamientos'),
         ('04', '04 - Gastos de Activos Fijos'),
         ('05', u'05 - Gastos de Representación'),
         ('06', '06 - Otras Deducciones Admitidas'),
         ('07', '07 - Gastos Financieros'),
         ('08', '08 - Gastos Extraordinarios'),
         ('09', '09 - Compras y Gastos que forman parte del Costo de Venta'),
         ('10', '10 - Adquisiciones de Activos'),
         ('11', '11 - Gastos de Seguro')],
        string="Tipo de gasto")

    fiscal_info_required = fields.Boolean(compute=_fiscal_info_required)
    country_id = fields.Many2one('res.country',
                                 string='Country',
                                 ondelete='restrict',
                                 default=lambda self: self.env.ref('base.do'))

    @api.depends('vat', 'country_id', 'name')
    def _compute_sale_fiscal_type(self):
        """ Compute the type of partner depending on soft decisions"""
        for partner in self:
            vat = str(partner.vat) if partner.vat else False
            is_dominican_partner = bool(partner.country_id == self.env.ref('base.do'))

            if partner.country_id and not is_dominican_partner:
                partner.sale_fiscal_type = 'export'

            elif vat and (
                not partner.sale_fiscal_type
                or partner.sale_fiscal_type == 'final'
            ):
                if partner.country_id and is_dominican_partner:
                    if vat.isdigit() and len(vat) == 9:
                        if partner.name and 'MINISTERIO' in partner.name:
                            partner.sale_fiscal_type = 'gov'
                        elif partner.name and any(
                            [n for n in ('IGLESIA', 'ZONA FRANCA') if n in partner.name]
                        ):
                            partner.sale_fiscal_type = 'special'
                        elif vat.startswith('1'):
                            partner.sale_fiscal_type = 'fiscal'
                        else:
                            partner.sale_fiscal_type = 'fiscal'

                    elif len(vat) == 11:
                        if vat.isdigit():
                            partner.sale_fiscal_type = 'fiscal'
                        else:
                            partner.sale_fiscal_type = 'final'
            elif not partner.sale_fiscal_type:
                partner.sale_fiscal_type = 'final'
            else:
                partner.sale_fiscal_type = (
                    partner.sale_fiscal_type
                )

    def _inverse_sale_fiscal_type(self):
        pass

    @api.multi
    def rewrite_due_date(self):
        for rec in self:
            invoice_ids = self.env["account.invoice"].search([
                ('state', '=', 'open'), ('partner_id', '=', self.id)
            ])
            for inv in invoice_ids:
                pterm = rec.property_payment_term_id or \
                    rec.property_supplier_payment_term_id
                if pterm:
                    pterm_list = pterm.with_context(
                        currency_id=inv.company_id.currency_id.id).compute(
                            value=1, date_ref=inv.date_invoice)[0]
                    date_due = max(line[0] for line in pterm_list)
                    inv.date_due = date_due
                    for line in inv.move_id.line_ids:
                        line.date_maturity = date_due
                else:
                    raise UserError(
                        _(u"Debe especificar el término de pago del contacto"))

    @api.model
    def get_sale_fiscal_type_selection(self):
        return {
            "sale_fiscal_type": self._fields['sale_fiscal_type'].selection,
            "sale_fiscal_type_list": self.sale_fiscal_type_list,
            "sale_fiscal_type_vat": self.sale_fiscal_type_vat
        }
