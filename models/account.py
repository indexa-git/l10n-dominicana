# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
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

from openerp import models, fields, api


class AccountJournal(models.Model):
    _inherit = "account.journal"

    purchase_type = fields.Selection([("normal",u"Proveedor normal"),
                                      ("minor", u"Gasto menor"),
                                      ("informal", u"Proveedor informal"),
                                      ("exterior", u"Pagos al exterior")
                                      ],
                                     string=u"Tipo de compra", default="normal")
    ncf_remote_validation = fields.Boolean(u"Validar NCF con DGII", default=True)
    final_sequence_id = fields.Many2one("ir.sequence", string=u"Secuencia para consumidor final")
    fiscal_sequence_id = fields.Many2one("ir.sequence", string=u"Secuencia para credito fiscal")
    gov_sequence_id = fields.Many2one("ir.sequence", string=u"Secuencia gubernamental")
    special_sequence_id = fields.Many2one("ir.sequence", string=u"Secuencia para regimenes especiales")
    unique_sequence_id = fields.Many2one("ir.sequence", string=u"Secuencia para unico ingreso")
    credit_out_invoice = fields.Boolean(u"Puede facturar a crédito")


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'


    supplier = fields.Boolean("Para proveedores")
    client_fiscal_type = fields.Selection([
        ("final", u"Consumidor final"),
        ("fiscal", u"Para credito fiscal"),
        ("gov", u"Gubernamental"),
        ("special", u"Regimenes especiales"),
        ("unico", u"Unico ingreso")
    ], string="Tipo de comprobante")
    journal_id = fields.Many2one("account.journal", string="Diario de compra", domain="[('type','=','purchase')]")
    supplier_fiscal_type = fields.Selection([
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
        ('11', u'11 - Gastos de Seguro'),
    ], string=u"Tipo de gasto")

    @api.model
    def get_fiscal_position(self, partner_id, delivery_id=None):
        if self.env.context.get("model", False) == "purchase.order":
            return super(AccountFiscalPosition, self).get_fiscal_position(partner_id, delivery_id=delivery_id)
        else:
            return self.get_fiscal_position_supplier(partner_id, delivery_id=delivery_id)

    @api.model
    def get_fiscal_position_supplier(self, partner_id, delivery_id=None):
        if not partner_id:
            return False
        # This can be easily overriden to apply more complex fiscal rules
        PartnerObj = self.env['res.partner']
        partner = PartnerObj.browse(partner_id)

        # if no delivery use invoicing
        if delivery_id:
            delivery = PartnerObj.browse(delivery_id)
        else:
            delivery = partner

        # partner manually set fiscal position always win
        if delivery.property_account_position_supplier_id or partner.property_account_position_supplier_id:
            return delivery.property_account_position_supplier_id.id or partner.property_account_position_supplier_id.id

        def fallback_search(vat_required):
            fpos = self._get_fpos_by_region(delivery.country_id.id, delivery.state_id.id, delivery.zip, vat_required)
            if not fpos:
                # Fallback on catchall (no country, no group)
                fpos = self.search([('auto_apply', '=', True), ('vat_required', '=', vat_required),
                                    ('country_id', '=', None), ('country_group_id', '=', None)], limit=1)
            return fpos

        # First search only matching VAT positions
        vat_required = bool(partner.vat)
        fp = fallback_search(vat_required)

        # Then if VAT required found no match, try positions that do not require it
        if not fp and vat_required:
            fp = fallback_search(False)

        return fp.id if fp else False


class AccountTax(models.Model):
    _inherit = 'account.tax'

    purchase_tax_type = fields.Selection([('itbis','ITBIS Pagado'),('ritbis','ITBIS Retenido'),('isr','ISR Retenido')],
                                         default="itbis", string="Tipo de impuesto de compra")
    tax_except = fields.Boolean(string="Exento de este impuesto")


    @api.v8
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        res = super(AccountTax, self).compute_all(price_unit, currency=currency, quantity=quantity, product=product, partner=partner)
        # if self.tax_except and res:
        #     for product_tax in res["taxes"]:
        #         product_tax["amount"] = 0.0
        return res

    @api.model
    def _fix_tax_included_price(self, price, prod_taxes, line_taxes):
        """Subtract tax amount from price when corresponding "price included" taxes do not apply"""

        if line_taxes.tax_except and line_taxes:
            return price

        incl_tax = prod_taxes.filtered(lambda tax: tax not in line_taxes and tax.price_include)

        if incl_tax:
            return incl_tax.compute_all(price)['total_excluded']

        return price