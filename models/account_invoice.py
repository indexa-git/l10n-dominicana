# -*- coding: utf-8 -*-
###############################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL.
#  (<https://marcos.do/>)

#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it,
# unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without
# copying any source code or material from the Software. You may distribute
# those modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the
# Softwar or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @api.depends('currency_id', "date_invoice")
    def _get_rate(self):
        for rec in self:
            if not rec.is_company_currency:
                try:
                    rate = rec.currency_id.with_context(
                        dict(self._context or {}, date=rec.date_invoice))
                    rec.invoice_rate = 1 / rate.rate
                    rec.rate_id = rate.res_currency_rate_id
                except:
                    pass

    @api.depends("currency_id")
    def _is_company_currency(self):
        for rec in self:
            if rec.currency_id == rec.company_id.currency_id:
                rec.is_company_currency = True
            else:
                rec.is_company_currency = False

    def _default_user_shop(self):
        Shop = self.env["shop.ncf.config"]
        shop_user_config = False

        if not self.journal_id:
            shop_user_config = Shop.sudo().search([('user_ids', 'in', self._uid)])
        else:
            shop_user_config = Shop.sudo().search([
                ('user_ids', 'in', self._uid),
                ('journal_id', '=', self.journal_id.id)])

        if shop_user_config:
            return shop_user_config[0]
        else:
            return False

    shop_id = fields.Many2one("shop.ncf.config", string="Sucursal",
                              required=False,
                              default=_default_user_shop,
                              domain=lambda s: [('user_ids', '=', [s._uid])])

    ncf_control = fields.Boolean(related="journal_id.ncf_control")
    purchase_type = fields.Selection(related="journal_id.purchase_type")

    sale_fiscal_type = fields.Selection(
        [("final", "Consumidor Final"),
         ("fiscal", u"Crédito Fiscal"),
         ("gov", "Gubernamental"),
         ("special", u"Regímenes Especiales"),
         ("unico", u"Único ingreso")],
        string="NCF para")

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

    anulation_type = fields.Selection(
        [("01", "01 - Deterioro de Factura Pre-impresa"),
         ("02", u"02 - Errores de Impresión (Factura Pre-impresa)"),
         ("03", u"03 - Impresión Defectuosa"),
         ("04", "04 - Duplicidad de Factura"),
         ("05", u"05 - Corrección de La Información"),
         ("06", "06 - Cambio de Productos"),
         ("07", u"07 - Devolución de Productos"),
         ("08", u"08 - Omisión de Productos"),
         ("09", "09 - Errores en Secuencia de NCF")],
        string=u"Tipo de anulación", copy=False)

    is_company_currency = fields.Boolean(compute=_is_company_currency)

    invoice_rate = fields.Monetary(string="Tasa", compute=_get_rate,
                                   currency_field='currency_id')
    purchase_type = fields.Selection(
        [("normal", "Requiere NCF"),
         ("minor", "Gasto Menor. NCF Generado por el Sistema"),
         ("informal", "Proveedores Informales. NCF Generado por el Sistema"),
         ("exterior", "Pagos al Exterior. NCF Generado por el Sistema"),
         ("import", "Importaciones. NCF Generado por el Sistema"),
         ("others", "Otros. No requiere NCF")],
        string="Tipo de Compra",
        related="journal_id.purchase_type")

    is_nd = fields.Boolean()
    origin_out = fields.Char(u"Afecta a", related="origin")

    _sql_constraints = [
        ('number_uniq',
         'unique(number, company_id, partner_id, journal_id, type)',
         'Invoice Number must be unique per Company!'),
    ]

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        super(AccountInvoice, self)._onchange_journal_id()
        if self.journal_id.type == 'purchase' and self.journal_id.purchase_type == "minor":
            self.partner_id = self.company_id.partner_id.id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id and self.type == 'out_invoice':
            if self.journal_id.ncf_control:
                self.sale_fiscal_type = self.partner_id.sale_fiscal_type
            if not self.partner_id.customer:
                self.partner_id.customer = True
        elif self.partner_id and self.type == 'in_invoice':
            self.expense_type = self.partner_id.expense_type
            if not self.partner_id.supplier:
                self.partner_id.supplier = True

        if self.journal_id.purchase_type == "minor":
            self.partner_id = self.company_id.partner_id.id

    @api.onchange('sale_fiscal_type', 'expense_type')
    def _onchange_fiscal_type(self):
        if self.partner_id:
            if self.type == 'out_invoice':
                self.partner_id.write(
                    {'sale_fiscal_type': self.sale_fiscal_type})
                if self.sale_fiscal_type == "special":
                    self.fiscal_position_id = self.env.ref(
                        "ncf_manager.ncf_manager_special_fiscal_position")
            if self.type == 'in_invoice':
                self.partner_id.write({'expense_type': self.expense_type})

    @api.onchange("shop_id")
    def onchange_shop_id(self):
        if self.type in ('out_invoice', 'out_refund'):
            self.journal_id = self.shop_id.journal_id.id

    @api.onchange("move_name")
    def onchange_ncf(self):
        if self.type in ("in_invoice", "in_refund") and self.move_name is not False:
            res = self.env["marcos.api.tools"].invoice_ncf_validation(self)
            if res is not True:
                _logger.warning(res)

    @api.multi
    def action_invoice_open(self):
        for rec in self:
            if rec.journal_id.ncf_control and not rec.partner_id.sale_fiscal_type:
                rec.sale_fiscal_type = "final"
            if rec.type == "out_invoice" and rec.sale_fiscal_type in ("fiscal", "gov", "special") and rec.journal_id.ncf_control and not rec.partner_id.vat:
                raise UserError(_(
                    u"El cliente [{}]{} no tiene RNC/Cédula, y es requerido"
                    "para este tipo de factura.".format(rec.partner_id.id,
                                                        rec.partner_id.name)))

            elif rec.type in ("in_invoice", "in_refund"):
                if rec.journal_id.purchase_type in ('normal', 'informal') and not rec.partner_id.vat:
                    raise UserError(_(
                        u"¡Para este tipo de Compra el Proveedor"
                        u" debe de tener un RNC/Cédula establecido!"))
                self.env["marcos.api.tools"].invoice_ncf_validation(rec)

        return super(AccountInvoice, self).action_invoice_open()

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)

        if self._context.get("credit_note_supplier_ncf", False):
            res.update({"move_name": self._context["credit_note_supplier_ncf"]
                        })
        return res
