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

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.depends('currency_id', "invoice_rate", "date_invoice")
    def _get_default_rate(self):
        for rec in self:
            if rec.invoice_rate == 0:
                rec.invoice_rate = rec.currency_id.with_context(dict(self._context or {}, date=rec.date_invoice)).rate/1

    @api.depends("currency_id")
    def _is_company_currency(self):
        for rec in self:
            if rec.currency_id == rec.company_id.currency_id:
                rec.is_company_currency = False
            else:
                rec.is_company_currency = True

    def _default_user_shop(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        return shop_user_config

    shop_id = fields.Many2one("shop.ncf.config", string="Punto de venta", required=False,
                              default=_default_user_shop, domain=lambda s: [('user_ids', '=', [s._uid])])
    ncf_control = fields.Boolean(related="journal_id.ncf_control")
    purchase_type = fields.Selection(related="journal_id.purchase_type")

    sale_fiscal_type = fields.Selection([
        ("final", u"Consumidor final"),
        ("fiscal", u"Para credito fiscal"),
        ("gov", u"Gubernamental"),
        ("special", u"Regimenes especiales"),
        ("unico", u"Unico ingreso")
    ], string="NCF para", default="final")

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
        ('11', u'11 - Gastos de Seguro'),
    ], string=u"Tipo de gasto")

    anulation_type = fields.Selection([
        ("01", u"DETERIORO DE FACTURA PRE-IMPRESA"),
        ("02", u"ERRORES DE IMPRESIÓN (FACTURA PRE-IMPRESA)"),
        ("03", u"IMPRESIÓN DEFECTUOSA"),
        ("04", u"DUPLICIDAD DE FACTURA"),
        ("05", u"CORRECCIÓN DE LA INFORMACIÓN"),
        ("06", u"CAMBIO DE PRODUCTOS"),
        ("07", u"DEVOLUCIÓN DE PRODUCTOS"),
        ("08", u"OMISIÓN DE PRODUCTOS"),
        ("09", u"ERRORES EN SECUENCIA DE NCF")
    ], string=u"Tipo de anulación", copy=False)

    invoice_rate = fields.Monetary(string="Tasa", compute=_get_default_rate, store=True)
    is_company_currency = fields.Boolean(compute=_is_company_currency)


    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        super(AccountInvoice, self)._onchange_partner_id()

        if self.partner_id:
            if type in ('out_invoice', 'out_refund'):
                self.sale_fiscal_type = self.partner_id.sale_fiscal_type
            else:
                self.purchase_fiscal_type = self.partner_id.purchase_fiscal_type

    @api.onchange('sale_fiscal_type', 'purchase_fiscal_type')
    def _onchange_fiscal_type(self):
        if self.partner_id:
            if type in ('out_invoice', 'out_refund'):
                self.partner_id.write({'sale_fiscal_type': self.sale_fiscal_type})
            else:
                self.partner_id.write({'purchase_fiscal_type': self.purchase_fiscal_type})

    @api.onchange("shop_id")
    def onchange_shop_id(self):
        self.journal_id = self.shop_id.journal_id
