# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################

from odoo import models, fields, api, exceptions

import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    payment_tax_on_606 = fields.Boolean(u"Para el 606 declarar retenciones al pago")
    country_id = fields.Many2one('res.country', compute='_compute_address', inverse='_inverse_country',
                                 string="Country", default=62)


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

            if not rec.vat:
                rec.vat_readonly = False
            else:
                rec.vat_readonly = True

    sale_fiscal_type = fields.Selection([
        ("final", u"Consumidor final"),
        ("fiscal", u"Para credito fiscal"),
        ("gov", u"Gubernamental"),
        ("special", u"Regimenes especiales"),
        ("unico", u"Unico ingreso")
    ], string="Tipo de comprobante", default="final")

    purchase_fiscal_type = fields.Selection([
        ('01', u'01 - Gastos de personal'),
        ('02', u'02 - Gastos por trabajo, suministros y servicios'),
        ('03', u'03 - Arrendamientos'),
        ('04', u'04 - Gastos de Activos Fijos'),
        ('05', u'05 - Gastos de Representación'),
        ('06', u'06 - Otras Deducciones Admitidas'),
        ('07', u'07 - Gastos Financieros'),
        ('08', u'08 - Gastos Extraordinarios'),
        ('09', u'09 - Compras y Gastos que forman parte del Costo de Venta'),
        ('10', u'10 - Adquisiciones de Activos'),
        ('11', u'11 - Gastos de Seguro')
    ], string=u"Tipo de gasto")

    fiscal_info_required = fields.Boolean(compute=_fiscal_info_required)
    vat_readonly = fields.Boolean(compute=_fiscal_info_required)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=62)

    @api.constrains("name", 'vat')
    def name_constrains(self):
        existing_names = self.search_count([('name', '=', self.name)])
        if existing_names > 1:
            raise exceptions.ValidationError(u"Ya esxite un relacionado con este nombre o RNC.")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(ResPartner, self).name_search(name, args=args, operator=operator, limit=100)
        if not res and name:
            if len(name) in (9, 11):
                partners = self.search([('vat', '=', name)])
            else:
                partners = self.search([('vat', 'ilike', name)])

            if partners:
                res = partners.name_get()
        return res

    @api.multi
    def update_partner_name_from_dgii(self):
        for rec in self:
            if rec.vat:
                res = self.env["marcos.api.tools"].rnc_cedula_validation(self.vat)
                if res[0] == 1:
                    self.write({"name": res[1]["name"]})

    @api.multi
    def write(self, vals):
        if vals.get("vat"):
            res = self.env["marcos.api.tools"].rnc_cedula_validation(vals["vat"])
            if res[0] == 1:
                vals.update({"name": res[1]["name"]})
        return super(ResPartner, self).write(vals)

    @api.model
    def create(self, vals):
        if self._context.get("install_mode", False):
            return super(ResPartner, self).create(vals)
        elif vals.get("vat"):
            vat_exist = self.search([('vat', '=', vals["vat"])])
            if vat_exist:
                return vat_exist
            res = self.env["marcos.api.tools"].rnc_cedula_validation(vals["vat"])
            if res[0] == 1:
                vals.update({"name": res[1]["name"]})

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

    @api.onchange("sale_fiscal_type")
    def onchange_sale_fiscal_type(self):
        if self.sale_fiscal_type == "special":
            self.property_account_position_id = self.env.ref("ncf_manager.ncf_manager_special_fiscal_position")
        else:
            self.property_account_position_id = False
