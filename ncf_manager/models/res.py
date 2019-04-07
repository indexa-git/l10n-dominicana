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

try:
    from stdnum.do import rnc, cedula
except (ImportError, IOError) as err:
    _logger.debug(err)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.onchange("name")
    def onchange_company_name(self):
        if self.name:
            result = self.env['res.partner'].validate_rnc_cedula(
                self.name, model='company')
            if result:
                self.name = result.get('name')
                self.vat = result.get('vat')

    @api.onchange("vat")
    def onchange_company_vat(self):
        if self.vat:
            result = self.env['res.partner'].validate_rnc_cedula(
                self.vat, model='company')
            if result:
                self.name = result.get('name')
                self.vat = result.get('vat')


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

    sale_fiscal_type = fields.Selection(
        [("final", "Consumo"),
         ("fiscal", u"Crédito Fiscal"),
         ("gov", "Gubernamental"),
         ("special", u"Regímenes Especiales"),
         ("unico", u"Único Ingreso")],
        string="Tipo de comprobante",
        default="final")

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
    }]

    sale_fiscal_type_vat = {
        "rnc": ["fiscal", "gov", "special"],
        "ced": ["final", "fiscal"],
        "other": ["final"],
        "no_vat": ["final", "unico"]
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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(ResPartner, self).name_search(name,
                                                  args=args,
                                                  operator=operator,
                                                  limit=100)
        if not res and name:
            if len(name) in (9, 11):
                partners = self.search([('vat', '=', name)])
            else:
                partners = self.search([('vat', 'ilike', name)])

            if partners:
                res = partners.name_get()
        return res

    @api.model
    def validate_rnc_cedula(self, number, model='partner'):
        if number:
            result, dgii_vals = {}, False
            model = 'res.partner' if model == 'partner' else 'res.company'

            if number.isdigit() and len(number) in (9, 11):
                message = "El contacto: %s, esta registrado con este RNC/Céd."
                self_id = self.id if self.id else 0
                contact = self.search([('vat', '=', number),
                                       ('id', '!=', self_id),
                                       ('parent_id', '=', False)])
                if contact:
                    name = contact.name if len(contact) == 1 else ", ".join(
                        [x.name for x in contact if x.name])
                    raise UserError(_(message) % name)

                try:
                    is_rnc = len(number) == 9
                    rnc.validate(number) if is_rnc else cedula.validate(number)
                except Exception:
                    _logger.warning(
                        "RNC/Ced Inválido en el contacto {}".format(self.name))

                dgii_vals = rnc.check_dgii(number)
                if dgii_vals is None:
                    if is_rnc:
                        _logger.error(
                            "RNC {} del contacto {} no está disponible en DGII"
                            .format(number, self.name))
                    result['vat'] = number
                    result['sale_fiscal_type'] = "final"
                else:
                    result['name'] = dgii_vals.get(
                        "name", False) or dgii_vals.get("commercial_name", "")
                    result['vat'] = dgii_vals.get('rnc')

                    if model == 'res.partner':
                        result['is_company'] = True if is_rnc else False,
                        result['sale_fiscal_type'] = "fiscal"
            return result

    @api.onchange("name")
    def onchange_partner_name(self):
        if self.name:
            result = self.validate_rnc_cedula(self.name)
            if result:
                self.name = result.get('name')
                self.vat = result.get('vat')
                self.is_company = result.get('is_company', False)
                self.sale_fiscal_type = result.get('sale_fiscal_type')

    @api.onchange("vat")
    def onchange_partner_vat(self):
        if self.vat:
            result = self.validate_rnc_cedula(self.vat)
            if result:
                self.name = result.get('name')
                self.vat = result.get('vat')
                self.is_company = result.get('is_company', False)
                self.sale_fiscal_type = result.get('sale_fiscal_type')

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

    @api.model
    def create(self, vals):
        vat = vals.get("vat", False)
        result = self.validate_rnc_cedula(vals["vat"]) if vat else None
        if result and result.get("name", False):
            vals.update({"name": result["name"]})

        return super(ResPartner, self).create(vals)

    @api.model
    def name_create(self, name):
        if self._context.get("install_mode", False):
            return super(ResPartner, self).name_create(name)
        if self._rec_name:
            if name.isdigit():
                partner = self.search([('vat', '=', name)])
                if partner:
                    return partner.name_get()[0]
                else:
                    new_partner = self.create({"vat": name})
                    return new_partner.name_get()[0]
            else:
                return super(ResPartner, self).name_create(name)
