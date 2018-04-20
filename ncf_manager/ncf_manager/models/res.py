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
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except(ImportError, IOError) as err:
    _logger.debug(err)


class ResCompany(models.Model):
    _inherit = 'res.company'

    payment_tax_on_606 = fields.Boolean("Reportar retenciones del 606 al pago")

    country_id = fields.Many2one('res.country', compute='_compute_address',
                                 inverse='_inverse_country',
                                 string="Country", default=62)

    @api.onchange("name")
    def onchange_company_name(self):
        if self.name:
            self.partner_id.validate_rnc_cedula(self.name)
            self.name = self.partner_id.name
            self.vat = self.partner_id.vat

    @api.onchange("vat")
    def onchange_company_vat(self):
        if self.vat:
            self.partner_id.validate_rnc_cedula(self.vat)
            self.name = self.partner_id.name
            self.vat = self.partner_id.vat


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _split_vat(self, vat):
        vat_country, vat_number = vat[:2].lower(), vat[2:].replace(' ', '')
        if vat_country.isnumeric():
            if self.country_id.code:
                vat_country = self.country_id.code
            elif self.company_id.country_id.code:
                vat_country = self.company_id.country_id.code
            else:
                vat_country = 'DO'
        return vat_country, vat_number

    @api.multi
    @api.depends('sale_fiscal_type')
    def _fiscal_info_required(self):
        for rec in self:
            if rec.sale_fiscal_type in ['fiscal', 'gov', 'special']:
                rec.fiscal_info_required = True
            else:
                rec.fiscal_info_required = False

    sale_fiscal_type = fields.Selection(
        [("final", "Consumidor Final"),
         ("fiscal", u"Crédito Fiscal"),
         ("gov", "Gubernamental"),
         ("special", u"Regímenes Especiales"),
         ("unico", u"Único Ingreso")],
        string="Tipo de comprobante", default="final")

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
    country_id = fields.Many2one('res.country', string='Country',
                                 ondelete='restrict', default=61)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(ResPartner, self).name_search(name, args=args,
                                                  operator=operator, limit=100)
        if not res and name:
            if len(name) in (9, 11):
                partners = self.search([('vat', '=', name)])
            else:
                partners = self.search([('vat', 'ilike', name)])

            if partners:
                res = partners.name_get()
        return res

    @api.model
    def validate_rnc_cedula(self, number):
        if number:
            if number.isdigit() and len(number) in (9, 11):
                message = "El contacto: %s, esta registrado con este RNC/Céd."
                contact = self.search([('vat', '=', number)])
                if contact:
                    name = contact.name if len(contact) == 1 else ", ".join(
                        [x.name for x in contact])
                    raise UserError(_(message % name))

                is_rnc = len(number) == 9
                try:
                    rnc.validate(number) if is_rnc else cedula.validate(number)
                except Exception as e:
                    raise ValidationError(_("RNC/Ced Inválido"))

                dgii_vals = rnc.check_dgii(number)

                if dgii_vals is None:
                    if is_rnc:
                        raise ValidationError(_("RNC no disponible en DGII"))
                    self.vat = number
                else:
                    self.name = dgii_vals.get(
                        "name", False) or dgii_vals.get("commercial_name", "")
                    self.vat = dgii_vals.get('rnc')
                    self.is_company = True if is_rnc else False,
                    self.sale_fiscal_type = "fiscal" if is_rnc else "final"

    @api.onchange("name")
    def onchange_partner_name(self):
        if self.name:
            self.validate_rnc_cedula(self.name)

    @api.onchange("vat")
    def onchange_partner_vat(self):
        if self.vat:
            self.validate_rnc_cedula(self.vat)

    @api.multi
    def rewrite_due_date(self):
        for rec in self:
            invoice_ids = self.env["account.invoice"].search(
                [('state', '=', 'open'), ('partner_id', '=', self.id)])
            for inv in invoice_ids:
                pterm = rec.property_payment_term_id or rec.property_supplier_payment_term_id
                if pterm:
                    pterm_list = pterm.with_context(currency_id=inv.company_id.currency_id.id).compute(
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
        return self._fields['sale_fiscal_type'].selection
